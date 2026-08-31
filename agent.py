import hashlib

# Cost of notification actions (in Indian Rupees - INR)
ACTION_COSTS = {
    "SKIP": 0.0,
    "AUTO_RETRY": 0.0,
    "WHATSAPP_LINK": 1.50,
    "SMS_LINK": 0.20,
    "EMAIL_LINK": 0.05,
    "WHATSAPP_BALANCE_REMINDER": 1.50,
    "EMAIL_BALANCE_REMINDER": 0.05,
    "SMS_BALANCE_REMINDER": 0.20,
    "EMAIL_UPDATE_METHOD": 0.05,
    "WHATSAPP_UPDATE_METHOD": 1.50,
    "SMS_UPDATE_METHOD": 0.20,
    "SMS_ALERT": 0.20,
    "EMAIL_ALERT": 0.05,
    "WHATSAPP_UPI_FALLBACK": 1.50,
    "SMS_UPI_FALLBACK": 0.20,
    "EMAIL_UPI_FALLBACK": 0.05
}

class BankTelemetry:
    def __init__(self, bank_rates=None, upi_rates=None):
        # Simulated real-time success rates
        self.bank_rates = bank_rates or {
            "HDFC": 0.60,
            "SBI": 0.58,
            "ICICI": 0.78,
            "Axis": 0.82
        }
        self.upi_rates = upi_rates or {
            "@okhdfcbank": 0.85,
            "@oksbi": 0.80,
            "@paytm": 0.75
        }

    def get_bank_rate(self, bank: str) -> float:
        return self.bank_rates.get(bank, 0.75)

    def get_upi_rate(self, handle: str) -> float:
        return self.upi_rates.get(handle, 0.80)

