import re
import hashlib
from datetime import datetime, timedelta

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
    "EMAIL_UPI_FALLBACK": 0.05,
    "WHATSAPP_VIP_WHITEGLOVE": 1.50,
    "WHATSAPP_CHURN_RECOVERY": 1.50
}

DEFAULT_POLICY = {
    "policy_name": "Standard Razorpay Dunning Policy",
    "min_amount_threshold": 20.0,
    "max_retries": 3,
    "discount_pct": 0.0,
    "discount_min_amount": 2000.0,
    "discount_categories": ["USER_DROPOFF", "TECHNICAL_TRANSIENT", "USER_BALANCE"],
    "discount_tiers": ["VIP_HIGH_LTV", "REGULAR", "HIGH_CHURN_RISK"],
    "churn_risk_threshold": 1.0,
    "zero_retry_on_high_churn": False,
    "priority_rail": "UPI",
    "rule_description": "Standard multi-rail recovery with bank telemetry routing and LTV tiering."
}

def parse_natural_language_policy(prompt: str) -> dict:
    """
    Parses natural language merchant instructions into structured SmartDunningAgent rule weights.
    Supports discount percentages, minimum cart thresholds, churn score constraints, retry caps, and targeting.
    """
    policy = DEFAULT_POLICY.copy()
    prompt_lower = prompt.lower().strip()
    
    policy["policy_name"] = "Custom AI Merchant Policy"
    extracted_rules = []
    
    # 1. Parse Churn Risk Threshold & Zero Retry Directives FIRST to capture churn decimals
    churn_match = re.search(r'(?:churn\s*(?:risk|score)?|dropoff\s*risk)\s*(?:>|above|>=|over)?\s*(0\.\d+|\d+%)', prompt_lower)
    if churn_match:
        val_str = churn_match.group(1)
        if "%" in val_str:
            churn_val = float(val_str.replace("%", "")) / 100.0
        else:
            churn_val = float(val_str)
        policy["churn_risk_threshold"] = min(1.0, max(0.1, churn_val))
        policy["zero_retry_on_high_churn"] = True
        extracted_rules.append(f"Halt Retries for Churn Score > {policy['churn_risk_threshold']:.2f}")
    elif "zero retries" in prompt_lower or "no retries" in prompt_lower or "0 retries" in prompt_lower or "halt churn" in prompt_lower:
        policy["zero_retry_on_high_churn"] = True
        policy["churn_risk_threshold"] = 0.80
        extracted_rules.append("Zero Retries for High Churn Risk (> 0.80)")

    # 2. Parse Discount Percentage (e.g., "5% discount", "give 10% instant discount", "7 % off")
    disc_match = re.search(r'(\d+(?:\.\d+)?)\s*%\s*(?:dynamic\s*)?(?:discount|off|cashback|concession)?', prompt_lower)
    if not disc_match:
        disc_match = re.search(r'(?:discount|off|cashback)\s*(?:of\s*)?(\d+(?:\.\d+)?)\s*%', prompt_lower)
    if disc_match:
        disc_val = float(disc_match.group(1))
        # Ensure it's not a churn percentage
        if not ("churn" in prompt_lower and disc_match.group(0).strip() in prompt_lower[prompt_lower.find("churn"):]):
            policy["discount_pct"] = min(30.0, max(0.0, disc_val))
            extracted_rules.append(f"{policy['discount_pct']:.0f}% Dynamic Discount Token")
        
    # 3. Parse Minimum Amount Threshold for Discount / Trigger (e.g. "> ₹2000", "carts > 2000", "above 1500", "over ₹500")
    # Must look for amounts >= 10 to avoid decimal churn values
    amt_match = re.search(r'(?:cart|order|amount|txn|transaction|value|>|above|greater than|over|exceeding|min|minimum)\s*(?:₹|rs\.?|inr)?\s*([1-9]\d{1,6}(?:,\d+)*(?:\.\d+)?)', prompt_lower)
    if not amt_match:
        amt_match = re.search(r'(?:₹|rs\.?|inr)\s*([1-9]\d*(?:,\d+)*(?:\.\d+)?)', prompt_lower)
    if amt_match:
        clean_amt = float(amt_match.group(1).replace(",", ""))
        if clean_amt >= 10.0:
            policy["discount_min_amount"] = clean_amt
            extracted_rules.append(f"Cart Value > ₹{clean_amt:,.0f}")
            
    # Guardrail low bypass check
    if "<" in prompt_lower or "below" in prompt_lower or "under" in prompt_lower:
        low_amt_match = re.search(r'(?:<|below|under|less than)\s*(?:₹|rs\.?|inr)?\s*([1-9]\d*(?:,\d+)*(?:\.\d+)?)', prompt_lower)
        if low_amt_match:
            clean_low = float(low_amt_match.group(1).replace(",", ""))
            policy["min_amount_threshold"] = clean_low
            extracted_rules.append(f"Guardrail Bypass < ₹{clean_low:,.0f}")

    # 4. Parse Max Retries (e.g. "max 1 retry", "cap retries to 2", "1 retry only")
    retry_match = re.search(r'(?:max|cap|limit|allow)\s*(?:to\s*)?(\d+)\s*(?:retries|retry|attempts)', prompt_lower)
    if retry_match:
        r_val = int(retry_match.group(1))
        policy["max_retries"] = min(5, max(1, r_val))
        extracted_rules.append(f"Max Retries Capped at {policy['max_retries']}")

    # 5. Parse Category Targeting (e.g., "upi dropoffs", "technical errors", "balance failures")
    targeted_cats = []
    if "drop" in prompt_lower or "abandon" in prompt_lower or "cart" in prompt_lower or "upi" in prompt_lower:
        targeted_cats.append("USER_DROPOFF")
    if "tech" in prompt_lower or "timeout" in prompt_lower or "gateway" in prompt_lower or "network" in prompt_lower:
        targeted_cats.append("TECHNICAL_TRANSIENT")
    if "balance" in prompt_lower or "funds" in prompt_lower:
        targeted_cats.append("USER_BALANCE")
    if targeted_cats:
        policy["discount_categories"] = list(dict.fromkeys(targeted_cats))
        extracted_rules.append(f"Targeting: {', '.join(policy['discount_categories'])}")

    # 6. Parse Tier Targeting (e.g. "vip only", "high ltv", "regular customers")
    targeted_tiers = []
    if "vip" in prompt_lower or "high ltv" in prompt_lower:
        targeted_tiers.append("VIP_HIGH_LTV")
    if "regular" in prompt_lower:
        targeted_tiers.append("REGULAR")
    if "churn" in prompt_lower and not policy.get("zero_retry_on_high_churn"):
        targeted_tiers.append("HIGH_CHURN_RISK")
    if targeted_tiers:
        policy["discount_tiers"] = list(dict.fromkeys(targeted_tiers))
        extracted_rules.append(f"Tier Focus: {', '.join(policy['discount_tiers'])}")

    if extracted_rules:
        policy["rule_description"] = " | ".join(extracted_rules)
    else:
        policy["rule_description"] = f"Adaptive merchant policy: '{prompt[:60]}...'"
        
    return policy

