"""
researcher.py — Kenya MSME Research Dashboard
Displays research outcomes for Kenya MSME study.
Access: Researcher role only.
"""

import streamlit as st
import sys
import json
import csv
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))
from kenya_msme_db import (
    list_all_users, get_baseline, get_endline,
    get_all_prompt_scores, get_research_summary
)

BASE_DIR = Path(__file__).parent.parent.parent
LOG_FILE = BASE_DIR / "logs" / "conversations.csv"

st.set_page_config(
    page_title="MSME Advisor — Research Dashboard",
    page_icon="🔬",
    layout="wide"
)

st.markdown("""
<style>
[data-testid="stSidebarNav"] { display: none !important; }
.kpi { background:#f8f9fa; border-radius:10px; padding:1.2rem;
       text-align:center; border-top:4px solid #006600; }
.kpi-val { font-size:2rem; font-weight:800; color:#006600; }
.kpi-lab { font-size:0.8rem; color:#666; margin-top:4px; }
.t1 { color:#006600; font-weight:700; }
.t2 { color:#cc0000; font-weight:700; }
</style>
""", unsafe_allow_html=True)

if not st.session_state.get("logged_in"):
    st.switch_page("pages/login.py")
if st.session_state.get("role") not in ["researcher", "admin"]:
    st.error("❌ Researcher role required.")
    st.stop()

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,#006600,#1a3a6e);
color:white;padding:1.2rem 1.5rem;border-radius:10px;margin-bottom:1.5rem;">
<h2 style="margin:0">🔬 Kenya MSME — Research Dashboard</h2>
<p style="margin:0.3rem 0 0;opacity:0.85;font-size:0.9rem">
Kenya MSME AI Advisory Study · Strathmore University 2026
</p>
</div>
""", unsafe_allow_html=True)

# Sidebar navigation
with st.sidebar:
    st.markdown("### 🔬 Research")
    section = st.radio("Section", [
        "📊 Overview",
        "👥 Participants",
        "📋 Baseline Surveys",
        "📈 Outcomes (Endline)",
        "🤖 AI Literacy Trends",
        "⚖️ T1 vs T2 Comparison",
        "💬 Conversation Log",
    ], label_visibility="collapsed")

    st.markdown("---")
    if st.button("← Back to Analytics", use_container_width=True):
        st.switch_page("pages/analytics.py")
    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("app.py")

# Load all data
summary = get_research_summary()
users   = list_all_users()
scores  = get_all_prompt_scores()

t1_users = [u for u in users if u.get("arm") == "T1"]
t2_users = [u for u in users if u.get("arm") == "T2"]
t1_ids   = {u["user_id"] for u in t1_users}
t2_ids   = {u["user_id"] for u in t2_users}

# ── OVERVIEW ──────────────────────────────────────────────────────────────────
if section == "📊 Overview":
    st.subheader("📊 Study Overview")

    cols = st.columns(4)
    metrics = [
        ("Total Participants", summary["total_users"], ""),
        ("T1 — Localised AI", summary["t1_count"], "RAG + Kenyan KB"),
        ("T2 — Generic AI", summary["t2_count"], "Plain Claude"),
        ("Baseline Completed", summary["baseline_count"], "Pre-surveys"),
    ]
    for col, (label, value, sub) in zip(cols, metrics):
        with col:
            st.markdown(f"""
            <div class="kpi">
                <div class="kpi-val">{value}</div>
                <div class="kpi-lab">{label}<br><small>{sub}</small></div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")
    cols2 = st.columns(4)
    metrics2 = [
        ("Endline Completed", summary["endline_count"], "Post-surveys"),
        ("Total Questions", summary["total_questions"], "All interactions"),
        ("Avg Score T1", summary["avg_score_t1"], "Prompt quality /10"),
        ("Avg Score T2", summary["avg_score_t2"], "Prompt quality /10"),
    ]
    for col, (label, value, sub) in zip(cols2, metrics2):
        with col:
            st.markdown(f"""
            <div class="kpi">
                <div class="kpi-val">{value}</div>
                <div class="kpi-lab">{label}<br><small>{sub}</small></div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🎯 Research Design")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
**Treatment Arm T1 — Localised AI (Kenya MSME Advisor)**
- RAG over 35,208 verified Kenyan regulatory chunks
- 8 domain-specific knowledge bases
- AI literacy coaching layer
- Multilingual: English + Kiswahili + 4 languages
        """)
    with col_b:
        st.markdown("""
**Treatment Arm T2 — Generic AI (Comparison)**
- Plain Claude without RAG knowledge base
- No Kenyan regulatory documents
- General business advice only
- English only
        """)

