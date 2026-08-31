import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime
from agent import SmartDunningAgent, BankTelemetry

# Set page config for wide layout and premium design feel
st.set_page_config(
    page_title="SmartDunning AI - Analytics Dashboard",
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
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .metric-value {
        color: #F8FAFC;
        font-size: 28px;
        font-weight: 700;
    }
    .metric-sub {
        color: #10B981;
        font-size: 12px;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# App Title & Header
st.title("⚡ SmartDunning AI Recovery Dashboard")
st.markdown("##### Real-time payment recovery, root-cause triage, and unit-economic analytics for Razorpay merchants.")

# Check for data files or if results are outdated (missing bank field)
results_path = "data/dunning_results.json"
failed_payments_path = "data/failed_payments.json"

outdated = False
if os.path.exists(results_path):
    try:
        with open(results_path, "r") as f:
            test_data = json.load(f)
        if len(test_data) > 0 and "bank" not in test_data[0]:
            outdated = True
    except Exception:
        outdated = True

if not os.path.exists(results_path) or outdated:
    st.info("📊 Results data not found or outdated. Running the evaluation agent simulation to generate outcomes...")
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

# Filter: Status
statuses = ["All"] + list(df['status'].unique())
selected_status = st.sidebar.selectbox("Recovery Status", statuses)

# Filter: Value Slider
min_amt = float(df['amount'].min())
max_amt = float(df['amount'].max())
amount_range = st.sidebar.slider("Transaction Amount (Rs)", min_amt, max_amt, (min_amt, max_amt))

# Search box
search_query = st.sidebar.text_input("🔍 Search Customer, Phone or TxID")

# Apply Filters
filtered_df = df.copy()

if selected_category != "All":
    filtered_df = filtered_df[filtered_df['failure_category'] == selected_category]

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
        filtered_df['transaction_id'].str.contains(search_query, case=False)
    ]

# ----------------- TABS SYSTEM -----------------
tab1, tab2 = st.tabs(["📊 Batch Revenue Recovery Benchmark", "⚡ Live Rail Telemetry & Webhook Sandbox"])

with tab1:
    # ----------------- CALCULATE METRICS -----------------
    total_at_risk = filtered_df['amount'].sum()
    recovered_df = filtered_df[filtered_df['status'] == 'RECOVERED']
    failed_df = filtered_df[filtered_df['status'] == 'FAILED']
    skipped_df = filtered_df[filtered_df['status'] == 'SKIPPED']
    suppressed_df = filtered_df[filtered_df['status'] == 'SUPPRESSED'] if 'status' in filtered_df.columns and 'SUPPRESSED' in filtered_df['status'].values else pd.DataFrame()

    gross_savings = recovered_df['amount'].sum()
    total_costs = filtered_df['total_cost'].sum()
    net_profit_saved = gross_savings - total_costs

    recovery_rate_pct = (len(recovered_df) / len(filtered_df) * 100) if len(filtered_df) > 0 else 0.0
    value_recovery_pct = (gross_savings / total_at_risk * 100) if total_at_risk > 0 else 0.0

    # ----------------- RENDER METRICS CARDS -----------------
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Volume at Risk</div>
            <div class="metric-value">₹{total_at_risk:,.2f}</div>
            <div class="metric-sub" style="color: #94A3B8;">{len(filtered_df)} failed txs</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Gross Recovery Savings</div>
            <div class="metric-value">₹{gross_savings:,.2f}</div>
            <div class="metric-sub">{len(recovered_df)} txs recovered</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Notification Costs</div>
            <div class="metric-value">₹{total_costs:,.2f}</div>
            <div class="metric-sub" style="color: #F43F5E;">Guardrails saved ₹{(len(skipped_df) + len(suppressed_df))*1.50:.1f}+</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Net Profit Saved</div>
            <div class="metric-value" style="color: #10B981;">₹{net_profit_saved:,.2f}</div>
            <div class="metric-sub">ROI: {((gross_savings/total_costs)*100 if total_costs > 0 else 0):,.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Recovery Rate</div>
            <div class="metric-value">{recovery_rate_pct:.1f}%</div>
            <div class="metric-sub" style="color: #6366F1;">Value Recov: {value_recovery_pct:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # ----------------- ANALYTICS CHARTS SECTION -----------------
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        # 1. Failure Categories Breakdown Pie Chart
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
        # 2. Recovery Success Rate by Category
        cat_recovery = filtered_df.groupby('failure_category').apply(
            lambda x: (x['status'] == 'RECOVERED').sum() / len(x) * 100 if len(x) > 0 else 0
        ).reset_index()
        cat_recovery.columns = ['Category', 'Recovery Rate (%)']
        fig_bar = px.bar(
            cat_recovery, 
            x='Category', 
            y='Recovery Rate (%)', 
            title='Recovery Success Rate by Failure Category (%)',
            color='Category',
            color_discrete_sequence=px.colors.qualitative.G10
        )
        fig_bar.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        # 3. Cumulative Savings & Costs Timeline
        df_timeline = filtered_df.copy()
        df_timeline['cumulative_recovered'] = df_timeline.apply(
            lambda row: row['amount'] if row['status'] == 'RECOVERED' else 0.0, axis=1
        ).cumsum()
        df_timeline['cumulative_cost'] = df_timeline['total_cost'].cumsum()
        df_timeline['cumulative_net_saved'] = df_timeline['cumulative_recovered'] - df_timeline['cumulative_cost']
        
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(x=df_timeline['timestamp'], y=df_timeline['cumulative_recovered'], mode='lines', name='Gross Savings (₹)', line=dict(color='#10B981', width=3)))
        fig_line.add_trace(go.Scatter(x=df_timeline['timestamp'], y=df_timeline['cumulative_net_saved'], mode='lines', name='Net Savings (₹)', line=dict(color='#6366F1', width=3, dash='dash')))
        fig_line.add_trace(go.Scatter(x=df_timeline['timestamp'], y=df_timeline['cumulative_cost'], mode='lines', name='Notification Costs (₹)', line=dict(color='#F43F5E', width=2)))
        
        fig_line.update_layout(
            title='Cumulative Dunning Impact Timeline',
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title='Date & Time',
            yaxis_title='Amount (₹)'
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with chart_col4:
        # 4. Action / Cost effectiveness breakdown
        actions_performed = []
        for hist in filtered_df['history']:
            for attempt in hist:
                actions_performed.append({
                    "action": attempt["action"],
                    "cost": attempt["cost"],
                    "success": attempt["success"]
                })
                
        if actions_performed:
            df_actions = pd.DataFrame(actions_performed)
            df_action_summary = df_actions.groupby('action').agg(
                Volume=('cost', 'count'),
                Total_Cost=('cost', 'sum'),
                Recovered_Count=('success', 'sum')
            ).reset_index()
            
            # Calculate success percentage per action
            df_action_summary['Success Rate (%)'] = (df_action_summary['Recovered_Count'] / df_action_summary['Volume']) * 100
            
            fig_actions = go.Figure(data=[
                go.Bar(name='Execution Volume', x=df_action_summary['action'], y=df_action_summary['Volume'], yaxis='y', offsetgroup=1, marker_color='#6366F1'),
                go.Bar(name='Success Rate (%)', x=df_action_summary['action'], y=df_action_summary['Success Rate (%)'], yaxis='y2', offsetgroup=2, marker_color='#10B981')
            ])
            
            fig_actions.update_layout(
                title='Recovery Action Distribution & Success Rate',
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(title='Execution Volume (count)'),
                yaxis2=dict(title='Success Rate (%)', overlaying='y', side='right'),
                legend=dict(x=0.01, y=0.99)
            )
            st.plotly_chart(fig_actions, use_container_width=True)
        else:
            st.info("No actions recorded to visualize efficiency.")

    # ----------------- AUDIT LEDGER SECTION -----------------
    st.write("---")
    st.markdown("### 📒 SmartDunning Audit Ledger")
    st.markdown("Explore detailed transactions, triage outcomes, and retry logs.")

    # Display DataFrame
    display_cols = ['transaction_id', 'customer_name', 'amount', 'bank', 'failure_category', 'failure_reason', 'attempts_made', 'total_cost', 'status', 'timestamp']
    table_df = filtered_df[display_cols].copy()
    table_df.columns = ['TxID', 'Customer', 'Amount (₹)', 'Bank', 'Failure Category', 'Failure Reason', 'Retries', 'Dunning Cost (₹)', 'Status', 'Timestamp']

    # Style the status column
    def highlight_status(val):
        if val == "RECOVERED":
            return 'color: #10B981; font-weight: bold;'
        elif val == "FAILED":
            return 'color: #F43F5E; font-weight: bold;'
        elif val == "SKIPPED":
            return 'color: #94A3B8; font-weight: normal; font-style: italic;'
        elif val == "SUPPRESSED":
            return 'color: #D97706; font-weight: normal; font-style: italic;'
        return ''

    styled_table = table_df.style.map(highlight_status, subset=['Status']).format({'Amount (₹)': '₹{:.2f}', 'Dunning Cost (₹)': '₹{:.2f}'})

    st.dataframe(styled_table, use_container_width=True, height=400)

    # Detail Audit Trail lookup
    st.markdown("#### 🔍 Deep-Dive Transaction Audit Trail")
    selected_tx_id = st.selectbox(
        "Select a transaction to inspect its complete retry dunning history:",
        options=filtered_df['transaction_id'].tolist(),
        format_func=lambda x: f"{x} - {filtered_df[filtered_df['transaction_id'] == x]['customer_name'].values[0]} (₹{filtered_df[filtered_df['transaction_id'] == x]['amount'].values[0]:.2f})",
        key="tx_audit_lookup"
    )

    if selected_tx_id:
        tx_detail = filtered_df[filtered_df['transaction_id'] == selected_tx_id].iloc[0]
        
        col_det1, col_det2, col_det3 = st.columns(3)
        with col_det1:
            st.markdown(f"**Customer:** {tx_detail['customer_name']}")
            st.markdown(f"**Contact:** {tx_detail['customer_phone']} | {tx_detail['customer_email']}")
        with col_det2:
            st.markdown(f"**Amount:** ₹{tx_detail['amount']:.2f}")
            st.markdown(f"**Failure Category:** `{tx_detail['failure_category']}`")
        with col_det3:
            st.markdown(f"**Root Cause Reason:** `{tx_detail['failure_reason']}`")
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

with tab2:
    st.markdown("### ⚡ Live Payment Rail Telemetry & Webhook Sandbox")
    st.markdown("Monitor issuing bank health in real-time, test custom transaction webhook recovery scenarios, and preview automated communications.")

    # Instantiate telemetry for UI display
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
            "Select Customer to Simulate",
            ["Rahul Sharma", "Aarav Gupta", "Diya Patel", "Kiara Sen", "Custom..."],
            key="sim_name_selectbox"
        )
        if sim_name == "Custom...":
            customer_name = st.text_input("Enter Custom Name", "Raj Malhotra", key="custom_name_input")
        else:
            customer_name = sim_name
            
        customer_phone = st.text_input("Customer Phone", "+919876543210", key="cust_phone_input")
        customer_email = st.text_input("Customer Email", f"{customer_name.lower().replace(' ', '.')}@example.com", key="cust_email_input")
        
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
            # Create transaction dict
            sim_tx = {
                "transaction_id": f"pay_sim_{int(datetime.now().timestamp())}",
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "customer_email": customer_email,
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
        
        # Message customization and preview toggle
        c_lang, c_chan = st.columns(2)
        with c_lang:
            preview_lang = st.radio("Message Language Mode", ["Natural Hinglish", "English"], horizontal=True, key="preview_lang_radio")
        with c_chan:
            preview_channel = st.radio("Delivery Rail Channel", ["WhatsApp Business", "SMS Text"], horizontal=True, key="preview_channel_radio")
            
        if "simulation_result" in st.session_state:
            sim_res = st.session_state["simulation_result"]
            
            # Find if there was any retry notification sent
            active_attempt = None
            for step in sim_res["history"]:
                if step["action"] not in ["SKIP", "SUPPRESS"]:
                    active_attempt = step
                    break
            
            # If dunning skipped or suppressed, explain and don't render chat bubble
            if sim_res["status"] == "SKIPPED":
                st.warning(f"⏩ **Dunning Bypass Triggered**\n\nReason: Amount Rs {sim_res['amount']:.2f} is below the unit-economic Rs 20.00 guardrail threshold. No notifications dispatched.")
            elif sim_res["status"] == "SUPPRESSED":
                st.info("🔕 **Dunning Suppression Triggered**\n\nReason: Card authorization, PIN, or OTP hard errors suppress recovery attempts entirely. No notifications dispatched.")
            elif active_attempt:
                # Render message bubble
                msg_text = active_attempt["message_hinglish"] if preview_lang == "Natural Hinglish" else active_attempt["message_english"]
                
                # Format WhatsApp vs SMS bubble
                bubble_bg = "#056162" if preview_channel == "WhatsApp Business" else "#007AFF"
                text_color = "#FFFFFF"
                header_text = "💬 WhatsApp Business" if preview_channel == "WhatsApp Business" else "💬 SMS Alert"
                
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
                
                # Show dynamic fallback routing details
                if active_attempt.get("rerouted"):
                    st.info(f"🔄 **Intelligent Routing Active:** Switched from degraded **{sim_res['bank']}** to **{active_attempt['fallback_bank']}** fallback payment rail (UPI handle **{active_attempt['fallback_handle']}**).")
                else:
                    st.success(f"🟢 **Direct Routing Active:** Processing payment recovery via standard **{sim_res['bank']}** rails.")
            
            # Print execution trace
            st.markdown("##### ⚙️ Webhook Sandbox Execution Trace Logs")
            
            st.markdown(f"**Transaction ID:** `{sim_res['transaction_id']}`")
            st.markdown(f"**Final Simulation Status:** `{sim_res['status']}`")
            st.markdown(f"**Total Recovery Cost:** ₹{sim_res['total_cost']:.2f}")
            st.markdown(f"**Attempts Executed:** {sim_res['attempts_made']}")
            
            for step in sim_res["history"]:
                success_icon = "✅ SUCCESS" if step.get("success") else "❌ FAILED"
                if step["action"] == "SKIP":
                    st.warning(f"⏩ **[Guardrail Skip]** {step.get('reason')}")
                elif step["action"] == "SUPPRESS":
                    st.info(f"🔕 **[Suppression Active]** {step.get('reason')}")
                else:
                    st.markdown(f"""
                    * **Attempt {step['attempt']}:**
                      * Action taken: `{step['action']}`
                      * Cost incurred: ₹{step['cost']:.2f}
                      * Recovery success probability: {step.get('probability', 0)*100:.1f}%
                      * Simulation result: **{success_icon}**
                    """)
        else:
            st.info("💡 Run a simulation using the form on the left to see the message preview bubble and execution logs here.")
