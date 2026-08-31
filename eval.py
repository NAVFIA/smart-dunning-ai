import json
import os
from mock_data import generate_mock_data
from agent import SmartDunningAgent

def run_evaluation():
    print("Generating fresh mock transaction data with LTV and tiering tags...")
    generate_mock_data()
        
    with open("data/failed_payments.json", "r") as f:
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
    
    # Tier breakdown dict
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
            
    # Calculate Key Metrics
    # Baseline
    baseline_net_profit_saved = baseline_gross_savings - baseline_total_costs
    baseline_count_recovery_pct = (baseline_recovered_count / total_count) * 100 if total_count > 0 else 0
    baseline_val_recovery_pct = (baseline_gross_savings / total_at_risk) * 100 if total_at_risk > 0 else 0
    baseline_ltv_recovery_pct = (baseline_ltv_recovered / total_ltv_at_risk) * 100 if total_ltv_at_risk > 0 else 0
    baseline_eligible_count = total_count - baseline_skipped_count - baseline_suppressed_count
    baseline_eligible_recovery_pct = (baseline_recovered_count / baseline_eligible_count) * 100 if baseline_eligible_count > 0 else 0
    baseline_roi = (baseline_gross_savings / baseline_total_costs * 100) if baseline_total_costs > 0 else float('inf')
    
    # Upgraded
    upgraded_net_profit_saved = upgraded_gross_savings - upgraded_total_costs
    upgraded_count_recovery_pct = (upgraded_recovered_count / total_count) * 100 if total_count > 0 else 0
    upgraded_val_recovery_pct = (upgraded_gross_savings / total_at_risk) * 100 if total_at_risk > 0 else 0
    upgraded_ltv_recovery_pct = (upgraded_ltv_recovered / total_ltv_at_risk) * 100 if total_ltv_at_risk > 0 else 0
    upgraded_eligible_count = total_count - upgraded_skipped_count - upgraded_suppressed_count
    upgraded_eligible_recovery_pct = (upgraded_recovered_count / upgraded_eligible_count) * 100 if upgraded_eligible_count > 0 else 0
    upgraded_roi = (upgraded_gross_savings / upgraded_total_costs * 100) if upgraded_total_costs > 0 else float('inf')
    
    # Differences
    recovery_count_gain = upgraded_recovered_count - baseline_recovered_count
    recovery_rate_gain = upgraded_count_recovery_pct - baseline_count_recovery_pct
    val_recovery_gain = upgraded_val_recovery_pct - baseline_val_recovery_pct
    ltv_recovery_gain = upgraded_ltv_recovery_pct - baseline_ltv_recovery_pct
    net_profit_gain = upgraded_net_profit_saved - baseline_net_profit_saved

    # Save upgraded results for Streamlit
    os.makedirs("data", exist_ok=True)
    with open("data/dunning_results.json", "w") as f:
        json.dump(upgraded_results, f, indent=4)
        
    # Terminal Scorecard
    print("\n" + "="*85)
    print(" " * 18 + "SMARTDUNNING AI ENTERPRISE EVALUATION SCORECARD")
    print("="*85)
    print(f" { 'Metric':<38} | { 'Baseline Engine':<20} | { 'Tier-1 Smart Engine':<20}")
    print("-"*85)
    print(f" { 'Total Failed Transactions':<38} | {total_count:<20} | {total_count:<20}")
    print(f" { 'Total Direct Volume At Risk':<38} | Rs {total_at_risk:,.2f}{'':<8} | Rs {total_at_risk:,.2f}{'':<8}")
    print(f" { 'Total Customer LTV Equity At Risk':<38} | Rs {total_ltv_at_risk:,.2f}{'':<8} | Rs {total_ltv_at_risk:,.2f}{'':<8}")
    print(f" { 'Skipped Guardrail (< Rs 20)':<38} | {baseline_skipped_count:<20} | {upgraded_skipped_count:<20}")
    print(f" { 'Suppressed (Hard Auth Failures)':<38} | {baseline_suppressed_count:<20} | {upgraded_suppressed_count:<20}")
    print(f" { 'Eligible for Dunning Intervention':<38} | {baseline_eligible_count:<20} | {upgraded_eligible_count:<20}")
    print("-"*85)
    print(f" { 'Recovered Transactions':<38} | {baseline_recovered_count} ({baseline_count_recovery_pct:.1f}%){'':<8} | {upgraded_recovered_count} ({upgraded_count_recovery_pct:.1f}%)")
    print(f" { 'Recovery Rate on Eligible':<38} | {baseline_eligible_recovery_pct:.1f}%{'':<15} | {upgraded_eligible_recovery_pct:.1f}%")
    print(f" { 'Direct Volume Recovered (GMV)':<38} | Rs {baseline_gross_savings:,.2f}{'':<8} | Rs {upgraded_gross_savings:,.2f}")
    print(f" { 'Customer LTV Equity Preserved':<38} | Rs {baseline_ltv_recovered:,.2f}{'':<8} | Rs {upgraded_ltv_recovered:,.2f}")
    print(f" { 'Direct Value Recovery Rate %':<38} | {baseline_val_recovery_pct:.2f}%{'':<13} | {upgraded_val_recovery_pct:.2f}%")
    print(f" { 'LTV-Weighted Recovery Rate %':<38} | {baseline_ltv_recovery_pct:.2f}%{'':<13} | {upgraded_ltv_recovery_pct:.2f}%")
    print(f" { 'Total Dunning Overhead Cost':<38} | Rs {baseline_total_costs:,.2f}{'':<10} | Rs {upgraded_total_costs:,.2f}")
    print("-"*85)
    print(f" { 'NET MERCHANT PROFIT SAVED':<38} | Rs {baseline_net_profit_saved:,.2f}{'':<8} | Rs {upgraded_net_profit_saved:,.2f}")
    
    roi_base_str = "Infinite" if baseline_roi == float('inf') else f"{baseline_roi:,.1f}%"
    roi_up_str = "Infinite" if upgraded_roi == float('inf') else f"{upgraded_roi:,.1f}%"
    print(f" { 'Dunning Unit Economic ROI':<38} | {roi_base_str:<20} | {roi_up_str:<20}")
    print("="*85)
    print(f" >>> PERFORMANCE GAIN FROM DYNAMIC TELEMETRY & LTV TIERING:")
    print(f"  - Customer Recovery Gain     : +{recovery_rate_gain:.1f}% ({recovery_count_gain} more customers preserved)")
    print(f"  - Direct GMV Lift            : +{val_recovery_gain:.2f}% (Rs +{upgraded_gross_savings - baseline_gross_savings:,.2f})")
    print(f"  - LTV Equity Preserved Gain  : +{ltv_recovery_gain:.2f}% (Rs +{upgraded_ltv_recovered - baseline_ltv_recovered:,.2f})")
    print(f"  - Incremental Net Profit     : Rs {net_profit_gain:,.2f}")
    print("="*85)
    
    # Customer Tier Breakdown
    print("\n" + "-"*85)
    print(" " * 28 + "CUSTOMER TIER PERFORMANCE BREAKDOWN")
    print("-"*85)
    print(f" { 'Segment':<20} | { 'Total':<8} | { 'Recovered':<12} | { 'Recovery %':<12} | { 'LTV Preserved':<18}")
    print("-"*85)
    for seg, data in tier_stats.items():
        rate = (data['recovered'] / data['total'] * 100) if data['total'] > 0 else 0
        print(f" { seg:<20} | { data['total']:<8} | { data['recovered']:<12} | { rate:.1f}%{'':<6} | Rs {data['ltv_recovered']:,.2f}")
    print("-"*85)
    
    # Enterprise Scale-Up Projections
    print("\n" + "="*85)
    print(" " * 22 + "ENTERPRISE ANNUAL SCALE-UP PROJECTIONS")
    print("="*85)
    print(f" { 'Merchant Tier':<22} | { 'Annual GMV':<15} | { 'Recoverable GMV':<18} | { 'Net Profit Lift':<18}")
    print("-"*85)
    scale_tiers = [
        ("Emerging Merchant", 10_000_000),      # ₹1 Cr
        ("Growth Mid-Market", 100_000_000),     # ₹10 Cr
        ("Enterprise Leader", 1_000_000_000),   # ₹100 Cr
        ("Unicorn / Tier-1", 10_000_000_000)    # ₹1000 Cr
    ]
    
    # Assumptions: 12% failure rate, upgraded value recovery %
    assumed_failure_rate = 0.12
    val_rec_ratio = upgraded_val_recovery_pct / 100.0
    cost_ratio = (upgraded_total_costs / upgraded_gross_savings) if upgraded_gross_savings > 0 else 0.002
    
    for tier_name, annual_gmv in scale_tiers:
        at_risk_gmv = annual_gmv * assumed_failure_rate
        recovered_gmv = at_risk_gmv * val_rec_ratio
        est_cost = recovered_gmv * cost_ratio
        net_lift = recovered_gmv - est_cost
        
        print(f" { tier_name:<22} | Rs {annual_gmv/10000000:.1f} Cr{'':<7} | Rs {recovered_gmv/10000000:,.2f} Cr{'':<7} | Rs {net_lift/10000000:,.2f} Cr")
    print("="*85 + "\n")

if __name__ == "__main__":
    run_evaluation()
