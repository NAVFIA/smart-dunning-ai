import json
import os
from agent import SmartDunningAgent

def run_evaluation():
    # Check if failed_payments.json exists, if not generate it
    if not os.path.exists("data/failed_payments.json"):
        print("Mock data file not found. Generating mock data first...")
        from mock_data import generate_mock_data
        generate_mock_data()
        
    with open("data/failed_payments.json", "r") as f:
        transactions = json.load(f)
        
    agent = SmartDunningAgent(min_amount_threshold=50.0, max_retries=3)
    
    results = []
    total_at_risk = 0.0
    gross_savings = 0.0
    total_costs = 0.0
    
    total_count = len(transactions)
    skipped_count = 0
    recovered_count = 0
    failed_count = 0
    
    for tx in transactions:
        total_at_risk += tx["amount"]
        result = agent.process_transaction(tx)
        results.append(result)
        
        total_costs += result["total_cost"]
        if result["status"] == "RECOVERED":
            gross_savings += result["amount"]
            recovered_count += 1
        elif result["status"] == "SKIPPED":
            skipped_count += 1
        else:
            failed_count += 1
            
    # Calculate key metrics
    net_profit_saved = gross_savings - total_costs
    val_recovery_pct = (gross_savings / total_at_risk) * 100 if total_at_risk > 0 else 0
    count_recovery_pct = (recovered_count / total_count) * 100 if total_count > 0 else 0
    eligible_count = total_count - skipped_count
    eligible_recovery_pct = (recovered_count / eligible_count) * 100 if eligible_count > 0 else 0
    roi = (gross_savings / total_costs * 100) if total_costs > 0 else float('inf')
    
    # Save the processed results back for use in streamlit
    os.makedirs("data", exist_ok=True)
    with open("data/dunning_results.json", "w") as f:
        json.dump(results, f, indent=4)
        
    # Print terminal scorecard
    print("\n" + "="*70)
    print(" " * 18 + "SMARTDUNNING AI BENCHMARK SCORECARD")
    print("="*70)
    print(f" { 'Metric':<35} | {'Value':<28}")
    print("-"*70)
    print(f" { 'Total Failed Transactions':<35} | {total_count:<28}")
    print(f" { 'Total Volume At Risk':<35} | Rs {total_at_risk:,.2f}")
    print(f" { 'Skipped Guardrail (< Rs 50)':<35} | {skipped_count:<28}")
    print(f" { 'Eligible for Dunning (>= Rs 50)':<35} | {eligible_count:<28}")
    print("-"*70)
    print(f" { 'Total Recovered (Transactions)':<35} | {recovered_count} / {total_count} ({count_recovery_pct:.1f}%)")
    print(f" { 'Recovery Rate on Eligible':<35} | {recovered_count} / {eligible_count} ({eligible_recovery_pct:.1f}%)")
    print(f" { 'Gross Savings (Volume Recovered)':<35} | Rs {gross_savings:,.2f}")
    print(f" { 'Value Recovery %':<35} | {val_recovery_pct:.2f}%")
    print(f" { 'Total Notification Costs':<35} | Rs {total_costs:,.2f}")
    print("-"*70)
    print(f" { 'NET PROFIT SAVED':<35} | Rs {net_profit_saved:,.2f}")
    if roi == float('inf'):
        print(f" { 'Dunning ROI':<35} | Infinite (Zero cost)")
    else:
        print(f" { 'Dunning ROI':<35} | {roi:,.1f}% ({gross_savings/total_costs:.1f}x savings-to-cost)")
    print("="*70 + "\n")
    
    print("Successfully processed all 100 transactions and generated data/dunning_results.json.")

if __name__ == "__main__":
    run_evaluation()
