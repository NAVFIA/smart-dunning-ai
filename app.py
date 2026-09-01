import streamlit as st
import json
import os
import re
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from agent import SmartDunningAgent, BankTelemetry, RetryWindowOptimizer, parse_natural_language_policy, DEFAULT_POLICY

# ==============================================================================
# PAGE CONFIGURATION & METADATA
# ==============================================================================
st.set_page_config(
    page_title="SmartDunning AI | RazorpayX Autonomous Recovery Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# RAZORPAYX DARK FINTECH DESIGN SYSTEM (CSS)
# ==============================================================================
st.markdown("""
<style>
    /* Google Fonts Import */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');

    /* Global Dark Fintech Theme */
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #0B0F19 !important;
        color: #F8FAFC !important;
    }
    
    /* Sleek Background Canvas */
    .stApp {
        background: radial-gradient(circle at 15% 15%, rgba(51, 149, 255, 0.07) 0%, transparent 45%),
                    radial-gradient(circle at 85% 85%, rgba(16, 185, 129, 0.05) 0%, transparent 45%),
                    #0B0F19 !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0E1322 !important;
        border-right: 1px solid rgba(51, 149, 255, 0.15) !important;
    }

    /* Header Brand Banner */
    .brand-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 24px;
        background: linear-gradient(135deg, rgba(17, 24, 39, 0.85) 0%, rgba(15, 23, 42, 0.85) 100%);
        border: 1px solid rgba(51, 149, 255, 0.2);
        border-radius: 16px;
        backdrop-filter: blur(16px);
        margin-bottom: 24px;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
    }
    .brand-badge {
        background: linear-gradient(135deg, #3395FF 0%, #0052FF 100%);
        color: #FFFFFF;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        box-shadow: 0 0 15px rgba(51, 149, 255, 0.5);
    }

    /* Glassmorphic Metric Cards */
    .metric-card {
        background: rgba(17, 24, 39, 0.75);
        border-radius: 14px;
        padding: 20px 18px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(12px);
        box-shadow: 0 8px 24px -6px rgba(0, 0, 0, 0.4);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        border-color: rgba(51, 149, 255, 0.4);
        box-shadow: 0 12px 28px -6px rgba(51, 149, 255, 0.25);
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, #3395FF, transparent);
        opacity: 0;
        transition: opacity 0.3s;
    }
    .metric-card:hover::before {
        opacity: 1;
    }
    .metric-title {
        color: #94A3B8;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 26px;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: -0.5px;
    }
    .metric-sub {
        font-size: 12px;
        margin-top: 6px;
        font-weight: 600;
    }

    /* Status Glowing Badges */
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.3px;
        text-transform: uppercase;
    }
    .status-recovered {
        background: rgba(16, 185, 129, 0.15);
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.4);
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.2);
    }
    .status-settled {
        background: rgba(51, 149, 255, 0.18);
        color: #38BDF8;
        border: 1px solid rgba(56, 189, 248, 0.4);
        box-shadow: 0 0 12px rgba(56, 189, 248, 0.3);
    }
    .status-failed {
        background: rgba(244, 63, 94, 0.15);
        color: #F43F5E;
        border: 1px solid rgba(244, 63, 94, 0.4);
    }
    .status-halted {
        background: rgba(245, 158, 11, 0.15);
        color: #F59E0B;
        border: 1px solid rgba(245, 158, 11, 0.4);
    }

    /* Copilot Synthesis Box */
    .copilot-box {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(51, 149, 255, 0.3);
        border-radius: 16px;
        padding: 20px;
        backdrop-filter: blur(16px);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    }
    .copilot-chip {
        display: inline-block;
        background: rgba(51, 149, 255, 0.15);
        color: #38BDF8;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 600;
        margin: 4px;
        border: 1px solid rgba(51, 149, 255, 0.3);
    }

    /* Custom 1-Tap Settlement Drawer */
    .settlement-drawer {
        background: linear-gradient(145deg, #111827 0%, #0F172A 100%);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 14px;
        padding: 18px;
        margin-top: 15px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
    }

    /* Streamlit Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(17, 24, 39, 0.6);
        padding: 8px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #94A3B8;
        font-weight: 600;
        padding: 10px 18px;
        transition: all 0.2s;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(51, 149, 255, 0.2) 0%, rgba(0, 82, 255, 0.3) 100%) !important;
        color: #38BDF8 !important;
        border: 1px solid rgba(51, 149, 255, 0.4) !important;
    }

    /* Code Blocks */
    pre, code {
        font-family: 'JetBrains Mono', monospace !important;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# DATA INGESTION & GLOBAL INITIALIZATION
# ==============================================================================
RESULTS_PATH = "data/dunning_results.json"
FAILED_PAYMENTS_PATH = "data/failed_payments.json"

def ensure_data_ready():
    """Generates initial dataset and runs benchmark if files are missing."""
    if not os.path.exists(RESULTS_PATH) or not os.path.exists(FAILED_PAYMENTS_PATH):
        os.makedirs("data", exist_ok=True)
        from mock_data import generate_mock_data
        generate_mock_data()
        from eval import run_evaluation
        run_evaluation()

ensure_data_ready()

# Initialize Session State
if "active_policy" not in st.session_state:
    st.session_state["active_policy"] = DEFAULT_POLICY.copy()

if "settled_overrides" not in st.session_state:
    st.session_state["settled_overrides"] = {}

if "copilot_prompt" not in st.session_state:
    st.session_state["copilot_prompt"] = "Give 5% dynamic discount on dropped UPI carts > ₹2000"

# Load transactions
with open(FAILED_PAYMENTS_PATH, "r", encoding="utf-8") as f:
    raw_transactions = json.load(f)

# Re-run simulation dynamically using active policy
agent = SmartDunningAgent(policy=st.session_state["active_policy"])
processed_results = []
for tx in raw_transactions:
    res = agent.process_transaction(tx, use_fallback=True)
    # Check if manually settled via 1-tap simulator
    if tx["transaction_id"] in st.session_state["settled_overrides"]:
        override_info = st.session_state["settled_overrides"][tx["transaction_id"]]
        res["status"] = "SETTLED_1TAP"
        res["settlement_time"] = override_info.get("settlement_time", datetime.now().isoformat())
        res["utr_ref"] = override_info.get("utr_ref", "UPI/2026/89201948")
    processed_results.append(res)

df = pd.DataFrame(processed_results)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values('timestamp')

# ==============================================================================
# HEADER BRAND BANNER
# ==============================================================================
active_p = st.session_state["active_policy"]
has_disc = active_p.get("discount_pct", 0) > 0
has_churn_halt = active_p.get("zero_retry_on_high_churn", False)

disc_pill = f"<span class='copilot-chip'>🏷️ {active_p['discount_pct']:.0f}% Dynamic Discount Active</span>" if has_disc else ""
churn_pill = f"<span class='copilot-chip'>🛡️ Churn Cutoff > {active_p.get('churn_risk_threshold', 0.8):.2f}</span>" if has_churn_halt else ""

st.markdown(f"""
<div class="brand-container">
    <div>
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 4px;">
            <span style="font-size: 24px;">⚡</span>
            <span style="font-size: 22px; font-weight: 800; color: #FFFFFF; letter-spacing: -0.5px;">SmartDunning AI</span>
            <span class="brand-badge">RazorpayX Core Rail</span>
        </div>
        <div style="color: #94A3B8; font-size: 13px;">
            Autonomous Policy Negotiation, Bank Telemetry Multi-Rail Fallback & 1-Tap Mandate Settlement Engine
        </div>
    </div>
    <div style="text-align: right;">
        {disc_pill}
        {churn_pill}
        <span class="status-badge status-recovered">🟢 Telemetry Live</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# SIDEBAR CONTROLS & FILTERING
# ==============================================================================
with st.sidebar:
    st.markdown("### 🎯 RazorpayX Control Center")
    st.markdown("---")
    
    # Category Filter
    categories = ["All"] + sorted(list(df['failure_category'].unique()))
    selected_category = st.selectbox("Failure Category", categories, key="sb_cat")
    
    # Tier Filter
    tiers = ["All"] + sorted(list(df['customer_tier'].unique())) if 'customer_tier' in df.columns else ["All"]
    selected_tier = st.selectbox("Customer LTV Tier", tiers, key="sb_tier")
    
    # Status Filter
    statuses = ["All"] + sorted(list(df['status'].unique()))
    selected_status = st.selectbox("Recovery Status", statuses, key="sb_status")
    
    # Amount Slider
    min_amt = float(df['amount'].min())
    max_amt = float(df['amount'].max())
    amount_range = st.slider("Transaction Amount (₹)", min_amt, max_amt, (min_amt, max_amt), key="sb_amt")
    
    # Search Query
    search_query = st.text_input("🔍 Search Customer, Phone, Bank, TxID", key="sb_search")
    
    st.markdown("---")
    st.markdown("#### ⚡ Active Copilot Status")
    st.markdown(f"**Policy:** `{active_p.get('policy_name', 'Custom')}`")
    st.caption(f"{active_p.get('rule_description', 'Standard')}")
    
    if st.button("🔄 Reset to Default Policy", key="reset_pol_btn"):
        st.session_state["active_policy"] = DEFAULT_POLICY.copy()
        st.session_state["settled_overrides"] = {}
        st.rerun()

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

# ==============================================================================
# TABS SYSTEM (4 TABS)
# ==============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Batch Revenue Recovery Benchmark",
    "⚡ Live Rail Telemetry & 1-Tap Sandbox",
    "📈 Enterprise ROI & Unit Economics",
    "🤖 Autonomous Policy Copilot"
])

