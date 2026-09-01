# ⚡ SmartDunning AI — Autonomous Revenue Recovery & Dynamic Rail Telemetry
> **Razorpay AI Buildathon 2026 | Track 03: AI Revenue Recovery**

SmartDunning AI is an enterprise-grade autonomous revenue recovery engine that diagnoses failed payment root causes, monitors issuing bank health telemetry in real-time, optimizes retry windows based on salary liquidity cycles, and executes bounded multi-rail fallbacks while preserving high-LTV customer relationships.

---

## 🎯 Key Architectural Pillars

1. **Dynamic Bank Health Telemetry & UPI Fallback:**
   - Real-time success rate monitoring for major Indian issuing banks (HDFC, SBI, ICICI, Axis).
   - Dynamic rail switching (e.g., auto-routing degraded HDFC NetBanking failures to 1-click PhonePe/GPay intent links).
   - Localized conversational Hinglish & English message templates.

2. **Customer LTV & Churn-Risk Aware Dunning:**
   - VIP/High-LTV patrons receive zero-delay white-glove WhatsApp routing with 1-click fallback links (+12% affinity boost).
   - Low-margin transactions default to low-cost SMS/silent retries to protect merchant unit economics.

3. **Temporal Intelligence & Dynamic Retry Scheduling:**
   - **Salary Liquidity Windows:** Retry alignments for month-start credit cycles (1st–5th).
   - **Nocturnal Maintenance Avoidance:** Zero retries between 12:00 AM – 05:00 AM.
   - **Intent Recapture:** Immediate (< 3 min) dynamic link dispatch for dropped sessions.

4. **Deterministic Fintech Guardrails:**
   - Hard cap of max 3 attempts per transaction.
   - Permanent suppression on expired/revoked mandates (`AUTHENTICATION_HARD`) to eliminate wasteful API charges.
   - Economic ROI check: Skips outbound messaging if $\text{Intervention Cost} \ge 10\%$ of transaction value.

---

## 📊 Evaluation Scorecard (`eval.py`)

Tested across a batch of 100 failed payment webhooks:

| Metric | Baseline Dunning | SmartDunning AI (Tier-1) | Impact / Lift |
|---|---|---|---|
| **Recovery Rate** | 64.0% | **79.0%** | **+15.0% Lift** |
| **Gross Revenue Recovered** | ₹68,553.96 | **₹86,672.72** | **+₹18,118.76** |
| **Preserved Customer LTV Equity** | — | **₹18,62,400.00** | **Protected** |
| **Total Notification Costs** | ₹111.90 | ₹128.40 | Controlled |
| **Net Merchant Profit Saved** | ₹68,442.06 | **₹86,544.32** | **+26.4%** |
| **Net Dunning ROI** | 612.6x | **674.0x** | **High Efficiency** |

---

## 🏗️ End-to-End Pipeline
<!-- [Failed Payment Event]
│
▼
[Root-Cause & Bank Telemetry Triage]
│
▼
[LTV Tiering & Churn Risk Classifier]
│
▼
[Guardrail Enforcement (Retry Cap + Unit Economics)]
│
┌─────┴───────────────────────────────────────┐
▼                                             ▼
[Technical / Balance / Nocturnal]       [UPI Drop-Off / High LTV]
│                                             │
[Temporal Scheduled Backoff]            [1-Tap WhatsApp Link (Hinglish/EN)]
│                                             │
└──────────────────────┬──────────────────────┘
│
▼
[Sankey Flow & Audit Ledger] -->

---

## 🚀 Quickstart & Local Setup

```bash
# 1. Clone repository
git clone <YOUR_REPO_URL>
cd smart-dunning-ai

# 2. Activate Virtual Environment
.\venv\Scripts\Activate.ps1  # On Linux/macOS: source venv/bin/activate

# 3. Install Dependencies
pip install -r requirements.txt

# 4. Run Batch Evaluation Benchmark
python mock_data.py
python eval.py

# 5. Launch Interactive Dashboard
streamlit run app.py