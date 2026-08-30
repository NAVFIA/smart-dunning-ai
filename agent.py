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
    "EMAIL_ALERT": 0.05
}

class SmartDunningAgent:
    def __init__(self, min_amount_threshold=50.0, max_retries=3):
        self.min_amount_threshold = min_amount_threshold
        self.max_retries = max_retries

    def get_action_for_attempt(self, category: str, attempt: int) -> str:
        """
        Determines the recovery action based on failure category and current attempt index (0-indexed).
        """
        # attempt: 0, 1, 2 (representing 1st, 2nd, 3rd retries)
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
        # Success probability degrades slightly with subsequent attempts
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
            # Hard failures have naturally lower recovery rates because user must act manually
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
        # Create a unique key for each attempt of a transaction
        attempt_key = f"{tx_id}_attempt_{attempt}"
        hash_object = hashlib.md5(attempt_key.encode())
        hex_dig = hash_object.hexdigest()
        # Convert first 8 characters of MD5 hash to float between 0 and 1
        val = int(hex_dig[:8], 16)
        hash_float = val / 0xFFFFFFFF
        return hash_float < probability

    def process_transaction(self, transaction: dict) -> dict:
        """
        Processes a transaction through the complete dunning logic.
        Applies guardrails, iterates through retry actions, and reports outcome history.
        """
        tx_id = transaction["transaction_id"]
        amount = transaction["amount"]
        category = transaction["failure_category"]
        
        result = {
            "transaction_id": tx_id,
            "customer_name": transaction["customer_name"],
            "customer_phone": transaction["customer_phone"],
            "customer_email": transaction["customer_email"],
            "amount": amount,
            "failure_category": category,
            "failure_reason": transaction["failure_reason"],
            "timestamp": transaction["timestamp"],
            "status": "PENDING",
            "total_cost": 0.0,
            "attempts_made": 0,
            "history": []
        }
        
        # 1. Economic Guardrail Check
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
            
        # 2. Dunning Lifecycle Execution
        for attempt in range(self.max_retries):
            action = self.get_action_for_attempt(category, attempt)
            cost = ACTION_COSTS.get(action, 0.0)
            prob = self.get_recovery_probability(category, action, attempt)
            
            # Simulate recovery
            success = self.is_recovery_successful(tx_id, attempt, prob)
            
            attempt_info = {
                "attempt": attempt + 1,
                "action": action,
                "cost": cost,
                "probability": round(prob, 3),
                "success": success
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
