# SmartDunning AI — Autonomous Revenue Recovery Agent
> **Razorpay AI Buildathon 2026 | Track 03: AI Revenue Recovery**

SmartDunning AI is an event-driven, autonomous revenue recovery engine designed to diagnose why digital payments degrade or fail, apply strict economic and policy guardrails, and execute bounded recovery workflows.

---

## 🎯 The Core Problem & Approach
Standard dunning systems blindly retry failed transactions or immediately drop customers, driving up bank API costs, notification spam, and customer churn.

SmartDunning AI closes the loop:
1. **Root-Cause Failure Triage:** Differentiates between transient bank node downtime, month-end balance timing, user session drop-offs, and hard mandate expirations.
2. **Economic & Policy Guardrails:** Evaluates expected value vs. messaging unit cost ($\text{EV} \le 0 \implies \text{Skip}$), caps retries at 3, and respects cool-down windows.
3. **Multi-Channel Bounded Action:** Schedules silent retries for technical issues, sends 1-tap UPI fallback links for drop-offs, and halts immediately on permanent credential blocks.
4. **Transparent Auditability:** Maintains a complete audit log of decisions, costs, and state transitions.

---

## 📊 Batch Evaluation Benchmark (`eval.py`)
Tested across a synthetic batch of 100 failed payment webhooks:

- **Total Volume At Risk:** ₹1,07,228.47
- **Transactions Recovered:** 64 / 100 (64.0% overall / 72.7% on eligible)
- **Gross Revenue Recovered:** ₹68,553.96
- **Total Intervention Cost:** ₹111.90
- **Net Merchant Profit Saved:** ₹68,442.06
- **Dunning ROI:** 612.6x

---

## 🏗️ System Architecture   
<!-- [Failed Payment Event]
│
▼
[Root-Cause Classifier]
│
▼
[Guardrail Check: Retry Cap & Unit Economics]
│
┌─────┴───────────────────────────┐
▼                                 ▼
[Technical / Balance]        [Drop-Off / Mandate]
│                                 │
[Silent Scheduled Retry]     [1-Tap WhatsApp Link]
│                                 │
└─────────────────┬───────────────┘
│
▼
[Audit Ledger & Metrics UI]      -->