# ==============================================================================
# TAB 1: BATCH BENCHMARK & ROOT-CAUSE AUDIT
# ==============================================================================
with tab1:
    total_at_risk = filtered_df['amount'].sum()
    total_ltv_at_risk = filtered_df['customer_ltv'].sum() if 'customer_ltv' in filtered_df.columns else 0.0
    
    recovered_df = filtered_df[filtered_df['status'].isin(['RECOVERED', 'SETTLED_1TAP'])]
    failed_df = filtered_df[filtered_df['status'] == 'FAILED']
    skipped_df = filtered_df[filtered_df['status'] == 'SKIPPED']
    suppressed_df = filtered_df[filtered_df['status'].isin(['SUPPRESSED', 'CHURN_HALTED'])]

    gross_savings = recovered_df['amount'].sum()
    ltv_recovered = recovered_df['customer_ltv'].sum() if 'customer_ltv' in recovered_df.columns else 0.0
    total_costs = filtered_df['total_cost'].sum()
    discounts_given = recovered_df['discount_amount'].sum() if 'discount_amount' in recovered_df.columns else 0.0
    net_profit_saved = (gross_savings - discounts_given) - total_costs

    recovery_rate_pct = (len(recovered_df) / len(filtered_df) * 100) if len(filtered_df) > 0 else 0.0
    value_recovery_pct = (gross_savings / total_at_risk * 100) if total_at_risk > 0 else 0.0
    ltv_recovery_pct = (ltv_recovered / total_ltv_at_risk * 100) if total_ltv_at_risk > 0 else 0.0
    roi_pct = ((gross_savings / total_costs) * 100) if total_costs > 0 else 0.0

    # Top Metric KPI Cards
    kpi_c1, kpi_c2, kpi_c3, kpi_c4, kpi_c5 = st.columns(5)

    with kpi_c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Direct GMV at Risk</div>
            <div class="metric-value">₹{total_at_risk:,.2f}</div>
            <div class="metric-sub" style="color: #94A3B8;">{len(filtered_df)} failed txs</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Direct GMV Recovered</div>
            <div class="metric-value" style="color: #10B981;">₹{gross_savings:,.2f}</div>
            <div class="metric-sub" style="color: #38BDF8;">{len(recovered_df)} txs ({value_recovery_pct:.1f}% value)</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Customer LTV Saved</div>
            <div class="metric-value" style="color: #8B5CF6;">₹{ltv_recovered:,.2f}</div>
            <div class="metric-sub" style="color: #A855F7;">Equity Retained: {ltv_recovery_pct:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Net Profit Saved</div>
            <div class="metric-value" style="color: #10B981;">₹{net_profit_saved:,.2f}</div>
            <div class="metric-sub" style="color: #94A3B8;">Overhead: ₹{total_costs:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_c5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Unit Economic ROI</div>
            <div class="metric-value" style="color: #3395FF;">{roi_pct:,.0f}%</div>
            <div class="metric-sub" style="color: #528FF0;">{(gross_savings/total_costs if total_costs > 0 else 0):,.1f}x Payback Multiplier</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # Root Cause & Dynamic Resolution Sankey Pipeline
    st.markdown("### 🔀 Root-Cause Triage & Dynamic Multi-Rail Resolution Pipeline")
    st.markdown("Visual flow from Ingested Failures through Root-Cause Classification, Autonomous Policy Checks, Interventions, and Settlement Outcomes.")

    if len(filtered_df) > 0:
        node_labels = [
            "Total Ingested Failures",         # 0
            "Technical / Transient",          # 1
            "User Drop-off / Cart Abandon",   # 2
            "Insufficient Balance",           # 3
            "Hard Auth / Mandate Fail",       # 4
            "Dunning Active (Eligible)",       # 5
            "Guardrail: Skipped (< Min)",     # 6
            "Policy: Suppressed / Churn Cut", # 7
            "VIP White-Glove WhatsApp",       # 8
            "1-Tap UPI Intent Fallback",      # 9
            "Intelligent Auto-Retry",         # 10
            "Multi-Rail SMS / Email Link",    # 11
            "✅ Recovered / Settled GMV",      # 12
            "❌ Unrecovered / Halted"          # 13
        ]

        cnt_tech = len(filtered_df[filtered_df['failure_category'] == 'TECHNICAL_TRANSIENT'])
        cnt_drop = len(filtered_df[filtered_df['failure_category'] == 'USER_DROPOFF'])
        cnt_bal = len(filtered_df[filtered_df['failure_category'] == 'USER_BALANCE'])
        cnt_auth = len(filtered_df[filtered_df['failure_category'] == 'AUTHENTICATION_HARD'])

        cnt_skip = len(skipped_df)
        cnt_supp = len(suppressed_df)
        cnt_active = max(0, len(filtered_df) - cnt_skip - cnt_supp)

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
            0, 0, 0, 0,
            1, 2, 3, 4,
            5, 5, 5, 5,
            8, 9, 10, 11,
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
                line=dict(color="#0B0F19", width=0.5),
                label=node_labels,
                color=[
                    "#3395FF",
                    "#38BDF8", "#F59E0B", "#EC4899", "#EF4444",
                    "#10B981", "#94A3B8", "#F43F5E",
                    "#8B5CF6", "#06B6D4", "#F97316", "#A855F7",
                    "#10B981", "#EF4444"
                ]
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color="rgba(51, 149, 255, 0.25)"
            )
        )])
        fig_sankey.update_layout(
            title_text="RazorpayX Autonomous Triage & Multi-Rail Fallback Stream",
            font_size=12,
            font_color="#F8FAFC",
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=400,
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig_sankey, use_container_width=True)

    # Analytics Breakdown Row
    st.write("")
    c_pie, c_tier = st.columns(2)

    with c_pie:
        cat_counts = filtered_df['failure_category'].value_counts().reset_index()
        cat_counts.columns = ['Failure Category', 'Count']
        fig_pie = px.pie(
            cat_counts, 
            values='Count', 
            names='Failure Category', 
            title='Failure Root-Cause Distribution',
            color_discrete_sequence=['#3395FF', '#38BDF8', '#8B5CF6', '#F43F5E'],
            hole=0.45
        )
        fig_pie.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=320,
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with c_tier:
        if 'customer_tier' in filtered_df.columns:
            tier_df = filtered_df.groupby('customer_tier').agg(
                Total=('amount', 'count'),
                Recovered=('status', lambda s: s.isin(['RECOVERED', 'SETTLED_1TAP']).sum()),
                LTV_Saved=('customer_ltv', lambda l: l[filtered_df.loc[l.index, 'status'].isin(['RECOVERED', 'SETTLED_1TAP'])].sum())
            ).reset_index()
            tier_df['Recovery Rate %'] = (tier_df['Recovered'] / tier_df['Total']) * 100
            
            fig_tier = px.bar(
                tier_df,
                x='customer_tier',
                y='Recovery Rate %',
                title='Recovery Rate by Customer LTV Segment (%)',
                color='customer_tier',
                color_discrete_sequence=['#8B5CF6', '#3395FF', '#F59E0B'],
                text_auto='.1f'
            )
            fig_tier.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                showlegend=False,
                height=320,
                margin=dict(l=10, r=10, t=40, b=10)
            )
            st.plotly_chart(fig_tier, use_container_width=True)

    # Audit Ledger Table
    st.write("---")
    st.markdown("### 📒 Enterprise Payment Audit Ledger")
    st.markdown("Real-time transactional audit log with customer LTV scores, bank telemetry, dynamic discount tokens, and 1-tap settlement states.")

    disp_cols = ['transaction_id', 'customer_name', 'customer_tier', 'customer_ltv', 'amount', 'payable_amount', 'discount_pct', 'bank', 'failure_category', 'status']
    avail_cols = [c for c in disp_cols if c in filtered_df.columns]
    table_df = filtered_df[avail_cols].copy()

    def color_status(val):
        if val in ["RECOVERED", "SETTLED_1TAP"]:
            return 'color: #10B981; font-weight: bold; background-color: rgba(16, 185, 129, 0.1);'
        elif val == "FAILED":
            return 'color: #F43F5E; font-weight: bold; background-color: rgba(244, 63, 94, 0.1);'
        elif val in ["SUPPRESSED", "CHURN_HALTED"]:
            return 'color: #F59E0B; font-weight: bold;'
        return 'color: #94A3B8;'

    def color_tier(val):
        if val == "VIP_HIGH_LTV":
            return 'color: #A855F7; font-weight: bold;'
        elif val == "HIGH_CHURN_RISK":
            return 'color: #F59E0B;'
        return 'color: #38BDF8;'

    st_styled = table_df.style.map(color_status, subset=['status']).map(color_tier, subset=['customer_tier'] if 'customer_tier' in table_df.columns else []).format({
        'amount': '₹{:,.2f}',
        'payable_amount': '₹{:,.2f}',
        'customer_ltv': '₹{:,.2f}',
        'discount_pct': '{:.0f}%'
    })

    st.dataframe(st_styled, use_container_width=True, height=350)

    # Detailed Transaction Inspector
    selected_tx_id = st.selectbox(
        "🔎 Select a transaction to inspect its complete execution lifecycle & payload:",
        options=filtered_df['transaction_id'].tolist(),
        format_func=lambda x: f"{x} - {filtered_df[filtered_df['transaction_id'] == x]['customer_name'].values[0]} (₹{filtered_df[filtered_df['transaction_id'] == x]['amount'].values[0]:.2f} | {filtered_df[filtered_df['transaction_id'] == x]['status'].values[0]})",
        key="tx_audit_inspector"
    )

    if selected_tx_id:
        tx_detail = filtered_df[filtered_df['transaction_id'] == selected_tx_id].iloc[0]
        
        d_c1, d_c2, d_c3, d_c4 = st.columns(4)
        with d_c1:
            st.markdown(f"**Customer:** {tx_detail['customer_name']}")
            st.markdown(f"**LTV Tier:** `{tx_detail.get('customer_tier', 'REGULAR')}`")
        with d_c2:
            st.markdown(f"**Cart Value:** ₹{tx_detail['amount']:,.2f}")
            st.markdown(f"**Payable Value:** ₹{tx_detail.get('payable_amount', tx_detail['amount']):,.2f}")
        with d_c3:
            st.markdown(f"**Failed Bank Rail:** `{tx_detail['bank']}`")
            st.markdown(f"**Failure Reason:** `{tx_detail['failure_reason']}`")
        with d_c4:
            st.markdown(f"**Retry Window:** `{tx_detail.get('optimal_retry_window', 'Immediate')}`")
            st.markdown(f"**Settlement State:** `{tx_detail['status']}`")

        if tx_detail.get('discount_token'):
            st.info(f"🏷️ **Active Dynamic Token:** `{tx_detail['discount_token']}` | Copilot Discount: **{tx_detail.get('discount_pct', 0):.0f}%** (Saved ₹{tx_detail.get('discount_amount', 0):,.2f})")

        st.markdown("**Action Audit Trail History:**")
        for step in tx_detail['history']:
            success_icon = "✅ SUCCESS" if step.get("success") else "❌ FAILED"
            if step["action"] == "SKIP":
                st.warning(f"⏩ **Guardrail Skip Action** — Reason: {step.get('reason')}")
            elif step["action"] in ["SUPPRESS", "HALT_CHURN_RISK"]:
                st.info(f"🔕 **Policy Suppression Action** — Reason: {step.get('reason')}")
            else:
                reroute_str = ""
                if step.get("rerouted"):
                    reroute_str = f" | Rerouted to **{step['fallback_bank']}** via **{step['fallback_handle']}**"
                st.markdown(
                    f"<div style='background: rgba(30, 41, 59, 0.6); padding: 10px 14px; border-radius: 8px; margin-bottom: 8px; border-left: 3px solid #3395FF;'>"
                    f"🔄 <b>Attempt {step['attempt']}</b>: Action <code>{step['action']}</code>{reroute_str} | "
                    f"Cost: ₹{step['cost']:.2f} | Prob: {step.get('probability', 0)*100:.1f}% | Outcome: <b>{success_icon}</b>"
                    f"</div>",
                    unsafe_allow_html=True
                )