# ── PARTICIPANTS ──────────────────────────────────────────────────────────────
elif section == "👥 Participants":
    st.subheader("👥 Participant Profiles")

    if not users:
        st.info("No participants yet.")
    else:
        # County distribution
        counties = defaultdict(int)
        biz_types = defaultdict(int)
        for u in users:
            if u.get("county"):
                counties[u["county"]] += 1
            if u.get("business_type"):
                biz_types[u["business_type"]] += 1

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**By County**")
            for county, count in sorted(counties.items(),
                                        key=lambda x: -x[1]):
                st.markdown(f"- {county}: **{count}**")
        with col2:
            st.markdown("**By Business Type**")
            for btype, count in sorted(biz_types.items(),
                                       key=lambda x: -x[1]):
                st.markdown(f"- {btype}: **{count}**")

        st.markdown("---")
        st.markdown("**All Participants**")
        for u in sorted(users, key=lambda x: x.get("created_at",""),
                        reverse=True):
            arm_color = "🟢" if u.get("arm") == "T1" else "🔴"
            baseline  = "✅" if u.get("has_baseline") else "⏳"
            endline   = "✅" if u.get("has_endline") else "⏳"
            st.markdown(
                f"{arm_color} **{u['user_id'][:8]}** | "
                f"Arm: {u.get('arm','?')} | "
                f"County: {u.get('county','?')} | "
                f"Questions: {u.get('total_questions',0)} | "
                f"Baseline: {baseline} | Endline: {endline}"
            )

# ── BASELINE ──────────────────────────────────────────────────────────────────
elif section == "📋 Baseline Surveys":
    st.subheader("📋 Baseline Survey Results")

    baseline_users = [u for u in users if u.get("has_baseline")]
    if not baseline_users:
        st.info("No baseline surveys completed yet.")
    else:
        st.markdown(f"**{len(baseline_users)} baseline surveys completed**")

        # Confidence scores at baseline
        conf_fields = {
            "conf_tax":      "KRA Tax",
            "conf_register": "Business Registration",
            "conf_loan":     "Loan Application",
            "conf_nssf":     "NSSF/SHIF",
            "conf_permit":   "County Permits",
            "conf_ai":       "AI Self-Efficacy",
        }

        st.markdown("### Average Baseline Confidence Scores (1-5 scale)")
        avgs = {field: [] for field in conf_fields}

        for u in baseline_users:
            b = get_baseline(u["user_id"])
            if b:
                for field in conf_fields:
                    val = b.get("responses", {}).get(field)
                    if val:
                        avgs[field].append(int(val))

        cols = st.columns(3)
        for i, (field, label) in enumerate(conf_fields.items()):
            vals = avgs[field]
            avg  = round(sum(vals)/len(vals), 2) if vals else 0
            bar  = "█" * int(avg * 2)
            with cols[i % 3]:
                st.metric(label, f"{avg}/5")

        # Primary challenges
        st.markdown("### Primary Challenges Reported")
        challenges = defaultdict(int)
        for u in baseline_users:
            b = get_baseline(u["user_id"])
            if b:
                ch = b.get("responses", {}).get("primary_challenge")
                if ch:
                    challenges[ch] += 1
        for ch, count in sorted(challenges.items(), key=lambda x: -x[1]):
            pct = int(count / len(baseline_users) * 100)
            st.markdown(f"- {ch}: **{count}** ({pct}%)")

# ── OUTCOMES ──────────────────────────────────────────────────────────────────
elif section == "📈 Outcomes (Endline)":
    st.subheader("📈 Endline Outcomes")

    endline_users = [u for u in users if u.get("has_endline")]
    if not endline_users:
        st.info("No endline surveys completed yet. Endline is triggered after 5 sessions.")
    else:
        st.markdown(f"**{len(endline_users)} endline surveys completed**")

        # Confidence delta
        st.markdown("### Confidence Change (Endline − Baseline)")
        conf_fields = {
            "conf_tax":      "KRA Tax",
            "conf_register": "Business Registration",
            "conf_loan":     "Loan Application",
            "conf_nssf":     "NSSF/SHIF",
            "conf_permit":   "County Permits",
            "conf_ai":       "AI Self-Efficacy",
        }

        deltas = {field: [] for field in conf_fields}
        for u in endline_users:
            b = get_baseline(u["user_id"])
            e = get_endline(u["user_id"])
            if b and e:
                br = b.get("responses", {})
                er = e.get("responses", {})
                for field in conf_fields:
                    bval = br.get(field, 0)
                    eval_ = er.get(field, 0)
                    if bval and eval_:
                        deltas[field].append(int(eval_) - int(bval))

        cols = st.columns(3)
        for i, (field, label) in enumerate(conf_fields.items()):
            vals = deltas[field]
            avg  = round(sum(vals)/len(vals), 2) if vals else 0
            delta_str = f"+{avg}" if avg > 0 else str(avg)
            with cols[i % 3]:
                st.metric(label, delta_str,
                          delta=avg,
                          delta_color="normal")

        # Behavioural outcomes
        st.markdown("### Behavioural Outcomes")
        outcomes = {
            "reg_change":  "Business registered",
            "tax_change":  "KRA filing improved",
            "loan_change": "Loan applied/approved",
            "nssf_change": "NSSF compliance improved",
        }
        for field, label in outcomes.items():
            positive = 0
            total    = 0
            for u in endline_users:
                e = get_endline(u["user_id"])
                if e:
                    val = e.get("responses", {}).get(field, "")
                    total += 1
                    if "Yes" in val:
                        positive += 1
            if total:
                pct = int(positive/total*100)
                st.markdown(f"- **{label}**: {positive}/{total} ({pct}%)")

