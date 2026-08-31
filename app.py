import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime
from agent import SmartDunningAgent, BankTelemetry, RetryWindowOptimizer

# Set page config for wide layout and premium design feel
st.set_page_config(
    page_title="SmartDunning AI - Enterprise Recovery Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for custom styling & micro-animations
st.markdown("""
<style>
    .reportview-container {
        background: #0F172A;
    }
    .metric-card {
        background-color: #1E293B;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        border: 1px solid #334155;
        transition: transform 0.2s ease-in-out;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        border-color: #6366F1;
    }
    .metric-title {
        color: #94A3B8;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .metric-value {
        color: #F8FAFC;
        font-size: 26px;
        font-weight: 700;
    }
    .metric-sub {
        color: #10B981;
        font-size: 12px;
        margin-top: 4px;
    }
    .tier-badge {
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# App Title & Header
st.title("⚡ SmartDunning AI - Enterprise Recovery Engine")
st.markdown("##### Production-grade payment recovery, bank telemetry multi-rail routing, customer LTV tiering, and unit-economic ROI analytics.")

# Check for data files or if results are outdated
results_path = "data/dunning_results.json"
failed_payments_path = "data/failed_payments.json"

outdated = False
if os.path.exists(results_path):
    try:
        with open(results_path, "r") as f:
            test_data = json.load(f)
        if len(test_data) > 0 and ("bank" not in test_data[0] or "customer_ltv" not in test_data[0]):
            outdated = True
    except Exception:
        outdated = True

if not os.path.exists(results_path) or outdated:
    st.info("📊 Results data not found or updating. Running enterprise evaluation simulation...")
    if os.path.exists(results_path):
        os.remove(results_path)
    if os.path.exists(failed_payments_path):
        os.remove(failed_payments_path)
        
    from mock_data import generate_mock_data
    generate_mock_data()
    
    from eval import run_evaluation
    run_evaluation()

# Load Results
with open(results_path, "r") as f:
    data = json.load(f)

# Convert to DataFrame
df = pd.DataFrame(data)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values('timestamp')

# ----------------- SIDEBAR FILTERS -----------------
st.sidebar.image("https://img.icons8.com/nolan/96/artificial-intelligence.png", width=70)
st.sidebar.header("🎯 Filters & Parameters")

# Filter: Category
categories = ["All"] + list(df['failure_category'].unique())
selected_category = st.sidebar.selectbox("Failure Category", categories)

# Filter: Customer Tier
tiers = ["All"] + list(df['customer_tier'].unique()) if 'customer_tier' in df.columns else ["All"]
selected_tier = st.sidebar.selectbox("Customer LTV Tier", tiers)

# Filter: Status
statuses = ["All"] + list(df['status'].unique())
selected_status = st.sidebar.selectbox("Recovery Status", statuses)

# Filter: Value Slider
min_amt = float(df['amount'].min())
max_amt = float(df['amount'].max())
amount_range = st.sidebar.slider("Transaction Amount (Rs)", min_amt, max_amt, (min_amt, max_amt))

# Search box
search_query = st.sidebar.text_input("🔍 Search Customer, Phone, Bank, TxID")

# Apply Filters
filtered_df = df.copy()

if selected_category != "All":
    filtered_df = filtered_df[filtered_df['failure_category'] == selected_category]

if selected_tier != "All" and 'customer_tier' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['customer_tier'] == selected_tier]

if selected_status != "All":
    filtered_df = filtered_df[filtered_df['status'] == selected_status]

filtered_df = filtered_df[
    (filtered_df['amount'] >= amount_range[0]) & 
    (filtered_df['amount'] <= amount_range[1])
]

if search_query:
    filtered_df = filtered_df[
        filtered_df['customer_name'].str.contains(search_query, case=False) |
        filtered_df['customer_email'].str.contains(search_query, case=False) |
        filtered_df['customer_phone'].str.contains(search_query, case=False) |
        filtered_df['bank'].str.contains(search_query, case=False) |
        filtered_df['transaction_id'].str.contains(search_query, case=False)
    ]

# ----------------- TABS SYSTEM -----------------
tab1, tab2, tab3 = st.tabs([
    "📊 Batch Revenue Recovery Benchmark",
    "⚡ Live Rail Telemetry & Webhook Sandbox",
    "📈 Enterprise ROI Calculator"
])

# ==============================================================================
# TAB 1: BENCHMARK & SANKEY PIPELINE
# ==============================================================================
with tab1:
    total_at_risk = filtered_df['amount'].sum()
    total_ltv_at_risk = filtered_df['customer_ltv'].sum() if 'customer_ltv' in filtered_df.columns else 0.0
    recovered_df = filtered_df[filtered_df['status'] == 'RECOVERED']
    failed_df = filtered_df[filtered_df['status'] == 'FAILED']
    skipped_df = filtered_df[filtered_df['status'] == 'SKIPPED']
    suppressed_df = filtered_df[filtered_df['status'] == 'SUPPRESSED'] if 'status' in filtered_df.columns and 'SUPPRESSED' in filtered_df['status'].values else pd.DataFrame()

    gross_savings = recovered_df['amount'].sum()
    ltv_recovered = recovered_df['customer_ltv'].sum() if 'customer_ltv' in recovered_df.columns else 0.0
    total_costs = filtered_df['total_cost'].sum()
    net_profit_saved = gross_savings - total_costs

    recovery_rate_pct = (len(recovered_df) / len(filtered_df) * 100) if len(filtered_df) > 0 else 0.0
    value_recovery_pct = (gross_savings / total_at_risk * 100) if total_at_risk > 0 else 0.0
    ltv_recovery_pct = (ltv_recovered / total_ltv_at_risk * 100) if total_ltv_at_risk > 0 else 0.0

    # Metrics Cards
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Direct GMV at Risk</div>
            <div class="metric-value">₹{total_at_risk:,.2f}</div>
            <div class="metric-sub" style="color: #94A3B8;">{len(filtered_df)} failed txs</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Direct GMV Recovered</div>
            <div class="metric-value" style="color: #10B981;">₹{gross_savings:,.2f}</div>
            <div class="metric-sub">{len(recovered_df)} txs ({value_recovery_pct:.1f}% value)</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Customer LTV Saved</div>
            <div class="metric-value" style="color: #6366F1;">₹{ltv_recovered:,.2f}</div>
            <div class="metric-sub">Equity Retained: {ltv_recovery_pct:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Net Profit Saved</div>
            <div class="metric-value" style="color: #10B981;">₹{net_profit_saved:,.2f}</div>
            <div class="metric-sub">Dunning Cost: ₹{total_costs:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Unit Economic ROI</div>
            <div class="metric-value">{((gross_savings/total_costs)*100 if total_costs > 0 else 0):,.0f}%</div>
            <div class="metric-sub" style="color: #6366F1;">{(gross_savings/total_costs if total_costs > 0 else 0):,.1f}x Savings-to-Cost</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # ----------------- SANKEY PIPELINE DIAGRAM -----------------
    st.markdown("### 🔀 Root-Cause Triage & Dynamic Resolution Pipeline")
    st.markdown("End-to-end visualization of transactions through Root-Cause Classification, Guardrail Policy Checks, Interventions, and Recovery Outcomes.")

    # Build dynamic Sankey nodes & links
    if len(filtered_df) > 0:
        node_labels = [
            "Total Ingested Failures",         # 0
            "Technical / Transient",          # 1
            "User Drop-off / Abandoned",      # 2
            "Insufficient Balance",           # 3
            "Hard Auth / Mandate Fail",       # 4
            "Dunning Active (Eligible)",       # 5
            "Guardrail: Skipped (< Rs 20)",   # 6
            "Policy: Suppressed (Hard Auth)", # 7
            "VIP White-Glove WhatsApp",       # 8
            "Dynamic UPI Intent Fallback",    # 9
            "Intelligent Auto-Retry",         # 10
            "Multi-Rail SMS / Email",         # 11
            "✅ Recovered Revenue",            # 12
            "❌ Unrecovered / Halted"          # 13
        ]

        # Counts
        cnt_tech = len(filtered_df[filtered_df['failure_category'] == 'TECHNICAL_TRANSIENT'])
        cnt_drop = len(filtered_df[filtered_df['failure_category'] == 'USER_DROPOFF'])
        cnt_bal = len(filtered_df[filtered_df['failure_category'] == 'USER_BALANCE'])
        cnt_auth = len(filtered_df[filtered_df['failure_category'] == 'AUTHENTICATION_HARD'])

        cnt_skip = len(skipped_df)
        cnt_supp = len(suppressed_df)
        cnt_active = len(filtered_df) - cnt_skip - cnt_supp

        # Interventions
        cnt_vip = 0
        cnt_fallback = 0
        cnt_auto = 0
        cnt_standard = 0

        for hists in filtered_df['history']:
            for h in hists:
                act = h.get("action", "")
                if act == "WHATSAPP_VIP_WHITEGLOVE":
                    cnt_vip += 1
                elif "FALLBACK" in act:
                    cnt_fallback += 1
                elif act == "AUTO_RETRY":
                    cnt_auto += 1
                elif act in ["WHATSAPP_LINK", "SMS_LINK", "EMAIL_LINK", "WHATSAPP_BALANCE_REMINDER", "SMS_BALANCE_REMINDER"]:
                    cnt_standard += 1

        tot_interventions = max(1, cnt_vip + cnt_fallback + cnt_auto + cnt_standard)
        
        cnt_rec = len(recovered_df)
        cnt_fail = len(failed_df) + cnt_skip + cnt_supp

        sources = [
            # Ingestion -> Categories
            0, 0, 0, 0,
            # Categories -> Guardrails/Eligibility
            1, 2, 3, 4,
            # Eligible -> Interventions
            5, 5, 5, 5,
            # Interventions -> Outcomes
            8, 9, 10, 11,
            # Guardrails -> Halted
            6, 7
        ]
        targets = [
            1, 2, 3, 4,
            5, 5, 5, 7,
            8, 9, 10, 11,
            12, 12, 12, 12,
            13, 13
        ]
        values = [
            max(0.1, cnt_tech), max(0.1, cnt_drop), max(0.1, cnt_bal), max(0.1, cnt_auth),
            max(0.1, cnt_tech), max(0.1, cnt_drop), max(0.1, cnt_bal), max(0.1, cnt_auth),
            max(0.1, cnt_active * (cnt_vip / tot_interventions)),
            max(0.1, cnt_active * (cnt_fallback / tot_interventions)),
            max(0.1, cnt_active * (cnt_auto / tot_interventions)),
            max(0.1, cnt_active * (cnt_standard / tot_interventions)),
            max(0.1, cnt_rec * 0.25),
            max(0.1, cnt_rec * 0.40),
            max(0.1, cnt_rec * 0.15),
            max(0.1, cnt_rec * 0.20),
            max(0.1, cnt_skip),
            max(0.1, cnt_supp)
        ]

        fig_sankey = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="#0F172A", width=0.5),
                label=node_labels,
                color=[
                    "#6366F1",  # Ingested
                    "#38BDF8", "#F59E0B", "#EC4899", "#EF4444", # Categories
                    "#10B981", "#94A3B8", "#F43F5E", # Policies
                    "#8B5CF6", "#06B6D4", "#F97316", "#A855F7", # Interventions
                    "#10B981", "#EF4444" # Outcomes
                ]
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color="rgba(99, 102, 241, 0.25)"
            )
        )])
        fig_sankey.update_layout(
            title_text="Payment Recovery & Multi-Rail Fallback Flow",
            font_size=12,
            font_color="#F8FAFC",
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=420
        )
        st.plotly_chart(fig_sankey, use_container_width=True)

    # ----------------- ANALYTICS CHARTS SECTION -----------------
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        # Category breakdown
        category_counts = filtered_df['failure_category'].value_counts().reset_index()
        category_counts.columns = ['Failure Category', 'Count']
        fig_pie = px.pie(
            category_counts, 
            values='Count', 
            names='Failure Category', 
            title='Failed Transactions by Category',
            color_discrete_sequence=px.colors.qualitative.G10,
            hole=0.4
        )
        fig_pie.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_pie, use_container_width=True)

    with chart_col2:
        # Customer Tier Recovery Efficiency
        if 'customer_tier' in filtered_df.columns:
            tier_df = filtered_df.groupby('customer_tier').agg(
                Total=('amount', 'count'),
                Recovered=('status', lambda s: (s == 'RECOVERED').sum()),
                LTV_Saved=('customer_ltv', lambda l: l[filtered_df.loc[l.index, 'status'] == 'RECOVERED'].sum())
            ).reset_index()
            tier_df['Recovery Rate %'] = (tier_df['Recovered'] / tier_df['Total']) * 100
            
            fig_tier = px.bar(
                tier_df,
                x='customer_tier',
                y='Recovery Rate %',
                title='Recovery Rate by Customer LTV Tier (%)',
                color='customer_tier',
                color_discrete_sequence=['#8B5CF6', '#38BDF8', '#F59E0B'],
                text_auto='.1f'
            )
            fig_tier.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
            st.plotly_chart(fig_tier, use_container_width=True)

    # ----------------- AUDIT LEDGER SECTION -----------------
    st.write("---")
    st.markdown("### 📒 Enterprise Payment Audit Ledger")
    st.markdown("Deep-dive transaction records with Customer LTV profiles, bank telemetry, and scheduled retry windows.")

    display_cols = ['transaction_id', 'customer_name', 'customer_tier', 'customer_ltv', 'amount', 'bank', 'failure_category', 'optimal_retry_window', 'attempts_made', 'total_cost', 'status']
    available_cols = [c for c in display_cols if c in filtered_df.columns]
    table_df = filtered_df[available_cols].copy()

    def highlight_status(val):
        if val == "RECOVERED":
            return 'color: #10B981; font-weight: bold;'
        elif val == "FAILED":
            return 'color: #F43F5E; font-weight: bold;'
        elif val == "SKIPPED":
            return 'color: #94A3B8; font-style: italic;'
        elif val == "SUPPRESSED":
            return 'color: #D97706; font-style: italic;'
        return ''

    def highlight_tier(val):
        if val == "VIP_HIGH_LTV":
            return 'color: #A855F7; font-weight: bold;'
        elif val == "HIGH_CHURN_RISK":
            return 'color: #F59E0B; font-weight: bold;'
        return 'color: #38BDF8;'

    st_styled = table_df.style.map(highlight_status, subset=['status']).map(highlight_tier, subset=['customer_tier'] if 'customer_tier' in table_df.columns else []).format({
        'amount': '₹{:,.2f}',
        'customer_ltv': '₹{:,.2f}',
        'total_cost': '₹{:.2f}'
    })

    st.dataframe(st_styled, use_container_width=True, height=350)

    # Detail Lookup
    selected_tx_id = st.selectbox(
        "Select a transaction to inspect its complete retry dunning history:",
        options=filtered_df['transaction_id'].tolist(),
        format_func=lambda x: f"{x} - {filtered_df[filtered_df['transaction_id'] == x]['customer_name'].values[0]} ({filtered_df[filtered_df['transaction_id'] == x]['customer_tier'].values[0] if 'customer_tier' in filtered_df.columns else ''} | ₹{filtered_df[filtered_df['transaction_id'] == x]['amount'].values[0]:.2f})",
        key="tx_audit_lookup"
    )

    if selected_tx_id:
        tx_detail = filtered_df[filtered_df['transaction_id'] == selected_tx_id].iloc[0]
        
        c_d1, c_d2, c_d3, c_d4 = st.columns(4)
        with c_d1:
            st.markdown(f"**Customer:** {tx_detail['customer_name']}")
            st.markdown(f"**Tier:** `{tx_detail.get('customer_tier', 'REGULAR')}`")
        with c_d2:
            st.markdown(f"**Customer LTV:** ₹{tx_detail.get('customer_ltv', 0):,.2f}")
            st.markdown(f"**Amount:** ₹{tx_detail['amount']:,.2f}")
        with c_d3:
            st.markdown(f"**Failed Bank:** `{tx_detail['bank']}`")
            st.markdown(f"**Failure Reason:** `{tx_detail['failure_reason']}`")
        with c_d4:
            st.markdown(f"**Optimal Retry Window:** `{tx_detail.get('optimal_retry_window', 'Immediate')}`")
            st.markdown(f"**Final Status:** `{tx_detail['status']}`")
            
        st.markdown("**Action Audit Trail History:**")
        for step in tx_detail['history']:
            success_icon = "✅ Success" if step.get("success") else "❌ Failed"
            if step["action"] == "SKIP":
                st.warning(f"⏩ **Guardrail Skip Action** — Reason: {step.get('reason')}")
            elif step["action"] == "SUPPRESS":
                st.info(f"🔕 **Suppression Action** — Reason: {step.get('reason')}")
            else:
                reroute_str = ""
                if step.get("rerouted"):
                    reroute_str = f" | Rerouted to **{step['fallback_bank']}** via **{step['fallback_handle']}**"
                st.info(
                    f"🔄 **Attempt {step['attempt']}**: Action `{step['action']}`{reroute_str} | "
                    f"Cost: ₹{step['cost']:.2f} | "
                    f"Success Probability: {step.get('probability', 0)*100:.1f}% | "
                    f"Result: **{success_icon}**"
                )

# ==============================================================================
# TAB 2: LIVE TELEMETRY & WEBHOOK SANDBOX
# ==============================================================================
with tab2:
    st.markdown("### ⚡ Live Payment Rail Telemetry & Webhook Sandbox")
    st.markdown("Monitor issuing bank health in real-time, test custom transaction webhook recovery scenarios, and preview automated communications.")

    telemetry = BankTelemetry()
    
    col_left, col_right = st.columns([2, 3])
    
    with col_left:
        st.markdown("#### 🏦 Issuing Bank Health Status")
        c1, c2 = st.columns(2)
        
        banks = ["HDFC", "SBI", "ICICI", "Axis"]
        for i, b in enumerate(banks):
            rate = telemetry.get_bank_rate(b)
            status = "Healthy" if rate >= 0.65 else "Degraded"
            icon = "🟢" if rate >= 0.65 else "🔴"
            color = "#10B981" if rate >= 0.65 else "#EF4444"
            target_col = c1 if i % 2 == 0 else c2
            
            with target_col:
                st.markdown(f"""
                <div style="background-color: #1E293B; border-radius: 12px; padding: 16px; border: 1px solid #334155; margin-bottom: 12px; text-align: center;">
                    <div style="font-size: 14px; font-weight: 600; color: #94A3B8; margin-bottom: 4px;">{b} NetBanking</div>
                    <div style="font-size: 20px; font-weight: 700; color: #F8FAFC; margin-bottom: 6px;">{rate*100:.0f}% Success</div>
                    <span style="background-color: {color}20; color: {color}; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 700; border: 1px solid {color}50;">
                        {icon} {status}
                    </span>
                </div>
                """, unsafe_allow_html=True)
                
        # UPI Handles Telemetry
        st.markdown("#### 📱 UPI Fallback Rails Telemetry")
        c3, c4, c5 = st.columns(3)
        upi_handles = ["@okhdfcbank", "@oksbi", "@paytm"]
        for i, h in enumerate(upi_handles):
            rate = telemetry.get_upi_rate(h)
            status = "Healthy" if rate >= 0.65 else "Degraded"
            icon = "🟢" if rate >= 0.65 else "🔴"
            color = "#10B981" if rate >= 0.65 else "#EF4444"
            target_col = c3 if i == 0 else (c4 if i == 1 else c5)
            
            with target_col:
                st.markdown(f"""
                <div style="background-color: #1E293B; border-radius: 12px; padding: 12px; border: 1px solid #334155; margin-bottom: 12px; text-align: center;">
                    <div style="font-size: 13px; font-weight: 600; color: #94A3B8; margin-bottom: 4px;">{h}</div>
                    <div style="font-size: 18px; font-weight: 700; color: #F8FAFC; margin-bottom: 6px;">{rate*100:.0f}% SR</div>
                    <span style="color: {color}; font-size: 11px; font-weight: 700;">
                        {icon} {status}
                    </span>
                </div>
                """, unsafe_allow_html=True)

        st.write("---")
        
        # Interactive Webhook Sandbox Form
        st.markdown("#### 🧪 Interactive Webhook Simulator")
        
        sim_name = st.selectbox(
            "Select Customer Profile",
            ["Rahul Sharma (VIP)", "Aarav Gupta (Regular)", "Kiara Sen (High Churn Risk)", "Custom..."],
            key="sim_name_selectbox"
        )
        
        if "VIP" in sim_name:
            def_tier = "VIP_HIGH_LTV"
            def_ltv = 65000.0
            def_name = "Rahul Sharma"
        elif "Churn" in sim_name:
            def_tier = "HIGH_CHURN_RISK"
            def_ltv = 8500.0
            def_name = "Kiara Sen"
        elif "Regular" in sim_name:
            def_tier = "REGULAR"
            def_ltv = 18000.0
            def_name = "Aarav Gupta"
        else:
            def_tier = "REGULAR"
            def_ltv = 15000.0
            def_name = "Raj Malhotra"

        customer_name = st.text_input("Customer Name", def_name, key="custom_name_input")
        sim_tier = st.selectbox("Customer Tier", ["VIP_HIGH_LTV", "REGULAR", "HIGH_CHURN_RISK"], index=["VIP_HIGH_LTV", "REGULAR", "HIGH_CHURN_RISK"].index(def_tier), key="sim_tier_select")
        sim_ltv = st.number_input("Customer LTV (Rs)", min_value=500.0, max_value=500000.0, value=def_ltv, step=1000.0, key="sim_ltv_input")
        sim_amount = st.number_input("Transaction Amount (Rs)", min_value=1.0, max_value=100000.0, value=1500.0, step=50.0, key="sim_amount_input")
        sim_bank = st.selectbox("Failed Issuing Bank", ["HDFC", "SBI", "ICICI", "Axis"], key="sim_bank_selectbox")
        
        sim_category = st.selectbox(
            "Failure Category",
            ["TECHNICAL_TRANSIENT", "USER_DROPOFF", "USER_BALANCE", "AUTHENTICATION_HARD"],
            key="sim_category_selectbox"
        )
        
        reasons_by_category = {
            "TECHNICAL_TRANSIENT": ["BANK_SYSTEM_TIMEOUT", "GATEWAY_DOWNTIME", "NETWORK_LATENCY_EXCEEDED"],
            "USER_DROPOFF": ["CUSTOMER_CLOSED_CHECKOUT", "OTP_PAGE_ABANDONED", "CHOSE_TO_CANCEL"],
            "USER_BALANCE": ["INSUFFICIENT_FUNDS", "ACCOUNT_LIMIT_EXCEEDED"],
            "AUTHENTICATION_HARD": ["INCORRECT_OTP", "CARD_EXPIRED", "CARD_BLOCKED_BY_ISSUER", "INVALID_PIN"]
        }
        
        sim_reason = st.selectbox("Failure Reason", reasons_by_category[sim_category], key="sim_reason_selectbox")
        
        if st.button("⚡ Trigger Webhook Recovery Simulation", key="trigger_simulation_btn"):
            sim_tx = {
                "transaction_id": f"pay_sim_{int(datetime.now().timestamp())}",
                "customer_name": customer_name,
                "customer_phone": "+919876543210",
                "customer_email": f"{customer_name.lower().replace(' ', '.')}@example.com",
                "customer_tier": sim_tier,
                "customer_ltv": sim_ltv,
                "amount": sim_amount,
                "bank": sim_bank,
                "failure_category": sim_category,
                "failure_reason": sim_reason,
                "timestamp": datetime.now().isoformat()
            }
            
            agent = SmartDunningAgent(min_amount_threshold=20.0, max_retries=3)
            sim_result = agent.process_transaction(sim_tx, use_fallback=True)
            
            st.session_state["simulation_result"] = sim_result
            st.success("Simulation complete! Check the sandbox preview column on the right.")
            
    with col_right:
        st.markdown("#### 📱 Live Interactive Dunning Communications Preview")
        
        c_lang, c_chan = st.columns(2)
        with c_lang:
            preview_lang = st.radio("Message Language Mode", ["Natural Hinglish", "English"], horizontal=True, key="preview_lang_radio")
        with c_chan:
            preview_channel = st.radio("Delivery Rail Channel", ["WhatsApp Business", "SMS Text"], horizontal=True, key="preview_channel_radio")
            
        if "simulation_result" in st.session_state:
            sim_res = st.session_state["simulation_result"]
            
            active_attempt = None
            for step in sim_res["history"]:
                if step["action"] not in ["SKIP", "SUPPRESS"]:
                    active_attempt = step
                    break
            
            # Dynamic Retry Window Info Box
            st.markdown(f"""
            <div style="background-color: #1E293B; border-radius: 8px; padding: 12px; border-left: 4px solid #6366F1; margin-bottom: 12px;">
                <div style="font-size: 11px; color: #94A3B8; font-weight: 600; text-transform: uppercase;">⏱️ Dynamic Retry Window Recommendation</div>
                <div style="font-size: 15px; font-weight: 700; color: #F8FAFC; margin: 2px 0;">{sim_res.get('optimal_retry_window', 'Immediate Intent')}</div>
                <div style="font-size: 12px; color: #38BDF8;">Schedule: {sim_res.get('scheduled_time', 'Instant')} | {sim_res.get('window_reasoning', '')}</div>
            </div>
            """, unsafe_allow_html=True)

            if sim_res["status"] == "SKIPPED":
                st.warning(f"⏩ **Dunning Bypass Triggered**\n\nReason: Amount Rs {sim_res['amount']:.2f} is below the unit-economic Rs 20.00 guardrail threshold. No notifications dispatched.")
            elif sim_res["status"] == "SUPPRESSED":
                st.info("🔕 **Dunning Suppression Triggered**\n\nReason: Card authorization, PIN, or OTP hard errors suppress recovery attempts entirely. No notifications dispatched.")
            elif active_attempt:
                msg_text = active_attempt["message_hinglish"] if preview_lang == "Natural Hinglish" else active_attempt["message_english"]
                
                bubble_bg = "#056162" if preview_channel == "WhatsApp Business" else "#007AFF"
                text_color = "#FFFFFF"
                header_text = f"💬 WhatsApp Business • {sim_res.get('customer_tier', 'REGULAR')}" if preview_channel == "WhatsApp Business" else f"💬 SMS Alert • {sim_res.get('customer_tier', 'REGULAR')}"
                
                st.markdown(f"""
                <div style="max-width: 450px; margin: 15px auto; background-color: #111B21; border-radius: 12px; border: 1px solid #202C33; padding: 14px; box-shadow: 0 4px 15px rgba(0,0,0,0.5);">
                    <div style="font-size: 11px; color: #8696A0; margin-bottom: 8px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">{header_text}</div>
                    <div style="background-color: {bubble_bg}; border-radius: 8px; padding: 12px; position: relative;">
                        <p style="color: {text_color}; margin: 0; font-size: 14px; line-height: 1.5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
                            {msg_text}
                        </p>
                        <span style="font-size: 9px; color: rgba(255,255,255,0.7); float: right; margin-top: 4px;">Just Now</span>
                        <div style="clear: both;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if active_attempt.get("rerouted"):
                    st.info(f"🔄 **Intelligent Routing Active:** Switched from degraded **{sim_res['bank']}** to **{active_attempt['fallback_bank']}** fallback rail (UPI handle **{active_attempt['fallback_handle']}**).")
                else:
                    st.success(f"🟢 **Direct Routing Active:** Processing payment recovery via standard **{sim_res['bank']}** rails.")
            
            st.markdown("##### ⚙️ Webhook Sandbox Execution Trace Logs")
            st.markdown(f"**Transaction ID:** `{sim_res['transaction_id']}` | **Final Status:** `{sim_res['status']}` | **Total Cost:** ₹{sim_res['total_cost']:.2f}")
            
            for step in sim_res["history"]:
                success_icon = "✅ SUCCESS" if step.get("success") else "❌ FAILED"
                if step["action"] == "SKIP":
                    st.warning(f"⏩ **[Guardrail Skip]** {step.get('reason')}")
                elif step["action"] == "SUPPRESS":
                    st.info(f"🔕 **[Suppression Active]** {step.get('reason')}")
                else:
                    st.markdown(f"""
                    * **Attempt {step['attempt']}:** `{step['action']}` | Cost: ₹{step['cost']:.2f} | Prob: {step.get('probability', 0)*100:.1f}% | **{success_icon}**
                    """)
        else:
            st.info("💡 Run a simulation using the form on the left to see the message preview bubble and execution logs here.")

# ==============================================================================
# TAB 3: ENTERPRISE ROI & UNIT ECONOMICS CALCULATOR
# ==============================================================================
with tab3:
    st.markdown("### 📈 Enterprise Merchant ROI & Unit Economics Calculator")
    st.markdown("Model dynamic revenue recovery, messaging overhead, and annual bottom-line EBITDA lift tailored to your business scale.")

    calc_c1, calc_c2 = st.columns([1, 2])

    with calc_c1:
        st.markdown("#### ⚙️ Merchant Processing Parameters")
        monthly_gmv_lakhs = st.slider("Monthly Processed GMV (₹ Lakhs)", min_value=5.0, max_value=1000.0, value=100.0, step=5.0, help="Total transaction volume processed per month")
        monthly_gmv = monthly_gmv_lakhs * 100_000.0
        
        avg_ticket = st.number_input("Average Order Value / Ticket Size (₹)", min_value=100.0, max_value=50000.0, value=1850.0, step=50.0)
        failure_rate_pct = st.slider("Payment Failure Rate (%)", min_value=3.0, max_value=30.0, value=12.0, step=0.5)
        failure_rate = failure_rate_pct / 100.0
        
        merchant_margin_pct = st.slider("Merchant Net Operating Margin (%)", min_value=5.0, max_value=70.0, value=25.0, step=1.0)
        merchant_margin = merchant_margin_pct / 100.0

        st.markdown("---")
        st.markdown("#### 🎯 SmartDunning Efficiency Defaults")
        recovery_efficiency_pct = st.slider("SmartDunning Recovery Rate (%)", min_value=40.0, max_value=90.0, value=72.0, step=1.0)
        recovery_efficiency = recovery_efficiency_pct / 100.0

    # Model Computations
    monthly_txns = monthly_gmv / avg_ticket
    monthly_failed_txns = monthly_txns * failure_rate
    monthly_failed_gmv = monthly_gmv * failure_rate
    annual_failed_gmv = monthly_failed_gmv * 12.0

    monthly_recovered_gmv = monthly_failed_gmv * recovery_efficiency
    annual_recovered_gmv = monthly_recovered_gmv * 12.0

    # Messaging overhead: ~1.2 notifications per eligible recovery @ avg ₹1.10
    monthly_cost = monthly_failed_txns * 0.85 * 1.2 * 1.10
    annual_cost = monthly_cost * 12.0

    annual_net_gmv_saved = annual_recovered_gmv - annual_cost
    annual_profit_lift = (annual_recovered_gmv * merchant_margin) - annual_cost
    roi_multiplier = (annual_recovered_gmv / annual_cost) if annual_cost > 0 else 0

    with calc_c2:
        st.markdown("#### 💰 Projected Annual Financial Impact")
        
        rc1, rc2, rc3 = st.columns(3)
        with rc1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Annual Recovered GMV</div>
                <div class="metric-value" style="color: #10B981;">₹{annual_recovered_gmv/10000000:,.2f} Cr</div>
                <div class="metric-sub">Monthly: ₹{monthly_recovered_gmv/100000:,.1f} Lakhs</div>
            </div>
            """, unsafe_allow_html=True)
            
        with rc2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Net Annual Profit Lift</div>
                <div class="metric-value" style="color: #6366F1;">₹{annual_profit_lift/100000:,.2f} L</div>
                <div class="metric-sub">EBITDA Margin: {merchant_margin_pct}%</div>
            </div>
            """, unsafe_allow_html=True)
            
        with rc3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Unit Economic ROI</div>
                <div class="metric-value">{roi_multiplier:,.0f}x</div>
                <div class="metric-sub">Annual Cost: ₹{annual_cost/1000:,.1f}k</div>
            </div>
            """, unsafe_allow_html=True)

        st.write("")

        # 1. 12-Month Cumulative Profit Projection Curve
        months = [f"Month {i}" for i in range(1, 13)]
        cum_status_quo = [0.0] * 12
        cum_recovered_gmv = [(monthly_recovered_gmv * i) / 100000.0 for i in range(1, 13)]
        cum_net_profit = [( (monthly_recovered_gmv * merchant_margin - monthly_cost) * i ) / 100000.0 for i in range(1, 13)]

        fig_proj = go.Figure()
        fig_proj.add_trace(go.Scatter(
            x=months, y=cum_recovered_gmv,
            mode='lines+markers', name='Cumulative Recovered GMV (₹ Lakhs)',
            line=dict(color='#10B981', width=3)
        ))
        fig_proj.add_trace(go.Scatter(
            x=months, y=cum_net_profit,
            mode='lines+markers', name='Cumulative Merchant Profit Lift (₹ Lakhs)',
            line=dict(color='#6366F1', width=3, dash='dash')
        ))
        fig_proj.add_trace(go.Scatter(
            x=months, y=cum_status_quo,
            mode='lines', name='Baseline Status Quo (₹0)',
            line=dict(color='#F43F5E', width=2)
        ))
        fig_proj.update_layout(
            title='12-Month Cumulative Revenue & Profit Trajectory',
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title='Timeline',
            yaxis_title='Amount (₹ Lakhs)',
            height=320
        )
        st.plotly_chart(fig_proj, use_container_width=True)

    # Secondary Charts Row
    st.write("---")
    sc1, sc2 = st.columns(2)

    with sc1:
        # Sensitivity Analysis
        rates = [5, 10, 15, 20, 25]
        sensitivity_data = []
        for r in rates:
            rec_gmv = (monthly_gmv * (r/100.0) * recovery_efficiency * 12) / 100000.0
            profit = (rec_gmv * 100000.0 * merchant_margin - (monthly_gmv * (r/100.0) / avg_ticket * 0.85 * 1.2 * 1.10 * 12)) / 100000.0
            sensitivity_data.append({
                "Failure Rate (%)": f"{r}% Failures",
                "Recovered GMV (₹ Lakhs)": rec_gmv,
                "Net Profit Lift (₹ Lakhs)": profit
            })
        sens_df = pd.DataFrame(sensitivity_data)
        fig_sens = px.bar(
            sens_df,
            x="Failure Rate (%)",
            y=["Recovered GMV (₹ Lakhs)", "Net Profit Lift (₹ Lakhs)"],
            barmode="group",
            title="Sensitivity Analysis Across Failure Rates",
            color_discrete_sequence=["#10B981", "#6366F1"]
        )
        fig_sens.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_sens, use_container_width=True)

    with sc2:
        # Unit Economics Waterfall
        waterfall_df = pd.DataFrame([
            {"Component": "Total Failed GMV", "Amount (₹ L)": annual_failed_gmv / 100000.0},
            {"Component": "Unrecoverable Churn", "Amount (₹ L)": -(annual_failed_gmv - annual_recovered_gmv) / 100000.0},
            {"Component": "Gross Recovered GMV", "Amount (₹ L)": annual_recovered_gmv / 100000.0},
            {"Component": "Dunning Overhead", "Amount (₹ L)": -annual_cost / 100000.0},
            {"Component": "Net Retained GMV", "Amount (₹ L)": annual_net_gmv_saved / 100000.0}
        ])
        fig_waterfall = go.Figure(go.Waterfall(
            name="Unit Economics",
            orientation="v",
            measure=["relative", "relative", "total", "relative", "total"],
            x=waterfall_df["Component"],
            textposition="outside",
            text=[f"₹{abs(v):,.1f}L" for v in waterfall_df["Amount (₹ L)"]],
            y=waterfall_df["Amount (₹ L)"],
            connector={"line": {"color": "#6366F1"}},
            decreasing={"marker": {"color": "#EF4444"}},
            increasing={"marker": {"color": "#10B981"}},
            totals={"marker": {"color": "#38BDF8"}}
        ))
        fig_waterfall.update_layout(
            title="Annual Dunning Unit Economics Waterfall",
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_waterfall, use_container_width=True)
