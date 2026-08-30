import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime

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
""", unsafe_style_html=True)

# App Title & Header
st.title("⚡ SmartDunning AI Recovery Dashboard")
st.markdown("##### Real-time payment recovery, root-cause triage, and unit-economic analytics for Razorpay merchants.")

# Check for data files
results_path = "data/dunning_results.json"
failed_payments_path = "data/failed_payments.json"

if not os.path.exists(results_path):
    st.info("📊 Results data not found. Running the evaluation agent simulation to generate outcomes...")
    # Dynamically trigger data generation and evaluation if files are missing
    if not os.path.exists(failed_payments_path):
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

# ----------------- CALCULATE METRICS -----------------
total_at_risk = filtered_df['amount'].sum()
recovered_df = filtered_df[filtered_df['status'] == 'RECOVERED']
failed_df = filtered_df[filtered_df['status'] == 'FAILED']
skipped_df = filtered_df[filtered_df['status'] == 'SKIPPED']

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
    """, unsafe_style_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Gross Recovery Savings</div>
        <div class="metric-value">₹{gross_savings:,.2f}</div>
        <div class="metric-sub">{len(recovered_df)} txs recovered</div>
    </div>
    """, unsafe_style_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Notification Costs</div>
        <div class="metric-value">₹{total_costs:,.2f}</div>
        <div class="metric-sub" style="color: #F43F5E;">Guardrails saved ₹{len(skipped_df)*1.50:.1f}+</div>
    </div>
    """, unsafe_style_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Net Profit Saved</div>
        <div class="metric-value" style="color: #10B981;">₹{net_profit_saved:,.2f}</div>
        <div class="metric-sub">ROI: {((gross_savings/total_costs)*100 if total_costs > 0 else 0):,.1f}%</div>
    </div>
    """, unsafe_style_html=True)

with col5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Recovery Rate</div>
        <div class="metric-value">{recovery_rate_pct:.1f}%</div>
        <div class="metric-sub" style="color: #6366F1;">Value Recov: {value_recovery_pct:.1f}%</div>
    </div>
    """, unsafe_style_html=True)

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
display_cols = ['transaction_id', 'customer_name', 'amount', 'failure_category', 'failure_reason', 'attempts_made', 'total_cost', 'status', 'timestamp']
table_df = filtered_df[display_cols].copy()
table_df.columns = ['TxID', 'Customer', 'Amount (₹)', 'Failure Category', 'Failure Reason', 'Retries', 'Dunning Cost (₹)', 'Status', 'Timestamp']

# Style the status column
def highlight_status(val):
    if val == "RECOVERED":
        return 'color: #10B981; font-weight: bold;'
    elif val == "FAILED":
        return 'color: #F43F5E; font-weight: bold;'
    elif val == "SKIPPED":
        return 'color: #94A3B8; font-weight: normal; font-style: italic;'
    return ''

styled_table = table_df.style.map(highlight_status, subset=['Status']).format({'Amount (₹)': '₹{:.2f}', 'Dunning Cost (₹)': '₹{:.2f}'})

st.dataframe(styled_table, use_container_width=True, height=400)

# Detail Audit Trail lookup
st.markdown("#### 🔍 Deep-Dive Transaction Audit Trail")
selected_tx_id = st.selectbox(
    "Select a transaction to inspect its complete retry dunning history:",
    options=filtered_df['transaction_id'].tolist(),
    format_func=lambda x: f"{x} - {filtered_df[filtered_df['transaction_id'] == x]['customer_name'].values[0]} (₹{filtered_df[filtered_df['transaction_id'] == x]['amount'].values[0]:.2f})"
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
        # Format the retry details nicely
        success_icon = "✅ Success" if step.get("success") else "❌ Failed"
        if step["action"] == "SKIP":
            st.warning(f"⏩ **Guardrail Skip Action** — Reason: {step.get('reason')}")
        else:
            st.info(
                f"🔄 **Attempt {step['attempt']}**: Action `{step['action']}` | "
                f"Cost: ₹{step['cost']:.2f} | "
                f"Success Probability: {step.get('probability', 0)*100:.1f}% | "
                f"Result: **{success_icon}**"
            )