# ==============================================================================
# TAB 2: LIVE RAIL TELEMETRY & 1-TAP MANDATE SANDBOX
# ==============================================================================
with tab2:
    st.markdown("### ⚡ Live Payment Rail Telemetry & 1-Tap Mandate Settlement Sandbox")
    st.markdown("Monitor issuing bank health in real-time, test custom transaction webhook recovery scenarios, and simulate instant 1-Tap UPI customer completions.")

    telemetry = BankTelemetry()
    
    col_sb_left, col_sb_right = st.columns([2, 3])
    
    with col_sb_left:
        st.markdown("#### 🏦 Issuing Bank NetBanking Telemetry")
        tb1, tb2 = st.columns(2)
        
        banks = ["HDFC", "SBI", "ICICI", "Axis"]
        for i, b in enumerate(banks):
            rate = telemetry.get_bank_rate(b)
            status = "Healthy" if rate >= 0.65 else "Degraded"
            icon = "🟢" if rate >= 0.65 else "🔴"
            color = "#10B981" if rate >= 0.65 else "#EF4444"
            target_col = tb1 if i % 2 == 0 else tb2
            
            with target_col:
                st.markdown(f"""
                <div style="background-color: #111827; border-radius: 12px; padding: 14px; border: 1px solid rgba(255,255,255,0.08); margin-bottom: 10px; text-align: center;">
                    <div style="font-size: 13px; font-weight: 600; color: #94A3B8;">{b} NetBanking</div>
                    <div style="font-size: 20px; font-weight: 800; color: #FFFFFF; margin: 4px 0;">{rate*100:.0f}% SR</div>
                    <span style="background-color: {color}20; color: {color}; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; border: 1px solid {color}50;">
                        {icon} {status}
                    </span>
                </div>
                """, unsafe_allow_html=True)
                
        # UPI Fallback Rails
        st.markdown("#### 📱 UPI Fallback Rails Health")
        u1, u2, u3 = st.columns(3)
        upi_handles = ["@okhdfcbank", "@oksbi", "@paytm"]
        for i, h in enumerate(upi_handles):
            rate = telemetry.get_upi_rate(h)
            status = "Healthy" if rate >= 0.65 else "Degraded"
            icon = "🟢" if rate >= 0.65 else "🔴"
            color = "#10B981" if rate >= 0.65 else "#EF4444"
            target_col = u1 if i == 0 else (u2 if i == 1 else u3)
            
            with target_col:
                st.markdown(f"""
                <div style="background-color: #111827; border-radius: 10px; padding: 10px; border: 1px solid rgba(255,255,255,0.06); text-align: center;">
                    <div style="font-size: 12px; font-weight: 600; color: #94A3B8;">{h}</div>
                    <div style="font-size: 16px; font-weight: 700; color: #FFFFFF;">{rate*100:.0f}% SR</div>
                    <span style="color: {color}; font-size: 11px; font-weight: 700;">{icon} {status}</span>
                </div>
                """, unsafe_allow_html=True)

        st.write("---")
        
        # Interactive Webhook Simulator Form
        st.markdown("#### 🧪 Interactive Webhook Simulator")
        
        sim_name = st.selectbox(
            "Select Customer Profile Preset",
            ["Rahul Sharma (VIP Patron - High LTV)", "Aarav Gupta (Regular E-Commerce)", "Kiara Sen (High Churn Risk Dropoff)", "Custom Ingestion..."],
            key="sim_profile_preset"
        )
        
        if "VIP" in sim_name:
            def_tier = "VIP_HIGH_LTV"
            def_ltv = 65000.0
            def_name = "Rahul Sharma"
            def_amt = 3200.0
            def_bank = "HDFC"
            def_cat = "TECHNICAL_TRANSIENT"
            def_churn = 0.15
        elif "Churn" in sim_name:
            def_tier = "HIGH_CHURN_RISK"
            def_ltv = 8500.0
            def_name = "Kiara Sen"
            def_amt = 2400.0
            def_bank = "SBI"
            def_cat = "USER_DROPOFF"
            def_churn = 0.88
        elif "Regular" in sim_name:
            def_tier = "REGULAR"
            def_ltv = 18000.0
            def_name = "Aarav Gupta"
            def_amt = 1500.0
            def_bank = "HDFC"
            def_cat = "USER_DROPOFF"
            def_churn = 0.40
        else:
            def_tier = "REGULAR"
            def_ltv = 15000.0
            def_name = "Raj Malhotra"
            def_amt = 2100.0
            def_bank = "ICICI"
            def_cat = "USER_BALANCE"
            def_churn = 0.35

        c_s1, c_s2 = st.columns(2)
        with c_s1:
            customer_name = st.text_input("Customer Name", def_name, key="sim_cname")
            sim_tier = st.selectbox("Customer Tier", ["VIP_HIGH_LTV", "REGULAR", "HIGH_CHURN_RISK"], index=["VIP_HIGH_LTV", "REGULAR", "HIGH_CHURN_RISK"].index(def_tier), key="sim_tier")
            sim_ltv = st.number_input("Customer LTV (₹)", min_value=500.0, max_value=500000.0, value=def_ltv, step=1000.0, key="sim_ltv")
            sim_churn = st.slider("Churn Risk Score", 0.0, 1.0, def_churn, step=0.05, key="sim_churn_slider")
            
        with c_s2:
            sim_amount = st.number_input("Transaction Amount (₹)", min_value=1.0, max_value=100000.0, value=def_amt, step=100.0, key="sim_amount")
            sim_bank = st.selectbox("Failed Issuing Bank Rail", ["HDFC", "SBI", "ICICI", "Axis"], index=["HDFC", "SBI", "ICICI", "Axis"].index(def_bank), key="sim_bank")
            sim_category = st.selectbox(
                "Failure Category",
                ["USER_DROPOFF", "TECHNICAL_TRANSIENT", "USER_BALANCE", "AUTHENTICATION_HARD"],
                index=["USER_DROPOFF", "TECHNICAL_TRANSIENT", "USER_BALANCE", "AUTHENTICATION_HARD"].index(def_cat),
                key="sim_cat"
            )
            reasons_by_cat = {
                "USER_DROPOFF": ["CUSTOMER_CLOSED_CHECKOUT", "OTP_PAGE_ABANDONED", "CHOSE_TO_CANCEL"],
                "TECHNICAL_TRANSIENT": ["BANK_SYSTEM_TIMEOUT", "GATEWAY_DOWNTIME", "NETWORK_LATENCY_EXCEEDED"],
                "USER_BALANCE": ["INSUFFICIENT_FUNDS", "ACCOUNT_LIMIT_EXCEEDED"],
                "AUTHENTICATION_HARD": ["INCORRECT_OTP", "CARD_EXPIRED", "CARD_BLOCKED_BY_ISSUER", "INVALID_PIN"]
            }
            sim_reason = st.selectbox("Failure Reason Code", reasons_by_cat[sim_category], key="sim_reason")

        if st.button("⚡ Dispatch Webhook to Dunning Engine", key="trigger_sim_btn"):
            sim_tx = {
                "transaction_id": f"pay_live_{int(datetime.now().timestamp())}",
                "customer_name": customer_name,
                "customer_phone": "+919876543210",
                "customer_email": f"{customer_name.lower().replace(' ', '.')}@example.com",
                "customer_tier": sim_tier,
                "customer_ltv": sim_ltv,
                "churn_risk_score": sim_churn,
                "amount": sim_amount,
                "bank": sim_bank,
                "failure_category": sim_category,
                "failure_reason": sim_reason,
                "timestamp": datetime.now().isoformat()
            }
            
            sim_result = agent.process_transaction(sim_tx, use_fallback=True, policy=st.session_state["active_policy"])
            st.session_state["active_sim_result"] = sim_result
            st.success("Webhook processed! Interactive communications & 1-Tap Drawer ready on right.")

    # Right Column: Interactive Communications & 1-Tap Settlement Drawer
    with col_sb_right:
        st.markdown("#### 📱 Live Communications & 1-Tap Mandate Settlement Drawer")
        
        c_lang, c_chan = st.columns(2)
        with c_lang:
            preview_lang = st.radio("Message Localization", ["Natural Hinglish", "English"], horizontal=True, key="pv_lang")
        with c_chan:
            preview_channel = st.radio("Dispatch Rail", ["WhatsApp Business", "SMS Text"], horizontal=True, key="pv_chan")
            
        if "active_sim_result" in st.session_state:
            sim_res = st.session_state["active_sim_result"]
            tx_id = sim_res["transaction_id"]
            
            active_attempt = None
            for step in sim_res["history"]:
                if step["action"] not in ["SKIP", "SUPPRESS", "HALT_CHURN_RISK"]:
                    active_attempt = step
                    break
            
            # Dynamic Retry Window Info Box
            st.markdown(f"""
            <div style="background-color: #111827; border-radius: 10px; padding: 12px; border-left: 4px solid #3395FF; margin-bottom: 12px;">
                <div style="font-size: 11px; color: #94A3B8; font-weight: 700; text-transform: uppercase;">⏱️ Dynamic Retry Scheduling Window</div>
                <div style="font-size: 15px; font-weight: 700; color: #FFFFFF; margin: 2px 0;">{sim_res.get('optimal_retry_window', 'Immediate Recapture')}</div>
                <div style="font-size: 12px; color: #38BDF8;">Scheduled: {sim_res.get('scheduled_time', 'Immediate')} | {sim_res.get('window_reasoning', '')}</div>
            </div>
            """, unsafe_allow_html=True)

            if sim_res["status"] == "SKIPPED":
                st.warning(f"⏩ **Economic Guardrail Triggered:** Transaction ₹{sim_res['amount']:.2f} below threshold ₹{st.session_state['active_policy']['min_amount_threshold']:.2f}.")
            elif sim_res["status"] in ["SUPPRESSED", "CHURN_HALTED"]:
                st.info(f"🔕 **Autonomous Policy Suppression:** {sim_res['history'][0].get('reason', 'Policy constraint triggered')}")
            elif active_attempt:
                msg_text = active_attempt["message_hinglish"] if preview_lang == "Natural Hinglish" else active_attempt["message_english"]
                bubble_bg = "#075E54" if preview_channel == "WhatsApp Business" else "#0052FF"
                header_text = f"💬 WhatsApp Business • {sim_res.get('customer_tier', 'REGULAR')}" if preview_channel == "WhatsApp Business" else f"💬 SMS Alert • {sim_res.get('customer_tier', 'REGULAR')}"
                
                # Render Chat Bubble
                st.markdown(f"""
                <div style="max-width: 480px; margin: 10px auto; background-color: #111827; border-radius: 14px; border: 1px solid rgba(255,255,255,0.1); padding: 14px; box-shadow: 0 8px 24px rgba(0,0,0,0.6);">
                    <div style="font-size: 11px; color: #8696A0; margin-bottom: 8px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">{header_text}</div>
                    <div style="background-color: {bubble_bg}; border-radius: 10px; padding: 12px; position: relative;">
                        <p style="color: #FFFFFF; margin: 0; font-size: 13.5px; line-height: 1.5;">
                            {msg_text}
                        </p>
                        <span style="font-size: 10px; color: rgba(255,255,255,0.7); float: right; margin-top: 6px;">⚡ Just Now</span>
                        <div style="clear: both;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # ==========================================================
                # KILLER FEATURE: INTERACTIVE 1-TAP MANDATE SETTLEMENT DRAWER
                # ==========================================================
                is_settled = sim_res["status"] in ["SETTLED_1TAP", "RECOVERED"] or tx_id in st.session_state["settled_overrides"]
                
                st.markdown("---")
                st.markdown("##### 📱 1-Tap Mandate Settlement Drawer (Customer Simulation)")
                
                drawer_container = st.container()
                with drawer_container:
                    if is_settled:
                        utr = st.session_state["settled_overrides"].get(tx_id, {}).get("utr_ref", "UPI/2026/90281944")
                        st.markdown(f"""
                        <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 12px; padding: 16px; text-align: center;">
                            <div style="font-size: 20px;">🎉</div>
                            <div style="color: #10B981; font-weight: 800; font-size: 16px;">PAYMENT INSTANTLY SETTLED</div>
                            <div style="color: #F8FAFC; font-size: 13px; margin: 6px 0;">
                                Gross Amount ₹{sim_res['amount']:,.2f} captured via PhonePe / GPay 1-Tap Intent.
                            </div>
                            <div style="font-size: 11px; color: #94A3B8;">
                                UTR Ref: <code>{utr}</code> | Rail: <code>UPI_INTENT_1TAP</code> | Status: <b style="color: #10B981;">SETTLED</b>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        payable = sim_res.get('payable_amount', sim_res['amount'])
                        disc_str = f"<span style='color: #38BDF8;'> (₹{sim_res.get('discount_amount', 0):,.2f} Copilot Discount Applied)</span>" if sim_res.get('discount_applied') else ""
                        
                        st.markdown(f"""
                        <div class="settlement-drawer">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <span style="font-size: 13px; font-weight: 700; color: #38BDF8;">Razorpay 1-Tap UPI Gateway</span>
                                <span class="status-badge status-settled">Ready</span>
                            </div>
                            <div style="font-size: 13px; color: #94A3B8; margin-bottom: 4px;">
                                Original Cart: ₹{sim_res['amount']:,.2f} | <b>Payable: ₹{payable:,.2f}</b>{disc_str}
                            </div>
                            <div style="font-size: 11px; color: #64748B; margin-bottom: 12px;">
                                Destination: <code>razorpay.me/pay_{tx_id[-6:]}</code> | Alternate Rail: <code>{active_attempt.get('fallback_bank', sim_res['bank'])} NetBanking / PhonePe</code>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("📱 Simulate Customer Clicking 1-Tap UPI Link (PhonePe / GPay)", key="settle_1tap_btn", type="primary", use_container_width=True):
                            # Flip status in session state
                            now_time = datetime.now().isoformat()
                            generated_utr = f"UPI/2026/{int(datetime.now().timestamp()*100)%90000000 + 10000000}"
                            
                            st.session_state["settled_overrides"][tx_id] = {
                                "settlement_time": now_time,
                                "utr_ref": generated_utr,
                                "amount": sim_res["amount"]
                            }
                            sim_res["status"] = "SETTLED_1TAP"
                            
                            st.balloons()
                            st.toast(f"🎉 1-Tap UPI Mandate Settled! ₹{sim_res['amount']:,.2f} credited to merchant ledger via PhonePe/GPay.", icon="⚡")
                            st.rerun()

            # Execution Trace Logs
            st.write("---")
            st.markdown("##### ⚙️ Webhook Execution Trace Logs")
            st.markdown(f"**Transaction ID:** `{sim_res['transaction_id']}` | **Status:** `{sim_res['status']}` | **Dunning Cost:** ₹{sim_res['total_cost']:.2f}")
            
            for step in sim_res["history"]:
                sc_icon = "✅ SUCCESS" if step.get("success") else "❌ FAILED"
                if step["action"] == "SKIP":
                    st.warning(f"⏩ **[Guardrail]** {step.get('reason')}")
                elif step["action"] in ["SUPPRESS", "HALT_CHURN_RISK"]:
                    st.info(f"🔕 **[Policy]** {step.get('reason')}")
                else:
                    st.markdown(f"* **Attempt {step['attempt']}:** `{step['action']}` | Cost: ₹{step['cost']:.2f} | Prob: {step.get('probability', 0)*100:.1f}% | **{sc_icon}**")
        else:
            st.info("💡 Select a profile preset and click **'Dispatch Webhook'** on the left to activate the interactive 1-Tap Settlement drawer.")

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

    # Computations
    monthly_txns = monthly_gmv / avg_ticket
    monthly_failed_txns = monthly_txns * failure_rate
    monthly_failed_gmv = monthly_gmv * failure_rate
    annual_failed_gmv = monthly_failed_gmv * 12.0

    monthly_recovered_gmv = monthly_failed_gmv * recovery_efficiency
    annual_recovered_gmv = monthly_recovered_gmv * 12.0

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
                <div class="metric-sub" style="color: #38BDF8;">Monthly: ₹{monthly_recovered_gmv/100000:,.1f} Lakhs</div>
            </div>
            """, unsafe_allow_html=True)
            
        with rc2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Net Annual Profit Lift</div>
                <div class="metric-value" style="color: #8B5CF6;">₹{annual_profit_lift/100000:,.2f} L</div>
                <div class="metric-sub" style="color: #A855F7;">EBITDA Margin: {merchant_margin_pct}%</div>
            </div>
            """, unsafe_allow_html=True)
            
        with rc3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Unit Economic ROI</div>
                <div class="metric-value" style="color: #3395FF;">{roi_multiplier:,.0f}x</div>
                <div class="metric-sub" style="color: #94A3B8;">Annual Cost: ₹{annual_cost/1000:,.1f}k</div>
            </div>
            """, unsafe_allow_html=True)

        st.write("")

        # 12-Month Cumulative Trajectory
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
            mode='lines+markers', name='Cumulative Net EBITDA Lift (₹ Lakhs)',
            line=dict(color='#3395FF', width=3, dash='dash')
        ))
        fig_proj.add_trace(go.Scatter(
            x=months, y=cum_status_quo,
            mode='lines', name='Status Quo (₹0)',
            line=dict(color='#F43F5E', width=2)
        ))
        fig_proj.update_layout(
            title='12-Month Cumulative Revenue & Profit Trajectory',
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title='Timeline',
            yaxis_title='Amount (₹ Lakhs)',
            height=320,
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig_proj, use_container_width=True)

    # Sensitivity & Waterfall Row
    st.write("---")
    sc1, sc2 = st.columns(2)

    with sc1:
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
            color_discrete_sequence=["#10B981", "#3395FF"]
        )
        fig_sens.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300)
        st.plotly_chart(fig_sens, use_container_width=True)

    with sc2:
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
            connector={"line": {"color": "#3395FF"}},
            decreasing={"marker": {"color": "#EF4444"}},
            increasing={"marker": {"color": "#10B981"}},
            totals={"marker": {"color": "#38BDF8"}}
        ))
        fig_waterfall.update_layout(
            title="Annual Dunning Unit Economics Waterfall",
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=300
        )
        st.plotly_chart(fig_waterfall, use_container_width=True)