class SmartDunningAgent:
    def __init__(self, min_amount_threshold=20.0, max_retries=3, telemetry=None):
        self.min_amount_threshold = min_amount_threshold
        self.max_retries = max_retries
        self.telemetry = telemetry or BankTelemetry()

    def get_action_for_attempt(self, category: str, attempt: int) -> str:
        """
        Determines the recovery action based on failure category and current attempt index (0-indexed).
        """
        if category == "TECHNICAL_TRANSIENT":
            if attempt < 2:
                return "AUTO_RETRY"
            else:
                return "SMS_ALERT"
        
        elif category == "USER_DROPOFF":
            if attempt == 0:
                return "WHATSAPP_LINK"
            elif attempt == 1:
                return "SMS_LINK"
            else:
                return "EMAIL_LINK"
                
        elif category == "USER_BALANCE":
            if attempt == 0:
                return "WHATSAPP_BALANCE_REMINDER"
            elif attempt == 1:
                return "EMAIL_BALANCE_REMINDER"
            else:
                return "SMS_BALANCE_REMINDER"
                
        elif category == "AUTHENTICATION_HARD":
            if attempt == 0:
                return "EMAIL_UPDATE_METHOD"
            elif attempt == 1:
                return "WHATSAPP_UPDATE_METHOD"
            else:
                return "SMS_UPDATE_METHOD"
                
        return "EMAIL_ALERT"

    def get_recovery_probability(self, category: str, action: str, attempt: int) -> float:
        """
        Calculates recovery success probability based on failure category, action taken, and attempt count.
        """
        decay = attempt * 0.08
        
        if category == "TECHNICAL_TRANSIENT":
            if action == "AUTO_RETRY":
                return max(0.20, 0.70 - decay)
            elif action == "SMS_ALERT":
                return max(0.15, 0.40 - decay)
                
        elif category == "USER_DROPOFF":
            if "WHATSAPP" in action:
                return max(0.20, 0.60 - decay)
            elif "SMS" in action:
                return max(0.15, 0.40 - decay)
            elif "EMAIL" in action:
                return max(0.10, 0.25 - decay)
                
        elif category == "USER_BALANCE":
            if "WHATSAPP" in action:
                return max(0.15, 0.45 - decay)
            elif "EMAIL" in action:
                return max(0.10, 0.30 - decay)
            elif "SMS" in action:
                return max(0.08, 0.20 - decay)
                
        elif category == "AUTHENTICATION_HARD":
            if "EMAIL" in action:
                return max(0.08, 0.28 - decay)
            elif "WHATSAPP" in action:
                return max(0.08, 0.22 - decay)
            elif "SMS" in action:
                return max(0.05, 0.15 - decay)
                
        return max(0.05, 0.15 - decay)

    def is_recovery_successful(self, tx_id: str, attempt: int, probability: float) -> bool:
        """
        Simulates if recovery is successful in a deterministic, repeatable way using transaction ID hash.
        """
        attempt_key = f"{tx_id}_attempt_{attempt}"
        hash_object = hashlib.md5(attempt_key.encode())
        hex_dig = hash_object.hexdigest()
        val = int(hex_dig[:8], 16)
        hash_float = val / 0xFFFFFFFF
        return hash_float < probability

    def process_transaction(self, transaction: dict, use_fallback: bool = True) -> dict:
        """
        Processes a transaction through the complete dunning logic.
        Applies guardrails, iterates through retry actions, and reports outcome history.
        """
        tx_id = transaction["transaction_id"]
        amount = transaction["amount"]
        category = transaction["failure_category"]
        bank = transaction.get("bank", "HDFC")
        
        result = {
            "transaction_id": tx_id,
            "customer_name": transaction["customer_name"],
            "customer_phone": transaction["customer_phone"],
            "customer_email": transaction["customer_email"],
            "amount": amount,
            "bank": bank,
            "failure_category": category,
            "failure_reason": transaction["failure_reason"],
            "timestamp": transaction["timestamp"],
            "status": "PENDING",
            "total_cost": 0.0,
            "attempts_made": 0,
            "history": []
        }
        
        # 1. Economic Guardrail Check (Skip if amount < Rs 20)
        if amount < self.min_amount_threshold:
            result["status"] = "SKIPPED"
            result["history"].append({
                "attempt": 0,
                "action": "SKIP",
                "cost": 0.0,
                "probability": 0.0,
                "success": False,
                "reason": f"Amount Rs {amount:.2f} is below Rs {self.min_amount_threshold:.2f} threshold"
            })
            return result

        # 2. Hard Authentication Suppression Check
        if category == "AUTHENTICATION_HARD":
            result["status"] = "SUPPRESSED"
            result["history"].append({
                "attempt": 0,
                "action": "SUPPRESS",
                "cost": 0.0,
                "probability": 0.0,
                "success": False,
                "reason": "Complete suppression on hard mandate/authentication failures"
            })
            return result
            
        # 3. Dunning Lifecycle Execution (Hard cap at 3 attempts)
        for attempt in range(min(self.max_retries, 3)):
            action = self.get_action_for_attempt(category, attempt)
            
            # Check bank health
            bank_rate = self.telemetry.get_bank_rate(bank)
            is_degraded = bank_rate < 0.65
            
            rerouted = False
            fallback_bank = None
            fallback_handle = None
            
            if use_fallback and is_degraded:
                rerouted = True
                # Find the healthiest alternate bank (excluding current degraded bank)
                healthy_banks = {b: r for b, r in self.telemetry.bank_rates.items() if b != bank and r >= 0.65}
                if healthy_banks:
                    fallback_bank = max(healthy_banks, key=healthy_banks.get)
                else:
                    fallback_bank = "Axis"
                
                # Select the healthiest UPI handle from the telemetry upi rates
                allowed_handles = {h: r for h, r in self.telemetry.upi_rates.items() if not (bank == "HDFC" and "hdfc" in h) and not (bank == "SBI" and "sbi" in h)}
                if allowed_handles:
                    fallback_handle = max(allowed_handles, key=allowed_handles.get)
                else:
                    fallback_handle = "@paytm"
                
                # Reroute action to fallback payment link
                if "WHATSAPP" in action or action == "AUTO_RETRY":
                    action = "WHATSAPP_UPI_FALLBACK"
                elif "SMS" in action:
                    action = "SMS_UPI_FALLBACK"
                else:
                    action = "EMAIL_UPI_FALLBACK"
                
                cost = ACTION_COSTS.get(action, 0.0)
                
                # Fallback success probability is determined by the UPI handle success rate, minus attempt decay
                upi_rate = self.telemetry.get_upi_rate(fallback_handle)
                decay = attempt * 0.08
                prob = max(0.20, upi_rate - decay)
            else:
                cost = ACTION_COSTS.get(action, 0.0)
                prob = self.get_recovery_probability(category, action, attempt)
            
            # Simulate recovery
            success = self.is_recovery_successful(tx_id, attempt, prob)
            
            # Generate fallback link & localized messages
            fallback_link = f"https://razorpay.me/fallback/pay_{tx_id}?rail=upi&bank={fallback_bank or bank}"
            msg_en = f"Hi {transaction['customer_name']}, {bank} servers are currently experiencing high latency. Tap here to complete your payment instantly using PhonePe/Paytm/UPI: {fallback_link}"
            msg_hi = f"Hey {transaction['customer_name']}, {bank} ke server slow hain. Yahan tap karke PhonePe/Paytm se bina kisi issue ke complete karein: {fallback_link}"
            
            attempt_info = {
                "attempt": attempt + 1,
                "action": action,
                "cost": cost,
                "probability": round(prob, 3),
                "success": success,
                "rerouted": rerouted,
                "fallback_bank": fallback_bank,
                "fallback_handle": fallback_handle,
                "message_english": msg_en,
                "message_hinglish": msg_hi,
                "fallback_link": fallback_link
            }
            
            result["history"].append(attempt_info)
            result["total_cost"] += cost
            result["attempts_made"] += 1
            
            if success:
                result["status"] = "RECOVERED"
                break
        
        if result["status"] == "PENDING":
            result["status"] = "FAILED"
            
        return result