# ── AI LITERACY TRENDS ────────────────────────────────────────────────────────
elif section == "🤖 AI Literacy Trends":
    st.subheader("🤖 AI Literacy — Prompt Quality Trends")

    if not scores:
        st.info("No prompt scores yet. Scores are recorded as users ask questions.")
    else:
        # Overall trend
        all_s = [s["score"] for s in scores]
        avg   = round(sum(all_s)/len(all_s), 2)
        st.metric("Overall Average Prompt Quality", f"{avg}/10",
                  help="Higher = users asking better questions")

        # Scores over time
        st.markdown("### Score Distribution")
        dist = defaultdict(int)
        for s in scores:
            dist[s["score"]] += 1

        for score_val in range(1, 11):
            count = dist.get(score_val, 0)
            bar   = "█" * count
            st.markdown(f"**{score_val}/10** {bar} ({count})")

        # Recent questions
        st.markdown("### Recent Questions & Scores")
        for s in sorted(scores, key=lambda x: x.get("timestamp",""),
                        reverse=True)[:10]:
            arm = "🟢 T1" if s.get("session_id") in t1_ids else "🔴 T2"
            st.markdown(
                f"{arm} | Score **{s['score']}/10** | "
                f"_{s.get('question','')[:80]}_"
            )

# ── T1 vs T2 COMPARISON ───────────────────────────────────────────────────────
elif section == "⚖️ T1 vs T2 Comparison":
    st.subheader("⚖️ T1 (Localised) vs T2 (Generic) Comparison")

    t1_scores = [s["score"] for s in scores if s.get("session_id") in t1_ids]
    t2_scores = [s["score"] for s in scores if s.get("session_id") in t2_ids]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🟢 T1 — Kenya MSME Advisor (Localised RAG)")
        st.metric("Participants", len(t1_users))
        st.metric("Total Questions", sum(u.get("total_questions",0)
                                        for u in t1_users))
        avg_t1 = round(sum(t1_scores)/len(t1_scores), 2) if t1_scores else 0
        st.metric("Avg Prompt Quality", f"{avg_t1}/10")
        t1_baseline = sum(1 for u in t1_users if u.get("has_baseline"))
        t1_endline  = sum(1 for u in t1_users if u.get("has_endline"))
        st.metric("Baseline Completed", t1_baseline)
        st.metric("Endline Completed",  t1_endline)

    with col2:
        st.markdown("### 🔴 T2 — Generic Claude (No RAG)")
        st.metric("Participants", len(t2_users))
        st.metric("Total Questions", sum(u.get("total_questions",0)
                                        for u in t2_users))
        avg_t2 = round(sum(t2_scores)/len(t2_scores), 2) if t2_scores else 0
        st.metric("Avg Prompt Quality", f"{avg_t2}/10")
        t2_baseline = sum(1 for u in t2_users if u.get("has_baseline"))
        t2_endline  = sum(1 for u in t2_users if u.get("has_endline"))
        st.metric("Baseline Completed", t2_baseline)
        st.metric("Endline Completed",  t2_endline)

    if t1_scores and t2_scores:
        diff = round(avg_t1 - avg_t2, 2)
        st.markdown("---")
        if diff > 0:
            st.success(f"✅ T1 users ask {diff} points higher quality questions than T2 users on average.")
        elif diff < 0:
            st.warning(f"⚠️ T2 users currently score {abs(diff)} points higher. More data needed.")
        else:
            st.info("T1 and T2 users currently score equally. More data needed.")

# ── CONVERSATION LOG ──────────────────────────────────────────────────────────
elif section == "💬 Conversation Log":
    st.subheader("💬 Full Conversation Log")

    if not LOG_FILE.exists():
        st.info("No conversations logged yet.")
    else:
        with open(LOG_FILE, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        st.metric("Total Conversations", len(rows))
        st.markdown("### Recent 20 Conversations")
        for row in rows[-20:][::-1]:
            arm = "🟢 T1" if row.get("session_id") in t1_ids else "🔴 T2"
            st.markdown(
                f"{arm} | **{row.get('date','')} {row.get('time','')}** | "
                f"Lang: {row.get('language_detected','')} | "
                f"Topic: {row.get('topic_category','')} | "
                f"_{row.get('question','')[:60]}_"
            )

        # Download
        with open(LOG_FILE, "rb") as f:
            st.download_button(
                "⬇️ Download Full Log (CSV)",
                f,
                file_name="kenya_msme_conversations.csv",
                mime="text/csv"
            )