class BankTelemetry:
    def __init__(self, bank_rates=None, upi_rates=None):
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

class RetryWindowOptimizer:
    """
    Intelligent retry scheduling based on bank downtime patterns,
    salary credit windows (1st-5th of month), and user engagement profiles.
    """
    @staticmethod
    def get_optimal_window(timestamp_str: str, category: str, bank: str, amount: float) -> dict:
        try:
            dt = datetime.fromisoformat(timestamp_str)
        except Exception:
            dt = datetime.now()
            
        day = dt.day
        hour = dt.hour
        
        # 1. Salary Credit Liquidity Window (1st to 5th of month for balance dropoffs)
        if category == "USER_BALANCE" and 1 <= day <= 5:
            return {
                "window_label": "Salary Credit Liquidity Window (09:30 AM - 11:30 AM)",
                "scheduled_time": "Next day 09:30 AM",
                "delay_minutes": 120,
                "strategy": "SALARY_CYCLE_ALIGNMENT",
                "reasoning": "High liquidity window following monthly salary disbursement cycle."
            }
            
        # 2. Nocturnal Core Banking Maintenance Avoidance (12:00 AM - 05:00 AM)
        if 0 <= hour <= 5:
            return {
                "window_label": "Morning Settlement Window (10:00 AM - 11:30 AM)",
                "scheduled_time": "Today 10:00 AM",
                "delay_minutes": max(15, (10 - hour) * 60),
                "strategy": "MAINTENANCE_AVOIDANCE",
                "reasoning": f"Bypasses midnight core-banking maintenance downtime on {bank} CBS."
            }
            
        # 3. Technical Transient (Gateway / Network timeouts)
        if category == "TECHNICAL_TRANSIENT":
            sched = (dt + timedelta(minutes=15)).strftime("%I:%M %p")
            return {
                "window_label": "Dynamic Cool-off Window (+15 mins)",
                "scheduled_time": f"Immediate +15m ({sched})",
                "delay_minutes": 15,
                "strategy": "EXPONENTIAL_LATENCY_COOLOFF",
                "reasoning": f"Allows {bank} gateway latency to stabilize and queue to drain."
            }
            
        # 4. User Dropoff (Hot checkout intent)
        if category == "USER_DROPOFF":
            return {
                "window_label": "Hot Intent Window (< 3 mins)",
                "scheduled_time": "Immediate (< 3 mins)",
                "delay_minutes": 3,
                "strategy": "HOT_INTENT_RECAPTURE",
                "reasoning": "Recaptures active checkout intent before customer leaves session."
            }
            
        # 5. Default Business Hours Peak
        return {
            "window_label": "High-Throughput Business Window (02:00 PM - 05:00 PM)",
            "scheduled_time": "Optimal Peak (02:30 PM)",
            "delay_minutes": 30,
            "strategy": "STANDARD_OPTIMIZED",
            "reasoning": "Optimized for high UPI server throughput and peak customer availability."
        }

