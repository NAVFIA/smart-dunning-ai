import os
import json
import random
from datetime import datetime, timedelta

# Create data directory if it doesn't exist
os.makedirs("data", exist_ok=True)

# Seed for reproducibility
random.seed(42)

# Lists for generating realistic data
FIRST_NAMES = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Krishna", "Ishaan", "Shaurya",
               "Diya", "Ananya", "Aanya", "Pihu", "Prisha", "Ira", "Saanvi", "Aadhya", "Riya", "Kiara"]
LAST_NAMES = ["Sharma", "Verma", "Gupta", "Mehta", "Patel", "Reddy", "Nair", "Rao", "Joshi", "Singh",
              "Kumar", "Choudhary", "Das", "Chatterjee", "Sen", "Pillai", "Iyer", "Mishra", "Pandey", "Yadav"]

FAILURE_CATEGORIES = {
    "TECHNICAL_TRANSIENT": [
        "BANK_SYSTEM_TIMEOUT",
        "GATEWAY_DOWNTIME",
        "NETWORK_LATENCY_EXCEEDED"
    ],
    "USER_DROPOFF": [
        "CUSTOMER_CLOSED_CHECKOUT",
        "OTP_PAGE_ABANDONED",
        "CHOSE_TO_CANCEL"
    ],
    "USER_BALANCE": [
        "INSUFFICIENT_FUNDS",
        "ACCOUNT_LIMIT_EXCEEDED"
    ],
    "AUTHENTICATION_HARD": [
        "INCORRECT_OTP",
        "CARD_EXPIRED",
        "CARD_BLOCKED_BY_ISSUER",
        "INVALID_PIN"
    ]
}

def generate_phone():
    return f"+91{random.randint(7000000000, 9999999999)}"

def generate_mock_data():
    records = []
    base_time = datetime.now() - timedelta(days=7)
    
    for i in range(100):
        # Determine failure category with realistic weights
        cat_roll = random.random()
        if cat_roll < 0.25:
            category = "TECHNICAL_TRANSIENT"
        elif cat_roll < 0.55:
            category = "USER_DROPOFF"
        elif cat_roll < 0.85:
            category = "USER_BALANCE"
        else:
            category = "AUTHENTICATION_HARD"
            
        reason = random.choice(FAILURE_CATEGORIES[category])
        
        # Determine amount: 10% under Rs 50 (guardrail checks), 50% medium (50 - 500), 40% high (500 - 5000)
        amt_roll = random.random()
        if amt_roll < 0.10:
            amount = round(random.uniform(5.0, 49.0), 2)
        elif amt_roll < 0.60:
            amount = round(random.uniform(50.0, 500.0), 2)
        else:
            amount = round(random.uniform(500.0, 5000.0), 2)
            
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        name = f"{first_name} {last_name}"
        email = f"{first_name.lower()}.{last_name.lower()}@example.com"
        phone = generate_phone()
        
        # Customer LTV & Tiering Profile Generation
        tier_roll = random.random()
        if tier_roll < 0.25:
            tier = "VIP_HIGH_LTV"
            ltv = round(random.uniform(35000.0, 125000.0), 2)
            past_txns = random.randint(12, 48)
            churn_risk = round(random.uniform(0.05, 0.25), 2)
        elif tier_roll < 0.50:
            tier = "HIGH_CHURN_RISK"
            ltv = round(random.uniform(3000.0, 18000.0), 2)
            past_txns = random.randint(1, 4)
            churn_risk = round(random.uniform(0.70, 0.95), 2)
        else:
            tier = "REGULAR"
            ltv = round(random.uniform(8000.0, 32000.0), 2)
            past_txns = random.randint(5, 15)
            churn_risk = round(random.uniform(0.25, 0.60), 2)
            
        # Space out transaction times across the last 7 days
        timestamp = (base_time + timedelta(hours=i * 1.6, minutes=random.randint(0, 59))).isoformat()
        
        records.append({
            "transaction_id": f"pay_{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.randint(100000000, 999999999)}",
            "user_id": f"cust_{random.randint(100000, 999999)}",
            "amount": amount,
            "timestamp": timestamp,
            "failure_category": category,
            "failure_reason": reason,
            "customer_name": name,
            "customer_phone": phone,
            "customer_email": email,
            "bank": random.choice(["HDFC", "SBI", "ICICI", "Axis"]),
            "customer_ltv": ltv,
            "customer_tier": tier,
            "past_successful_txns": past_txns,
            "churn_risk_score": churn_risk,
            "retry_count": 0
        })
        
    with open("data/failed_payments.json", "w") as f:
        json.dump(records, f, indent=4)
        
    print(f"Generated 100 failed payment records with customer LTV/tier profiles and saved to data/failed_payments.json")

if __name__ == "__main__":
    generate_mock_data()