# ==============================================================================
# TAB 4: AUTONOMOUS POLICY COPILOT (THE KILLER FEATURE)
# ==============================================================================
with tab4:
    st.markdown("### 🤖 Autonomous Policy Negotiation & Dynamic Settlement Copilot")
    st.markdown("Define adaptive recovery and concession policies in natural language. The Copilot compiles your business intent into real-time rule weights and runs instant benchmark simulations.")

    # Copilot Prompt Bar
    st.markdown("##### 💬 Natural Language Merchant Policy Input")
    
    preset_col1, preset_col2, preset_col3, preset_col4, preset_col5 = st.columns(5)
    
    if preset_col1.button("🏷️ 5% UPI Cart > ₹2k", key="pr1", use_container_width=True):
        st.session_state["copilot_prompt"] = "Give 5% dynamic discount on dropped UPI carts > ₹2000"
    if preset_col2.button("🛑 Strict Churn > 0.80", key="pr2", use_container_width=True):
        st.session_state["copilot_prompt"] = "Strict Zero Retries for Churn Score > 0.8"
    if preset_col3.button("💎 10% VIP Retention", key="pr3", use_container_width=True):
        st.session_state["copilot_prompt"] = "Offer 10% dynamic discount for VIP customers with LTV > ₹50000"
    if preset_col4.button("⚡ 7% Cart Recapture", key="pr4", use_container_width=True):
        st.session_state["copilot_prompt"] = "Give 7% instant discount on user dropoffs above ₹1500"
    if preset_col5.button("🛡️ 1 Retry Low Cost", key="pr5", use_container_width=True):
        st.session_state["copilot_prompt"] = "Cap max retries to 1 for transactions below ₹500"

    user_policy_input = st.text_input(
        "Type or edit your merchant recovery policy in plain English:",
        value=st.session_state["copilot_prompt"],
        key="merchant_nl_input"
    )

    # Compile Natural Language Policy
    compiled_policy = parse_natural_language_policy(user_policy_input)

    c_comp_left, c_comp_right = st.columns([1, 1])

    with c_comp_left:
        st.markdown("#### 🧠 AI Policy Intent Synthesis")
        st.markdown(f"""
        <div class="copilot-box">
            <div style="font-size: 14px; font-weight: 700; color: #38BDF8; margin-bottom: 8px;">
                🎯 Rule Summary: {compiled_policy['rule_description']}
            </div>
            <div style="margin-top: 10px;">
                <span class="copilot-chip">🏷️ Discount: {compiled_policy['discount_pct']:.0f}%</span>
                <span class="copilot-chip">💰 Min Cart: ₹{compiled_policy['discount_min_amount']:,.0f}</span>
                <span class="copilot-chip">🔄 Max Retries: {compiled_policy['max_retries']}</span>
                <span class="copilot-chip">🛡️ Churn Cutoff: {compiled_policy['churn_risk_threshold']:.2f} ({'Zero Retries' if compiled_policy['zero_retry_on_high_churn'] else 'Standard'})</span>
                <span class="copilot-chip">🎯 Target: {', '.join(compiled_policy['discount_categories'])}</span>
            </div>
            <div style="font-size: 12px; color: #94A3B8; margin-top: 12px; line-height: 1.5;">
                <b>Autonomous Agent Rationale:</b> Incentivizes drop-off customers with dynamic 1-tap checkout tokens while suppressing unprofitable retries on low-margin or high-churn risk carts.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("##### 📄 Compiled JSON Policy Schema")
        st.json(compiled_policy)

    with c_comp_right:
        st.markdown("#### ⚡ Live Benchmark Simulation (Before vs After)")
        
        # Run comparison simulation
        sim_baseline_agent = SmartDunningAgent(policy=DEFAULT_POLICY)
        sim_copilot_agent = SmartDunningAgent(policy=compiled_policy)
        
        base_res = [sim_baseline_agent.process_transaction(tx, use_fallback=True) for tx in raw_transactions]
        cop_res = [sim_copilot_agent.process_transaction(tx, use_fallback=True) for tx in raw_transactions]
        
        base_rec_count = sum(1 for r in base_res if r["status"] == "RECOVERED")
        cop_rec_count = sum(1 for r in cop_res if r["status"] == "RECOVERED")
        
        base_gmv = sum(r["amount"] for r in base_res if r["status"] == "RECOVERED")
        cop_gmv = sum(r["amount"] for r in cop_res if r["status"] == "RECOVERED")
        
        cop_disc_cost = sum(r.get("discount_amount", 0) for r in cop_res if r["status"] == "RECOVERED")
        cop_msg_cost = sum(r["total_cost"] for r in cop_res)
        base_msg_cost = sum(r["total_cost"] for r in base_res)
        
        cop_net_profit = (cop_gmv - cop_disc_cost) - cop_msg_cost
        base_net_profit = base_gmv - base_msg_cost
        
        halted_count = sum(1 for r in cop_res if r["status"] == "CHURN_HALTED")
        
        # Comparison Metric Cards
        comp_c1, comp_c2 = st.columns(2)
        
        with comp_c1:
            gmv_delta = cop_gmv - base_gmv
            st.markdown(f"""
            <div class="metric-card" style="border-color: rgba(51, 149, 255, 0.4);">
                <div class="metric-title">Simulated Recovered GMV</div>
                <div class="metric-value" style="color: #10B981;">₹{cop_gmv:,.2f}</div>
                <div class="metric-sub" style="color: #38BDF8;">
                    Delta: <b>{'+' if gmv_delta >= 0 else ''}₹{gmv_delta:,.2f}</b> ({'+' if (cop_rec_count-base_rec_count)>=0 else ''}{cop_rec_count - base_rec_count} txs)
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with comp_c2:
            profit_delta = cop_net_profit - base_net_profit
            st.markdown(f"""
            <div class="metric-card" style="border-color: rgba(139, 92, 246, 0.4);">
                <div class="metric-title">Net Merchant Profit Saved</div>
                <div class="metric-value" style="color: #8B5CF6;">₹{cop_net_profit:,.2f}</div>
                <div class="metric-sub" style="color: #A855F7;">
                    Delta: <b>{'+' if profit_delta >= 0 else ''}₹{profit_delta:,.2f}</b> (Discounts: ₹{cop_disc_cost:,.2f})
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        st.write("")
        st.markdown(f"""
        <div style="background: rgba(17, 24, 39, 0.7); border-radius: 10px; padding: 12px; border: 1px solid rgba(255,255,255,0.08); font-size: 13px;">
            🛡️ <b>Shielded Carts:</b> <code>{halted_count}</code> high-churn dropoffs shielded from notification fatigue.<br>
            🏷️ <b>1-Tap Incentive Tokens:</b> <code>{sum(1 for r in cop_res if r.get('discount_applied'))}</code> transactions received dynamic discount links.
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        if st.button("🚀 Apply Compiled Policy Globally to Enterprise Engine", key="apply_pol_global_btn", type="primary", use_container_width=True):
            st.session_state["active_policy"] = compiled_policy
            st.session_state["copilot_prompt"] = user_policy_input
            st.toast("✅ Autonomous Policy deployed globally! All tabs and simulations updated.", icon="🤖")
            st.rerun()

    # Manual Fine-Tuning Parameter Sliders
    st.write("---")
    st.markdown("#### 🎛️ Manual Policy Fine-Tuning Sliders")
    
    ft_c1, ft_c2, ft_c3, ft_c4 = st.columns(4)
    with ft_c1:
        ft_disc = st.slider("Dynamic Discount (%)", 0.0, 25.0, compiled_policy["discount_pct"], step=1.0, key="ft_disc")
    with ft_c2:
        ft_min = st.number_input("Discount Minimum Cart (₹)", 100.0, 10000.0, compiled_policy["discount_min_amount"], step=250.0, key="ft_min")
    with ft_c3:
        ft_retries = st.slider("Max Dunning Retries", 1, 4, compiled_policy["max_retries"], key="ft_retries")
    with ft_c4:
        ft_churn_cutoff = st.slider("Churn Risk Cutoff", 0.1, 1.0, compiled_policy["churn_risk_threshold"], step=0.05, key="ft_churn")

    if st.button("💾 Save & Apply Fine-Tuned Adjustments", key="apply_slider_pol"):
        tuned = compiled_policy.copy()
        tuned["discount_pct"] = ft_disc
        tuned["discount_min_amount"] = ft_min
        tuned["max_retries"] = ft_retries
        tuned["churn_risk_threshold"] = ft_churn_cutoff
        tuned["zero_retry_on_high_churn"] = ft_churn_cutoff < 1.0
        tuned["rule_description"] = f"{ft_disc:.0f}% Discount on Cart > ₹{ft_min:,.0f} | Max {ft_retries} Retries | Churn Cutoff {ft_churn_cutoff:.2f}"
        st.session_state["active_policy"] = tuned
        st.toast("✅ Fine-tuned parameters applied globally!", icon="🎛️")
        st.rerun()
