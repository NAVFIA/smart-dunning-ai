import json
import os
from mock_data import generate_mock_data
from agent import SmartDunningAgent, parse_natural_language_policy

def run_evaluation():
    print("Generating fresh mock transaction data with LTV and tiering tags...")
    generate_mock_data()
        
    with open("data/failed_payments.json", "r", encoding="utf-8") as f:
        transactions = json.load(f)
        
    agent = SmartDunningAgent(min_amount_threshold=20.0, max_retries=3)
    
    total_count = len(transactions)
    total_at_risk = sum(tx["amount"] for tx in transactions)
    total_ltv_at_risk = sum(tx.get("customer_ltv", 15000.0) for tx in transactions)
    
    # --- SWEEP 1: BASELINE DUNNING (Standard routing, no tier-boosting or bank fallback) ---
    baseline_results = []
    baseline_recovered_count = 0
    baseline_skipped_count = 0
    baseline_suppressed_count = 0
    baseline_failed_count = 0
    baseline_gross_savings = 0.0
    baseline_total_costs = 0.0
    baseline_ltv_recovered = 0.0
    
    for tx in transactions:
        res = agent.process_transaction(tx, use_fallback=False)
        baseline_results.append(res)
        baseline_total_costs += res["total_cost"]
        
        if res["status"] == "RECOVERED":
            baseline_gross_savings += res["amount"]
            baseline_recovered_count += 1
            baseline_ltv_recovered += tx.get("customer_ltv", 15000.0)
        elif res["status"] == "SKIPPED":
            baseline_skipped_count += 1
        elif res["status"] == "SUPPRESSED":
            baseline_suppressed_count += 1
        else:
            baseline_failed_count += 1
            
    # --- SWEEP 2: UPGRADED TIER-1 FINTECH DUNNING (With LTV tiering & dynamic bank fallback) ---
    upgraded_results = []
    upgraded_recovered_count = 0
    upgraded_skipped_count = 0
    upgraded_suppressed_count = 0
    upgraded_failed_count = 0
    upgraded_gross_savings = 0.0
    upgraded_total_costs = 0.0
    upgraded_ltv_recovered = 0.0
    
    tier_stats = {
        "VIP_HIGH_LTV": {"total": 0, "recovered": 0, "amount_at_risk": 0.0, "amount_recovered": 0.0, "ltv_at_risk": 0.0, "ltv_recovered": 0.0},
        "REGULAR": {"total": 0, "recovered": 0, "amount_at_risk": 0.0, "amount_recovered": 0.0, "ltv_at_risk": 0.0, "ltv_recovered": 0.0},
        "HIGH_CHURN_RISK": {"total": 0, "recovered": 0, "amount_at_risk": 0.0, "amount_recovered": 0.0, "ltv_at_risk": 0.0, "ltv_recovered": 0.0}
    }
    
    for tx in transactions:
        res = agent.process_transaction(tx, use_fallback=True)
        upgraded_results.append(res)
        upgraded_total_costs += res["total_cost"]
        
        t = tx.get("customer_tier", "REGULAR")
        if t in tier_stats:
            tier_stats[t]["total"] += 1
            tier_stats[t]["amount_at_risk"] += tx["amount"]
            tier_stats[t]["ltv_at_risk"] += tx.get("customer_ltv", 15000.0)
        
        if res["status"] == "RECOVERED":
            upgraded_gross_savings += res["amount"]
            upgraded_recovered_count += 1
            upgraded_ltv_recovered += tx.get("customer_ltv", 15000.0)
            if t in tier_stats:
                tier_stats[t]["recovered"] += 1
                tier_stats[t]["amount_recovered"] += tx["amount"]
                tier_stats[t]["ltv_recovered"] += tx.get("customer_ltv", 15000.0)
        elif res["status"] == "SKIPPED":
            upgraded_skipped_count += 1
        elif res["status"] == "SUPPRESSED":
            upgraded_suppressed_count += 1
        else:
            upgraded_failed_count += 1

    # --- SWEEP 3: AUTONOMOUS POLICY COPILOT (5% Dynamic Discount on Drop-off Carts > ₹2,000) ---
    policy_discount = parse_natural_language_policy("Give 5% dynamic discount on dropped UPI carts > 2000")
    copilot_disc_results = []
    copilot_disc_recovered_count = 0
    copilot_disc_gross_savings = 0.0
    copilot_disc_discounts_given = 0.0
    copilot_disc_total_costs = 0.0
    copilot_disc_ltv_recovered = 0.0
    
    for tx in transactions:
        res = agent.process_transaction(tx, use_fallback=True, policy=policy_discount)
        copilot_disc_results.append(res)
        copilot_disc_total_costs += res["total_cost"]
        
        if res["status"] == "RECOVERED":
            copilot_disc_recovered_count += 1
            copilot_disc_gross_savings += res["amount"]
            copilot_disc_discounts_given += res.get("discount_amount", 0.0)
            copilot_disc_ltv_recovered += tx.get("customer_ltv", 15000.0)

    # --- SWEEP 4: AUTONOMOUS CHURN ZERO-RETRY POLICY (Strict Zero Retries for Churn Score > 0.8) ---
    policy_churn = parse_natural_language_policy("Strict Zero Retries for Churn Score > 0.8")
    copilot_churn_results = []
    copilot_churn_halted_count = 0
    copilot_churn_recovered_count = 0
    copilot_churn_gross_savings = 0.0
    copilot_churn_total_costs = 0.0
    
    for tx in transactions:
        res = agent.process_transaction(tx, use_fallback=True, policy=policy_churn)
        copilot_churn_results.append(res)
        copilot_churn_total_costs += res["total_cost"]
        if res["status"] == "CHURN_HALTED":
            copilot_churn_halted_count += 1
        elif res["status"] == "RECOVERED":
            copilot_churn_recovered_count += 1
            copilot_churn_gross_savings += res["amount"]
            
    # Calculate Key Metrics
    baseline_net_profit_saved = baseline_gross_savings - baseline_total_costs
    baseline_count_recovery_pct = (baseline_recovered_count / total_count) * 100 if total_count > 0 else 0
    baseline_val_recovery_pct = (baseline_gross_savings / total_at_risk) * 100 if total_at_risk > 0 else 0
    baseline_ltv_recovery_pct = (baseline_ltv_recovered / total_ltv_at_risk) * 100 if total_ltv_at_risk > 0 else 0
    baseline_roi = (baseline_gross_savings / baseline_total_costs * 100) if baseline_total_costs > 0 else float('inf')
    
    upgraded_net_profit_saved = upgraded_gross_savings - upgraded_total_costs
    upgraded_count_recovery_pct = (upgraded_recovered_count / total_count) * 100 if total_count > 0 else 0
    upgraded_val_recovery_pct = (upgraded_gross_savings / total_at_risk) * 100 if total_at_risk > 0 else 0
    upgraded_ltv_recovery_pct = (upgraded_ltv_recovered / total_ltv_at_risk) * 100 if total_ltv_at_risk > 0 else 0
    upgraded_roi = (upgraded_gross_savings / upgraded_total_costs * 100) if upgraded_total_costs > 0 else float('inf')
    
    copilot_net_profit = (copilot_disc_gross_savings - copilot_disc_discounts_given) - copilot_disc_total_costs
    copilot_count_recovery_pct = (copilot_disc_recovered_count / total_count) * 100 if total_count > 0 else 0

    # Save upgraded results for Streamlit
    os.makedirs("data", exist_ok=True)
    with open("data/dunning_results.json", "w", encoding="utf-8") as f:
        json.dump(upgraded_results, f, indent=4)
        
    # Terminal Scorecard
    print("\n" + "="*95)
    print(" " * 22 + "SMARTDUNNING AI ENTERPRISE EVALUATION SCORECARD")
    print("="*95)
    print(f" { 'Metric':<38} | { 'Baseline Engine':<16} | { 'Tier-1 Smart Engine':<18} | { 'Copilot 5% Disc':<16}")
    print("-"*95)
    print(f" { 'Total Failed Transactions':<38} | {total_count:<16} | {total_count:<18} | {total_count:<16}")
    print(f" { 'Total Direct Volume At Risk':<38} | Rs {total_at_risk:,.2f}{'':<4} | Rs {total_at_risk:,.2f}{'':<6} | Rs {total_at_risk:,.2f}")
    print(f" { 'Total Customer LTV Equity At Risk':<38} | Rs {total_ltv_at_risk:,.2f}{'':<4} | Rs {total_ltv_at_risk:,.2f}{'':<6} | Rs {total_ltv_at_risk:,.2f}")
    print("-"*95)
    print(f" { 'Recovered Transactions':<38} | {baseline_recovered_count} ({baseline_count_recovery_pct:.1f}%){'':<4} | {upgraded_recovered_count} ({upgraded_count_recovery_pct:.1f}%){'':<6} | {copilot_disc_recovered_count} ({copilot_count_recovery_pct:.1f}%)")
    print(f" { 'Direct Volume Recovered (GMV)':<38} | Rs {baseline_gross_savings:,.2f}{'':<4} | Rs {upgraded_gross_savings:,.2f}{'':<6} | Rs {copilot_disc_gross_savings:,.2f}")
    print(f" { 'Customer LTV Equity Preserved':<38} | Rs {baseline_ltv_recovered:,.2f}{'':<4} | Rs {upgraded_ltv_recovered:,.2f}{'':<6} | Rs {copilot_disc_ltv_recovered:,.2f}")
    print(f" { 'Total Dunning Messaging Cost':<38} | Rs {baseline_total_costs:,.2f}{'':<6} | Rs {upgraded_total_costs:,.2f}{'':<8} | Rs {copilot_disc_total_costs:,.2f}")
    print(f" { 'Dynamic Merchant Discounts Given':<38} | Rs 0.00{'':<10} | Rs 0.00{'':<12} | Rs {copilot_disc_discounts_given:,.2f}")
    print("-"*95)
    print(f" { 'NET MERCHANT PROFIT SAVED':<38} | Rs {baseline_net_profit_saved:,.2f}{'':<4} | Rs {upgraded_net_profit_saved:,.2f}{'':<6} | Rs {copilot_net_profit:,.2f}")
    
    roi_base_str = "Infinite" if baseline_roi == float('inf') else f"{baseline_roi:,.1f}%"
    roi_up_str = "Infinite" if upgraded_roi == float('inf') else f"{upgraded_roi:,.1f}%"
    print(f" { 'Dunning Unit Economic ROI':<38} | {roi_base_str:<16} | {roi_up_str:<18} | {(copilot_disc_gross_savings/copilot_disc_total_costs*100):,.1f}%")
    print("="*95)
    
    print("\n" + "="*95)
    print(" " * 24 + "AUTONOMOUS POLICY FLEXIBILITY EVALUATION")
    print("="*95)
    print(f" [Test 1] Dynamic 5% Discount Cart Policy:")
    print(f"   - Rule Target           : {policy_discount['rule_description']}")
    print(f"   - Recovery Count Lift   : +{copilot_disc_recovered_count - upgraded_recovered_count} additional carts settled via 1-tap incentive")
    print(f"   - Incremental GMV Saved : Rs +{copilot_disc_gross_savings - upgraded_gross_savings:,.2f}")
    print(f"   - Net Realized Margin   : Rs {copilot_net_profit:,.2f} (after accounting for Rs {copilot_disc_discounts_given:,.2f} in merchant discounts)")
    print(f"\n [Test 2] High Churn Score Suppression Policy:")
    print(f"   - Rule Target           : {policy_churn['rule_description']}")
    print(f"   - Transactions Halted   : {copilot_churn_halted_count} high-churn dropoffs shielded from spam retries")
    print(f"   - Overhead Cost Saved   : Rs {upgraded_total_costs - copilot_churn_total_costs:,.2f} in prevented notification cost")
    print("="*95 + "\n")

if __name__ == "__main__":
    run_evaluation()