class SmartDunningAgent:
    def __init__(self, min_amount_threshold=20.0, max_retries=3, telemetry=None, policy=None):
        self.policy = DEFAULT_POLICY.copy()
        if policy:
            self.policy.update(policy)
            
        self.min_amount_threshold = self.policy.get("min_amount_threshold", min_amount_threshold)
        self.max_retries = self.policy.get("max_retries", max_retries)
        self.telemetry = telemetry or BankTelemetry()
        self.optimizer = RetryWindowOptimizer()

    def apply_policy(self, policy: dict):
        """Updates active agent rule weights in real-time."""
        self.policy.update(policy)
        self.min_amount_threshold = self.policy.get("min_amount_threshold", self.min_amount_threshold)
        self.max_retries = self.policy.get("max_retries", self.max_retries)

    def get_action_for_attempt(self, category: str, attempt: int, tier: str = "REGULAR", amount: float = 100.0) -> str:
        """
        Determines the recovery action based on failure category, attempt index, and customer tier.
        """
        # Low-margin protection: If amount < Rs 100 and Regular tier, prioritize low-cost SMS / silent retries
        if amount < 100.0 and tier == "REGULAR":
            if attempt == 0:
                return "AUTO_RETRY"
            elif attempt == 1:
                return "SMS_LINK"
            else:
                return "EMAIL_LINK"
                
        # VIP High-LTV customers get priority White-Glove WhatsApp routing
        if tier == "VIP_HIGH_LTV" and attempt == 0:
            return "WHATSAPP_VIP_WHITEGLOVE"
            
        # High Churn Risk customers receive urgent dedicated WhatsApp re-engagement
        if tier == "HIGH_CHURN_RISK" and attempt == 0:
            return "WHATSAPP_CHURN_RECOVERY"

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

    def get_recovery_probability(self, category: str, action: str, attempt: int, tier: str = "REGULAR", discount_pct: float = 0.0) -> float:
        """
        Calculates recovery success probability based on failure category, action taken, attempt count, tier, and dynamic discount.
        """
        decay = attempt * 0.08
        
        # Base probabilities
        if category == "TECHNICAL_TRANSIENT":
            if action == "AUTO_RETRY":
                prob = max(0.20, 0.70 - decay)
            elif action == "SMS_ALERT":
                prob = max(0.15, 0.40 - decay)
            else:
                prob = max(0.20, 0.65 - decay)
                
        elif category == "USER_DROPOFF":
            if "WHATSAPP" in action:
                prob = max(0.20, 0.60 - decay)
            elif "SMS" in action:
                prob = max(0.15, 0.40 - decay)
            elif "EMAIL" in action:
                prob = max(0.10, 0.25 - decay)
            else:
                prob = max(0.15, 0.45 - decay)
                
        elif category == "USER_BALANCE":
            if "WHATSAPP" in action:
                prob = max(0.15, 0.45 - decay)
            elif "EMAIL" in action:
                prob = max(0.10, 0.30 - decay)
            elif "SMS" in action:
                prob = max(0.08, 0.20 - decay)
            else:
                prob = max(0.10, 0.35 - decay)
                
        elif category == "AUTHENTICATION_HARD":
            if "EMAIL" in action:
                prob = max(0.08, 0.28 - decay)
            elif "WHATSAPP" in action:
                prob = max(0.08, 0.22 - decay)
            elif "SMS" in action:
                prob = max(0.05, 0.15 - decay)
            else:
                prob = max(0.05, 0.15 - decay)
        else:
            prob = max(0.05, 0.15 - decay)

        # Tier-based responsiveness adjustments
        if tier == "VIP_HIGH_LTV":
            prob = min(0.95, prob + 0.12)
        elif tier == "HIGH_CHURN_RISK":
            prob = max(0.10, prob - 0.05)

        # Dynamic Discount Conversion Lift (incentivizes fast 1-tap checkout)
        if discount_pct > 0:
            incentive_lift = min(0.22, (discount_pct / 100.0) * 1.5)
            prob = min(0.98, prob + incentive_lift)

        return prob

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

    def process_transaction(self, transaction: dict, use_fallback: bool = True, policy: dict = None) -> dict:
        """
        Processes a transaction through the complete dunning logic with dynamic policy evaluation.
        """
        active_policy = self.policy.copy()
        if policy:
            active_policy.update(policy)

        tx_id = transaction["transaction_id"]
        amount = transaction["amount"]
        category = transaction["failure_category"]
        bank = transaction.get("bank", "HDFC")
        tier = transaction.get("customer_tier", "REGULAR")
        ltv = transaction.get("customer_ltv", 15000.0)
        churn_risk = transaction.get("churn_risk_score", 0.35)
        timestamp = transaction.get("timestamp", datetime.now().isoformat())
        
        # Calculate dynamic retry window recommendation
        retry_window = self.optimizer.get_optimal_window(timestamp, category, bank, amount)
        
        min_threshold = active_policy.get("min_amount_threshold", self.min_amount_threshold)
        max_retries_limit = active_policy.get("max_retries", self.max_retries)
        
        # Check dynamic discount eligibility
        discount_pct = active_policy.get("discount_pct", 0.0)
        discount_min_amt = active_policy.get("discount_min_amount", 2000.0)
        target_cats = active_policy.get("discount_categories", ["USER_DROPOFF", "TECHNICAL_TRANSIENT", "USER_BALANCE"])
        target_tiers = active_policy.get("discount_tiers", ["VIP_HIGH_LTV", "REGULAR", "HIGH_CHURN_RISK"])
        
        is_discount_eligible = (
            discount_pct > 0 and 
            amount >= discount_min_amt and 
            category in target_cats and 
            tier in target_tiers
        )
        
        effective_discount_pct = discount_pct if is_discount_eligible else 0.0
        discount_amount = round(amount * (effective_discount_pct / 100.0), 2)
        payable_amount = round(amount - discount_amount, 2)
        discount_token = f"rzp_disc_{int(effective_discount_pct)}pct_{tx_id[-6:]}" if is_discount_eligible else None
        
        result = {
            "transaction_id": tx_id,
            "customer_name": transaction["customer_name"],
            "customer_phone": transaction["customer_phone"],
            "customer_email": transaction["customer_email"],
            "amount": amount,
            "bank": bank,
            "customer_ltv": ltv,
            "customer_tier": tier,
            "churn_risk_score": churn_risk,
            "failure_category": category,
            "failure_reason": transaction["failure_reason"],
            "timestamp": timestamp,
            "optimal_retry_window": retry_window["window_label"],
            "scheduled_time": retry_window["scheduled_time"],
            "window_reasoning": retry_window["reasoning"],
            "status": "PENDING",
            "total_cost": 0.0,
            "attempts_made": 0,
            "discount_applied": is_discount_eligible,
            "discount_pct": effective_discount_pct,
            "discount_amount": discount_amount,
            "payable_amount": payable_amount,
            "discount_token": discount_token,
            "settlement_rail": "UPI_INTENT_1TAP",
            "history": []
        }
        
        # 1. Economic Guardrail Check (Skip if amount < min_threshold)
        if amount < min_threshold:
            result["status"] = "SKIPPED"
            result["history"].append({
                "attempt": 0,
                "action": "SKIP",
                "cost": 0.0,
                "probability": 0.0,
                "success": False,
                "reason": f"Amount ₹{amount:.2f} is below policy ₹{min_threshold:.2f} threshold"
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

        # 3. Dynamic High Churn Suppression Check (Autonomous Policy Override)
        churn_threshold = active_policy.get("churn_risk_threshold", 1.0)
        zero_retry_churn = active_policy.get("zero_retry_on_high_churn", False)
        if zero_retry_churn and churn_risk >= churn_threshold:
            result["status"] = "CHURN_HALTED"
            result["history"].append({
                "attempt": 0,
                "action": "HALT_CHURN_RISK",
                "cost": 0.0,
                "probability": 0.0,
                "success": False,
                "reason": f"Policy halted: Churn risk score {churn_risk:.2f} exceeds cutoff {churn_threshold:.2f}"
            })
            return result
            
        # 4. Dunning Lifecycle Execution
        max_attempts = min(max_retries_limit, 4)
        for attempt in range(max_attempts):
            action = self.get_action_for_attempt(category, attempt, tier=tier, amount=amount)
            
            # Check bank health
            bank_rate = self.telemetry.get_bank_rate(bank)
            is_degraded = bank_rate < 0.65
            
            rerouted = False
            fallback_bank = None
            fallback_handle = None
            
            if use_fallback and is_degraded:
                rerouted = True
                healthy_banks = {b: r for b, r in self.telemetry.bank_rates.items() if b != bank and r >= 0.65}
                fallback_bank = max(healthy_banks, key=healthy_banks.get) if healthy_banks else "Axis"
                
                allowed_handles = {h: r for h, r in self.telemetry.upi_rates.items() if not (bank == "HDFC" and "hdfc" in h) and not (bank == "SBI" and "sbi" in h)}
                fallback_handle = max(allowed_handles, key=allowed_handles.get) if allowed_handles else "@paytm"
                
                if tier == "VIP_HIGH_LTV":
                    action = "WHATSAPP_VIP_WHITEGLOVE"
                elif "WHATSAPP" in action or action == "AUTO_RETRY":
                    action = "WHATSAPP_UPI_FALLBACK"
                elif "SMS" in action:
                    action = "SMS_UPI_FALLBACK"
                else:
                    action = "EMAIL_UPI_FALLBACK"
                
                cost = ACTION_COSTS.get(action, 0.0)
                
                upi_rate = self.telemetry.get_upi_rate(fallback_handle)
                decay = attempt * 0.08
                tier_bonus = 0.08 if tier == "VIP_HIGH_LTV" else 0.0
                disc_bonus = min(0.20, (effective_discount_pct / 100.0) * 1.5) if effective_discount_pct > 0 else 0.0
                prob = min(0.98, max(0.20, upi_rate - decay + tier_bonus + disc_bonus))
            else:
                cost = ACTION_COSTS.get(action, 0.0)
                prob = self.get_recovery_probability(category, action, attempt, tier=tier, discount_pct=effective_discount_pct)
            
            # Deterministic recovery simulation
            success = self.is_recovery_successful(tx_id, attempt, prob)
            
            # Generate 1-Click Fallback Link with Dynamic Discount Token & Rail Params
            discount_query = f"&disc={int(effective_discount_pct)}pct&save=INR{discount_amount:.0f}&pay={payable_amount:.0f}" if is_discount_eligible else ""
            fallback_link = f"https://rzp.io/l/{tx_id}?rail=upi&bank={fallback_bank or bank}{discount_query}"
            
            # Contextual & localized message generation with Copilot Discount callout
            cust_name = transaction["customer_name"]
            disc_badge = f" ⚡ {int(effective_discount_pct)}% Instant Copilot Discount applied! Pay ₹{payable_amount:,.2f} instead of ₹{amount:,.2f}." if is_discount_eligible else ""
            
            if tier == "VIP_HIGH_LTV":
                msg_en = f"Hi {cust_name}, as our VIP patron, we noticed {bank} servers had a latency spike.{disc_badge} Tap here for your priority 1-Tap UPI instant completion: {fallback_link}"
                msg_hi = f"Hey {cust_name}, aap hamare VIP member hain aur {bank} ke servers slow hain.{disc_badge} Yahan tap karke PhonePe/Paytm se 1-click me payment complete karein: {fallback_link}"
            elif tier == "HIGH_CHURN_RISK":
                msg_en = f"Hi {cust_name}, your order of ₹{amount:,.2f} on {bank} had a hiccup.{disc_badge} Tap here to complete securely in 1 click via UPI before session expiry: {fallback_link}"
                msg_hi = f"Hey {cust_name}, aapka ₹{amount:,.2f} payment {bank} pe atak gaya.{disc_badge} Session expire hone se pehle yahan tap karke UPI se instantly complete karein: {fallback_link}"
            else:
                msg_en = f"Hi {cust_name}, {bank} servers are experiencing latency.{disc_badge} Tap here to complete your payment in 1-tap using PhonePe/Paytm/GPay: {fallback_link}"
                msg_hi = f"Hey {cust_name}, {bank} ke server slow chal rahe hain.{disc_badge} Yahan tap karke PhonePe/Paytm se bina kisi issue ke 1-click me complete karein: {fallback_link}"
            
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
                "fallback_link": fallback_link,
                "discount_token": discount_token,
                "payable_amount": payable_amount,
                "scheduled_time": retry_window["scheduled_time"],
                "strategy": retry_window["strategy"]
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
