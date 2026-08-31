import json
import os
from mock_data import generate_mock_data
from agent import SmartDunningAgent

def run_evaluation():
    # Always generate new mock data to guarantee that the bank field exists
    print("Generating fresh mock transaction data with bank tags...")
    generate_mock_data()
        
    with open("data/failed_payments.json", "r") as f:
        transactions = json.load(f)
        
    agent = SmartDunningAgent(min_amount_threshold=20.0, max_retries=3)
    
    total_count = len(transactions)
    total_at_risk = sum(tx["amount"] for tx in transactions)
    
    # --- SWEEP 1: BASELINE DUNNING (No dynamic bank fallback) ---
    baseline_results = []
    baseline_recovered_count = 0
    baseline_skipped_count = 0
    baseline_suppressed_count = 0
    baseline_failed_count = 0
    baseline_gross_savings = 0.0
    baseline_total_costs = 0.0
    
    for tx in transactions:
        # Run agent without fallback routing
        res = agent.process_transaction(tx, use_fallback=False)
        baseline_results.append(res)
        baseline_total_costs += res["total_cost"]
        
        if res["status"] == "RECOVERED":
            baseline_gross_savings += res["amount"]
            baseline_recovered_count += 1
        elif res["status"] == "SKIPPED":
            baseline_skipped_count += 1
        elif res["status"] == "SUPPRESSED":
            baseline_suppressed_count += 1
        else:
            baseline_failed_count += 1
            
    # --- SWEEP 2: UPGRADED DUNNING (With dynamic bank fallback) ---
    upgraded_results = []
    upgraded_recovered_count = 0
    upgraded_skipped_count = 0
    upgraded_suppressed_count = 0
    upgraded_failed_count = 0
    upgraded_gross_savings = 0.0
    upgraded_total_costs = 0.0
    
    for tx in transactions:
        # Run agent with fallback routing
        res = agent.process_transaction(tx, use_fallback=True)
        upgraded_results.append(res)
        upgraded_total_costs += res["total_cost"]
        
        if res["status"] == "RECOVERED":
            upgraded_gross_savings += res["amount"]
            upgraded_recovered_count += 1
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
    baseline_eligible_count = total_count - baseline_skipped_count - baseline_suppressed_count
    baseline_eligible_recovery_pct = (baseline_recovered_count / baseline_eligible_count) * 100 if baseline_eligible_count > 0 else 0
    baseline_roi = (baseline_gross_savings / baseline_total_costs * 100) if baseline_total_costs > 0 else float('inf')
    
    # Upgraded
    upgraded_net_profit_saved = upgraded_gross_savings - upgraded_total_costs
    upgraded_count_recovery_pct = (upgraded_recovered_count / total_count) * 100 if total_count > 0 else 0
    upgraded_val_recovery_pct = (upgraded_gross_savings / total_at_risk) * 100 if total_at_risk > 0 else 0
    upgraded_eligible_count = total_count - upgraded_skipped_count - upgraded_suppressed_count
    upgraded_eligible_recovery_pct = (upgraded_recovered_count / upgraded_eligible_count) * 100 if upgraded_eligible_count > 0 else 0
    upgraded_roi = (upgraded_gross_savings / upgraded_total_costs * 100) if upgraded_total_costs > 0 else float('inf')
    
    # Differences
    recovery_count_gain = upgraded_recovered_count - baseline_recovered_count
    recovery_rate_gain = upgraded_count_recovery_pct - baseline_count_recovery_pct
    val_recovery_gain = upgraded_val_recovery_pct - baseline_val_recovery_pct
    net_profit_gain = upgraded_net_profit_saved - baseline_net_profit_saved

    # Save the upgraded processed results for use in Streamlit
    os.makedirs("data", exist_ok=True)
    with open("data/dunning_results.json", "w") as f:
        json.dump(upgraded_results, f, indent=4)
        
    # Print terminal scorecard
    print("\n" + "="*80)
    print(" " * 20 + "SMARTDUNNING AI COMPARATIVE EVALUATION SCORECARD")
    print("="*80)
    print(f" { 'Metric':<34} | { 'Baseline Dunning':<20} | { 'Upgraded Dunning':<20}")
    print("-"*80)
    print(f" { 'Total Failed Transactions':<34} | {total_count:<20} | {total_count:<20}")
    print(f" { 'Total Volume At Risk':<34} | Rs {total_at_risk:,.2f}{'':<8} | Rs {total_at_risk:,.2f}{'':<8}")
    print(f" { 'Skipped Guardrail (< Rs 20)':<34} | {baseline_skipped_count:<20} | {upgraded_skipped_count:<20}")
    print(f" { 'Suppressed (Hard Auth Failures)':<34} | {baseline_suppressed_count:<20} | {upgraded_suppressed_count:<20}")
    print(f" { 'Eligible for Dunning':<34} | {baseline_eligible_count:<20} | {upgraded_eligible_count:<20}")
    print("-"*80)
    print(f" { 'Recovered Transactions':<34} | {baseline_recovered_count} ({baseline_count_recovery_pct:.1f}%){'':<8} | {upgraded_recovered_count} ({upgraded_count_recovery_pct:.1f}%)")
    print(f" { 'Recovery Rate on Eligible':<34} | {baseline_eligible_recovery_pct:.1f}%{'':<15} | {upgraded_eligible_recovery_pct:.1f}%")
    print(f" { 'Gross Savings (Recovered Volume)':<34} | Rs {baseline_gross_savings:,.2f}{'':<8} | Rs {upgraded_gross_savings:,.2f}")
    print(f" { 'Value Recovery Rate %':<34} | {baseline_val_recovery_pct:.2f}%{'':<13} | {upgraded_val_recovery_pct:.2f}%")
    print(f" { 'Total Notification Costs':<34} | Rs {baseline_total_costs:,.2f}{'':<10} | Rs {upgraded_total_costs:,.2f}")
    print("-"*80)
    print(f" { 'NET PROFIT SAVED':<34} | Rs {baseline_net_profit_saved:,.2f}{'':<8} | Rs {upgraded_net_profit_saved:,.2f}")
    
    roi_base_str = "Infinite" if baseline_roi == float('inf') else f"{baseline_roi:,.1f}%"
    roi_up_str = "Infinite" if upgraded_roi == float('inf') else f"{upgraded_roi:,.1f}%"
    print(f" { 'Dunning ROI':<34} | {roi_base_str:<20} | {roi_up_str:<20}")
    print("="*80)
    print(f" >>> PERFORMANCE GAIN FROM DYNAMIC BANK RAIL SWITCHING:")
    print(f"  - Recovery Count Improvement : +{recovery_rate_gain:.1f}% ({recovery_count_gain} more customers recovered)")
    print(f"  - Value Recovery Improvement : +{val_recovery_gain:.2f}%")
    print(f"  - Incremental Net Profit Saved: Rs {net_profit_gain:,.2f}")
    print("="*80 + "\n")
    
    print("Successfully generated data/dunning_results.json using upgraded engine.")

if __name__ == "__main__":
    run_evaluation()
