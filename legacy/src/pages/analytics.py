"""
analytics.py — Kenya MSME Advisor: Researcher Analytics Dashboard
Organised with sidebar navigation — no scrolling needed.
"""

import csv
import json
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
import streamlit as st
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from auth import verify_password, update_password, update_profile, load_credentials
from generate_report import generate_pdf_report
from collections import defaultdict as _defaultdict

BASE_DIR  = Path(__file__).parent.parent.parent
LOG_FILE  = BASE_DIR / "logs" / "conversations.csv"
EVAL_FILE = BASE_DIR / "logs" / "evaluation_results.csv"

st.set_page_config(
    page_title="MSME Advisor — Analytics",
    page_icon="📊",
    layout="wide"
)

# ── Hide streamlit nav ─────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebarNav"] { display: none !important; }
.section-title {
    font-size: 1.3rem;
    font-weight: 700;
    color: #1a1a2e;
    padding-bottom: 0.4rem;
    border-bottom: 3px solid #006600;
    margin-bottom: 1.2rem;
}
.nav-btn {
    width: 100%;
    text-align: left;
    padding: 0.6rem 1rem;
    border-radius: 8px;
    margin-bottom: 4px;
    font-size: 0.88rem;
    font-weight: 500;
}
.active-nav {
    background: #e8f5e9;
    border-left: 4px solid #006600;
    color: #006600;
    font-weight: 700;
}
.kpi-box {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 1.2rem;
    text-align: center;
    border-top: 4px solid #006600;
}
.kpi-value {
    font-size: 2rem;
    font-weight: 800;
    color: #006600;
}
.kpi-label {
    font-size: 0.8rem;
    color: #666;
    margin-top: 4px;
}
</style>
""", unsafe_allow_html=True)

# ── Login gate ─────────────────────────────────────────────────────────────────
if not st.session_state.get("logged_in"):
    st.switch_page("pages/login.py")

# ── Research Dashboard shortcut ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    if st.button("🔬 Research Dashboard", use_container_width=True, type="primary"):
        st.switch_page("pages/researcher.py")
    st.markdown("---")

if st.session_state.get("role") not in ["researcher", "admin"]:
    st.error("❌ Access denied. Researcher role required.")
    if st.button("← Back to Login"):
        st.session_state.clear()
        st.switch_page("pages/login.py")
    st.stop()

# ── Load research data ───────────────────────────────────────────────────────
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from kenya_msme_db import (list_all_users, get_baseline, get_endline,
                            get_all_prompt_scores, get_research_summary)
from collections import defaultdict as _dd

# ── Load data ──────────────────────────────────────────────────────────────────
def load_data():
    if not LOG_FILE.exists():
        return []
    with open(LOG_FILE, encoding="utf-8") as f:
        return list(csv.DictReader(f))

rows = load_data()

# ── Compute stats ──────────────────────────────────────────────────────────────
total     = len(rows)
sessions  = len(set(r["session_id"] for r in rows)) if rows else 0
times     = [float(r["response_time_seconds"]) for r in rows
             if r.get("response_time_seconds")]
avg_time  = round(sum(times) / len(times), 1) if times else 0
words     = [int(r["answer_length_words"]) for r in rows
             if r.get("answer_length_words")]
avg_words = round(sum(words) / len(words)) if words else 0
topics    = Counter(r["topic_category"] for r in rows)
languages = Counter(r["language_detected"] for r in rows)
dates     = Counter(r["date"] for r in rows)

all_sources = []
for r in rows:
    if r.get("sources") and r["sources"] != "none":
        all_sources.extend(r["sources"].split(" | "))
src_count = Counter(s for s in all_sources if s.strip())

fast   = sum(1 for t in times if t < 10)
medium = sum(1 for t in times if 10 <= t < 30)
slow   = sum(1 for t in times if t >= 30)

lang_labels = {
    "english":   "🇬🇧 English",
    "kiswahili": "🇰🇪 Kiswahili",
    "dholuo":    "🐟 Dholuo",
    "kikuyu":    "🏔️ Kikuyu",
    "kalenjin":  "🏃 Kalenjin",
    "kamba":     "🎨 Kamba",
}

# ── Navigation state ───────────────────────────────────────────────────────────
if "analytics_page" not in st.session_state:
    st.session_state["analytics_page"] = "Overview"

PAGES = [
    ("📈", "Overview"),
    ("🗂️", "Topic Analysis"),
    ("🔬", "Research"),
    ("🌍", "Language Analysis"),
    ("⏱️", "Response Times"),
    ("📚", "Knowledge Sources"),
    ("🧪", "Evaluation Results"),
    ("💬", "Conversations"),
    ("📥", "Export Data"),
    ("👤", "My Profile"),
]

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:0.5rem 0 0.8rem 0;'>
        <span style='font-size:1.1rem;font-weight:700;color:#006600'>
        📊 Analytics
        </span><br>
        <span style='font-size:0.72rem;color:#888'>Researcher Dashboard</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"👤 **{st.session_state.get('user_name','Researcher')}**")
    st.caption(f"📊 {total} Q&As · {sessions} sessions")

    st.markdown("---")
    st.markdown("**Dashboard Sections**")

    for icon, page in PAGES:
        is_active = st.session_state["analytics_page"] == page
        if st.button(
            f"{icon}  {page}",
            key=f"nav_{page}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state["analytics_page"] = page
            st.rerun()

    st.markdown("---")
    st.markdown("**System**")
    if st.button("🇰🇪 Go to Chat", use_container_width=True):
        st.switch_page("app.py")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.switch_page("pages/login.py")

    st.markdown("---")
    st.caption(
        f"Last updated: {datetime.now().strftime('%H:%M:%S')}"
    )

# ── Page header ────────────────────────────────────────────────────────────────
current_page = st.session_state["analytics_page"]
current_icon = next(i for i, p in PAGES if p == current_page)

st.markdown(f"""
<div style="background:linear-gradient(135deg,#006600 0%,#cc0000 100%);
color:white;padding:1rem 1.5rem;border-radius:10px;margin-bottom:1.5rem;
display:flex;align-items:center;gap:12px;">
    <span style="font-size:1.8rem">{current_icon}</span>
    <div>
        <h2 style="margin:0;font-size:1.3rem">{current_page}</h2>
        <p style="margin:0;opacity:0.85;font-size:0.82rem">
            Kenya MSME Advisor — Researcher Analytics
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# PAGE 1 — OVERVIEW
# ==============================================================================
if current_page == "Overview":
    if not rows:
        st.warning("No data yet. Start the chatbot and ask some questions.")
        st.stop()

    # KPI cards
    kpis = [
        ("Total Q&As",        total,         "Questions answered"),
        ("Sessions",          sessions,      "Unique user sessions"),
        ("Avg Response",      f"{avg_time}s","Time to generate answer"),
        ("Avg Answer",        f"{avg_words}w","Words per response"),
        ("Fastest",           f"{min(times):.1f}s" if times else "N/A", "Best response time"),
        ("Slowest",           f"{max(times):.1f}s" if times else "N/A", "Longest response"),
    ]
    cols = st.columns(6)
    for col, (label, value, caption) in zip(cols, kpis):
        with col:
            st.markdown(f"""
            <div class="kpi-box">
                <div class="kpi-value">{value}</div>
                <div class="kpi-label">{label}</div>
                <div style="font-size:0.7rem;color:#999">{caption}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Quick summary charts side by side
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Top Topics**")
        for topic, count in topics.most_common(5):
            pct = count / total * 100
            st.markdown(f"`{pct:.0f}%` {topic}")
            st.progress(pct / 100)

    with col2:
        st.markdown("**Languages Used**")
        for lang, count in languages.most_common():
            pct   = count / total * 100
            label = lang_labels.get(lang, lang)
            st.markdown(f"`{pct:.0f}%` {label}")
            st.progress(pct / 100)

    with col3:
        st.markdown("**Response Speed**")
        st.markdown(f"`{fast/total*100:.0f}%` ⚡ Fast (under 10s)")
        st.progress(fast / total if total else 0)
        st.markdown(f"`{medium/total*100:.0f}%` 🕐 Medium (10-30s)")
        st.progress(medium / total if total else 0)
        st.markdown(f"`{slow/total*100:.0f}%` 🐢 Slow (over 30s)")
        st.progress(slow / total if total else 0)

    st.markdown("---")
    st.markdown("**Daily Activity**")
    if dates:
        max_d = max(dates.values())
        d_cols = st.columns(min(len(dates), 7))
        for col, (date, count) in zip(d_cols, sorted(dates.items())):
            col.metric(date, count)

# ==============================================================================
# PAGE 2 — TOPIC ANALYSIS
# ==============================================================================
elif current_page == "Topic Analysis":
    st.markdown("**Distribution of questions across MSME topic categories**")
    st.caption(f"Based on {total} total questions logged")
    st.markdown("---")

    total_t = sum(topics.values())
    for topic, count in topics.most_common():
        pct = count / total_t * 100
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.markdown(f"**{topic}**")
        c2.markdown(f"`{count} questions`")
        c3.markdown(f"`{pct:.1f}%`")
        st.progress(pct / 100)
        st.markdown("")

    st.markdown("---")
    st.info(
        f"**Finding:** The most queried topic is "
        f"**{topics.most_common(1)[0][0]}** with "
        f"{topics.most_common(1)[0][1]} questions "
        f"({topics.most_common(1)[0][1]/total*100:.0f}% of total). "
        f"This is consistent with World Bank identification of "
        f"regulatory and financing barriers as top MSME challenges."
    )

# ==============================================================================
# PAGE 3 — LANGUAGE ANALYSIS
# ==============================================================================
elif current_page == "Language Analysis":
    st.markdown("**Language detection results across all conversations**")
    st.caption(f"System supports 6 Kenyan languages")
    st.markdown("---")

    total_l = sum(languages.values())
    for lang, count in languages.most_common():
        pct   = count / total_l * 100
        label = lang_labels.get(lang, lang)
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.markdown(f"**{label}**")
        c2.markdown(f"`{count} questions`")
        c3.markdown(f"`{pct:.1f}%`")
        st.progress(pct / 100)
        st.markdown("")

    st.markdown("---")
    detected_langs = len([l for l, c in languages.items() if l != "english"])
    st.info(
        f"**Finding:** English dominates at "
        f"{languages.get('english',0)/total_l*100:.0f}% of queries. "
        f"{detected_langs} non-English language(s) detected, "
        f"confirming multilingual usage among Kenyan MSME operators."
    )

# ==============================================================================
# PAGE 4 — RESPONSE TIMES
# ==============================================================================
elif current_page == "Response Times":
    st.markdown("**System performance — time from query to response**")
    st.markdown("---")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Average",  f"{avg_time}s")
    c2.metric("Fastest",  f"{min(times):.1f}s" if times else "N/A")
    c3.metric("Slowest",  f"{max(times):.1f}s" if times else "N/A")
    c4.metric("Median",
              f"{sorted(times)[len(times)//2]:.1f}s" if times else "N/A")

    st.markdown("---")
    st.markdown("**Speed Distribution**")

    for label, count, color, note in [
        ("⚡ Fast — under 10 seconds",  fast,   "#006600",
         "Ideal for mobile users"),
        ("🕐 Medium — 10 to 30 seconds", medium, "#ff9800",
         "Acceptable for advisory responses"),
        ("🐢 Slow — over 30 seconds",    slow,   "#cc0000",
         "May indicate complex queries or API latency"),
    ]:
        pct = count / total * 100 if total else 0
        st.markdown(f"**{label}**")
        st.markdown(f"{count} responses ({pct:.1f}%) — *{note}*")
        st.progress(pct / 100)
        st.markdown("")

    st.markdown("---")
    st.markdown("**Individual Response Times**")
    st.caption("All recorded response times")
    time_rows = [(r.get("time",""), r.get("question","")[:50],
                  float(r.get("response_time_seconds",0)))
                 for r in rows if r.get("response_time_seconds")]
    time_rows.sort(key=lambda x: x[2], reverse=True)
    for t, q, rt in time_rows[:20]:
        badge = "⚡" if rt < 10 else "🕐" if rt < 30 else "🐢"
        st.markdown(f"{badge} `{rt:.1f}s` — {q}...")

# ==============================================================================
# PAGE 5 — KNOWLEDGE SOURCES
# ==============================================================================
elif current_page == "Knowledge Sources":
    st.markdown("**Documents most frequently retrieved during conversations**")
    st.caption(f"From {len(all_sources)} total source retrievals")
    st.markdown("---")

    if src_count:
        top = src_count.most_common(20)
        max_count = top[0][1]
        for rank, (src, count) in enumerate(top, 1):
            short = src.replace("_", " ").replace(".pdf", "").replace(".txt", "")
            short = short[:55] + "…" if len(short) > 55 else short
            c1, c2, c3 = st.columns([1, 5, 1])
            c1.markdown(f"**#{rank}**")
            c2.markdown(f"`{short}`")
            c3.markdown(f"`{count}x`")
            st.progress(count / max_count)
    else:
        st.info("No source retrieval data available yet.")

# ==============================================================================
# PAGE 6 — EVALUATION RESULTS
# ==============================================================================
elif current_page == "Evaluation Results":
    st.markdown("**Structured evaluation of chatbot accuracy across 30 test questions**")
    st.markdown("---")

    if EVAL_FILE.exists():
        with open(EVAL_FILE, encoding="utf-8") as f:
            eval_rows = list(csv.DictReader(f))

        if eval_rows:
            scores    = [int(r["score"]) for r in eval_rows]
            avg_score = sum(scores) / len(scores)
            total_q   = len(eval_rows)
            excellent = sum(1 for s in scores if s == 5)
            good      = sum(1 for s in scores if s == 4)
            partial   = sum(1 for s in scores if s == 3)
            weak      = sum(1 for s in scores if s <= 2)
            rate      = (excellent + good) / total_q * 100

            # KPI row
            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("Questions",      total_q)
            k2.metric("Mean Score",     f"{avg_score:.2f}/5.0")
            k3.metric("Accuracy",       f"{avg_score/5*100:.1f}%")
            k4.metric("Good/Excellent", f"{rate:.0f}%")
            k5.metric("Perfect (5/5)",  excellent)

            st.markdown("---")

            col_e1, col_e2 = st.columns(2)

            with col_e1:
                st.markdown("**Score Distribution**")
                for label, count, icon in [
                    ("Excellent (5/5)", excellent, "🟢"),
                    ("Good (4/5)",      good,      "🔵"),
                    ("Partial (3/5)",   partial,   "🟡"),
                    ("Weak/Poor (≤2)",  weak,      "🔴"),
                ]:
                    pct = count / total_q * 100
                    c1, c2, c3 = st.columns([1, 3, 1])
                    c1.markdown(icon)
                    c2.markdown(f"**{label}**")
                    c3.markdown(f"`{count} ({pct:.0f}%)`")
                    st.progress(count / total_q)

            with col_e2:
                st.markdown("**Score by Category**")
                cat_scores = defaultdict(list)
                for r in eval_rows:
                    cat_scores[r["category"]].append(int(r["score"]))
                for cat, sc in sorted(cat_scores.items(),
                                      key=lambda x: -sum(x[1])/len(x[1])):
                    avg = sum(sc) / len(sc)
                    icon = "🟢" if avg >= 4.5 else "🔵" if avg >= 4.0 else "🟡"
                    c1, c2 = st.columns([4, 1])
                    c1.markdown(f"{icon} **{cat}**")
                    c2.markdown(f"`{avg:.1f}`")
                    st.progress(avg / 5)

            st.markdown("---")
            st.markdown("**All Test Questions and Scores**")
            filter_cat = st.selectbox(
                "Filter by category",
                ["All"] + sorted(set(r["category"] for r in eval_rows))
            )
            filtered = eval_rows if filter_cat == "All" else [
                r for r in eval_rows if r["category"] == filter_cat
            ]
            for r in filtered:
                score = int(r["score"])
                icon  = "🟢" if score == 5 else "🔵" if score == 4 \
                        else "🟡" if score == 3 else "🔴"
                with st.expander(
                    f"{icon} Q{r['id']:>2} [{r['category']}] "
                    f"Score: {score}/5 — {r['question'][:50]}..."
                ):
                    st.markdown(f"**Question:** {r['question']}")
                    st.markdown(f"**Score:** {score}/5 — **{r['rating']}**")
                    if r.get("answer"):
                        st.markdown("**Answer preview:**")
                        st.info(r["answer"][:300] + "...")

            st.markdown("---")
            with open(EVAL_FILE, "rb") as f:
                st.download_button(
                    "📥 Download Evaluation Results (CSV)",
                    data=f,
                    file_name="evaluation_results.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
    else:
        st.warning("No evaluation results yet.")
        st.info("Go to Admin Panel → Test Questions → Run Evaluation.")

# ==============================================================================
# PAGE 7 — CONVERSATIONS
# ==============================================================================
elif current_page == "Conversations":
    st.markdown("**Full conversation log with filters**")
    st.caption(f"{total} conversations recorded")
    st.markdown("---")

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filter_topic = st.selectbox(
            "Filter by topic",
            ["All"] + sorted(set(r["topic_category"] for r in rows))
        )
    with col_f2:
        filter_lang = st.selectbox(
            "Filter by language",
            ["All"] + sorted(set(r["language_detected"] for r in rows))
        )
    with col_f3:
        filter_date = st.selectbox(
            "Filter by date",
            ["All"] + sorted(set(r["date"] for r in rows), reverse=True)
        )

    filtered = rows
    if filter_topic != "All":
        filtered = [r for r in filtered if r["topic_category"] == filter_topic]
    if filter_lang != "All":
        filtered = [r for r in filtered if r["language_detected"] == filter_lang]
    if filter_date != "All":
        filtered = [r for r in filtered if r["date"] == filter_date]

    st.caption(f"Showing {len(filtered)} conversations")
    st.markdown("---")

    for r in filtered[::-1]:
        lang_label = lang_labels.get(r.get("language_detected", ""), "")
        with st.expander(
            f"🕐 {r.get('time','')} {r.get('date','')} | "
            f"{r.get('topic_category','')} | "
            f"{lang_label} | "
            f"{r.get('question','')[:45]}..."
        ):
            col_a, col_b = st.columns(2)
            col_a.markdown(f"**Topic:** {r.get('topic_category','')}")
            col_a.markdown(f"**Language:** {lang_label}")
            col_a.markdown(f"**Response time:** {r.get('response_time_seconds','')}s")
            col_b.markdown(f"**Words:** {r.get('answer_length_words','')}")
            col_b.markdown(f"**Session:** `{r.get('session_id','')}`")
            st.markdown("**Question:**")
            st.info(r.get("question", ""))
            st.markdown("**Answer:**")
            st.success(r.get("answer", "")[:500] + "...")

# ==============================================================================
# PAGE 8 — EXPORT DATA
# ==============================================================================
elif current_page == "Export Data":
    st.markdown("**Download research data for analysis**")
    st.markdown("---")

    st.markdown("### 📊 Conversation Log")
    st.caption(f"Full log of all {total} Q&A interactions")
    if LOG_FILE.exists():
        with open(LOG_FILE, "rb") as f:
            st.download_button(
                "📥 Download Conversation Log (CSV)",
                data=f,
                file_name="msme_conversations.csv",
                mime="text/csv",
                use_container_width=True,
            )

    st.markdown("---")
    st.markdown("### 🧪 Evaluation Results")
    if EVAL_FILE.exists():
        with open(EVAL_FILE, "rb") as f:
            st.download_button(
                "📥 Download Evaluation Results (CSV)",
                data=f,
                file_name="evaluation_results.csv",
                mime="text/csv",
                use_container_width=True,
            )
    else:
        st.info("No evaluation results yet.")

    st.markdown("---")
    st.markdown("### 📄 Summary Report")
    st.caption("Auto-generated text report for thesis findings")

    eval_summary = ""
    if EVAL_FILE.exists():
        with open(EVAL_FILE, encoding="utf-8") as f:
            eval_rows = list(csv.DictReader(f))
        if eval_rows:
            scores    = [int(r["score"]) for r in eval_rows]
            avg_score = sum(scores) / len(scores)
            excellent = sum(1 for s in scores if s == 5)
            good      = sum(1 for s in scores if s == 4)
            eval_summary = f"""
EVALUATION RESULTS
------------------
Questions tested:     {len(eval_rows)}
Mean score:           {avg_score:.2f}/5.0
Accuracy:             {avg_score/5*100:.1f}%
Good/Excellent rate:  {(excellent+good)/len(eval_rows)*100:.0f}%
Perfect scores (5/5): {excellent}
"""

    summary = f"""KENYA MSME ADVISOR — RESEARCH SUMMARY REPORT
Researcher: {st.session_state.get('user_name','Researcher')}
Generated:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Institution: Strathmore University — MSIT Thesis 2026
Author:      Kathembo Tsongo Dieudonne (112721)
=====================================================

SYSTEM USAGE STATISTICS
------------------------
Total Q&As logged:        {total}
Total sessions:           {sessions}
Average response time:    {avg_time}s
Average answer length:    {avg_words} words
Fastest response:         {min(times):.1f}s
Slowest response:         {max(times):.1f}s

TOPIC DISTRIBUTION
------------------
{chr(10).join(f'{topic:<30} {count:>3} questions ({count/total*100:.1f}%)' for topic, count in topics.most_common())}

LANGUAGE DISTRIBUTION
---------------------
{chr(10).join(f'{lang_labels.get(lang,lang):<20} {count:>3} questions ({count/total*100:.1f}%)' for lang, count in languages.most_common())}

RESPONSE TIME DISTRIBUTION
---------------------------
Fast (under 10s):    {fast:>3} ({fast/total*100:.1f}%)
Medium (10-30s):     {medium:>3} ({medium/total*100:.1f}%)
Slow (over 30s):     {slow:>3} ({slow/total*100:.1f}%)

TOP KNOWLEDGE SOURCES
---------------------
{chr(10).join(f'{rank:>2}. {src:<50} {count} uses' for rank, (src, count) in enumerate(src_count.most_common(10), 1))}

DAILY ACTIVITY
--------------
{chr(10).join(f'{date}: {count} questions' for date, count in sorted(dates.items()))}
{eval_summary}
=====================================================
END OF REPORT
"""
    if st.button("📊 Generate PDF Report",
                 type="primary",
                 use_container_width=True):
        with st.spinner("Building professional PDF report..."):
            from collections import defaultdict as dd
            cat_scores_pdf = dd(list)
            eval_file = BASE_DIR / "logs" / "evaluation_results.csv"
            avg_score_val="N/A"; accuracy_val="N/A"; rate_val="N/A"
            total_q_val=0; excellent_val=0; good_val=0
            partial_val=0; weak_val=0
            if eval_file.exists():
                with open(eval_file, encoding="utf-8") as ef:
                    er = list(csv.DictReader(ef))
                if er:
                    sc = [int(r["score"]) for r in er]
                    avg_s = sum(sc)/len(sc)
                    total_q_val   = len(er)
                    excellent_val = sum(1 for s in sc if s==5)
                    good_val      = sum(1 for s in sc if s==4)
                    partial_val   = sum(1 for s in sc if s==3)
                    weak_val      = sum(1 for s in sc if s<=2)
                    avg_score_val = f"{avg_s:.2f}"
                    accuracy_val  = f"{avg_s/5*100:.1f}"
                    rate_val = f"{(excellent_val+good_val)/total_q_val*100:.0f}"
                    for r in er:
                        cat_scores_pdf[r["category"]].append(int(r["score"]))
            pdf_data = {
                "total":      total,
                "sessions":   sessions,
                "avg_time":   avg_time,
                "avg_words":  avg_words,
                "times":      times if times else [0],
                "fast":       fast,
                "medium":     medium,
                "slow":       slow,
                "topics":     topics,
                "languages":  languages,
                "dates":      dates,
                "src_count":  src_count,
                "avg_score":  avg_score_val,
                "accuracy":   accuracy_val,
                "rate":       rate_val,
                "total_q":    total_q_val,
                "excellent":  excellent_val,
                "good":       good_val,
                "partial":    partial_val,
                "weak":       weak_val,
                "cat_scores": cat_scores_pdf,
                "author":     "Kathembo Tsongo Dieudonne (112721)",
                "generated":  datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            pdf_bytes = generate_pdf_report(pdf_data)
        fname = f"msme_report_{datetime.now().strftime('%Y%m%d')}.pdf"
        st.download_button(
            "📥 Download PDF Report Now",
            data=pdf_bytes,
            file_name=fname,
            mime="application/pdf",
            use_container_width=True,
        )


# ── RESEARCH DASHBOARD ──────────────────────────────────────────────────────
elif current_page == "Research":
    st.markdown("## 🔬 Kenya MSME Research Dashboard")
    st.caption("Kenya MSME AI Advisory Study · Strathmore University 2026")

    research_summary = get_research_summary()
    research_users = list_all_users()
    research_scores = get_all_prompt_scores()
    t1_users = [u for u in research_users if u.get("arm") == "T1"]
    t2_users = [u for u in research_users if u.get("arm") == "T2"]
    c_users  = [u for u in research_users if u.get("arm") == "C"]
    t1_ids   = {u["user_id"] for u in t1_users}
    t2_ids   = {u["user_id"] for u in t2_users}
    c_ids    = {u["user_id"] for u in c_users}

    # KPI row
    c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
    c1.metric("Total Participants", research_summary["total_users"])
    c2.metric("T1 Localised", research_summary["t1_count"])
    c3.metric("T2 Generic", research_summary["t2_count"])
    c4.metric("C Control", len(c_users))
    c5.metric("Baselines", research_summary["baseline_count"])
    c6.metric("Endlines", research_summary["endline_count"])
    c7.metric("Total Questions", research_summary["total_questions"])

    st.markdown("---")

    # Tabs inside Research section
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👥 Participants",
        "📋 Baseline",
        "📈 Outcomes",
        "🤖 AI Literacy",
        "⚖️ T1 vs T2"
    ])

    with tab1:
        st.markdown("### Participant Profiles")
        if not research_users:
            st.info("No participants yet.")
        else:
            counties   = _dd(int)
            biz_types  = _dd(int)
            for u in research_users:
                if u.get("county"):       counties[u["county"]] += 1
                if u.get("business_type"): biz_types[u["business_type"]] += 1
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**By County**")
                for k,v in sorted(counties.items(), key=lambda x:-x[1]):
                    st.markdown(f"- {k}: **{v}**")
            with col2:
                st.markdown("**By Business Type**")
                for k,v in sorted(biz_types.items(), key=lambda x:-x[1]):
                    st.markdown(f"- {k}: **{v}**")
            st.markdown("---")
            for u in sorted(research_users, key=lambda x: x.get("created_at",""), reverse=True):
                arm = "🟢 T1" if u.get("arm")=="T1" else "🔴 T2"
                bl  = "✅" if u.get("has_baseline") else "⏳"
                el  = "✅" if u.get("has_endline")  else "⏳"
                st.markdown(f"{arm} **{u['user_id'][:8]}** | "
                            f"County: {u.get('county','?')} | "
                            f"Questions: {u.get('total_questions',0)} | "
                            f"Baseline: {bl} | Endline: {el}")

    with tab2:
        st.markdown("### Baseline Survey Results")
        bl_users = [u for u in research_users if u.get("has_baseline")]
        if not bl_users:
            st.info("No baseline surveys yet.")
        else:
            st.metric("Baselines completed", len(bl_users))
            conf_fields = {
                "conf_tax":"KRA Tax","conf_register":"Registration",
                "conf_loan":"Loan Application","conf_nssf":"NSSF/SHIF",
                "conf_permit":"County Permits","conf_ai":"AI Self-Efficacy"
            }
            avgs = {f:[] for f in conf_fields}
            challenges = _dd(int)
            for u in bl_users:
                b = get_baseline(u["user_id"])
                if b:
                    for f in conf_fields:
                        v = b.get("responses",{}).get(f)
                        if v: avgs[f].append(int(v))
                    ch = b.get("responses",{}).get("primary_challenge")
                    if ch: challenges[ch] += 1
            st.markdown("**Average Baseline Confidence (1-5)**")
            cols = st.columns(3)
            for i,(f,label) in enumerate(conf_fields.items()):
                vals = avgs[f]
                avg  = round(sum(vals)/len(vals),2) if vals else 0
                cols[i%3].metric(label, f"{avg}/5")
            st.markdown("**Primary Challenges**")
            for ch,cnt in sorted(challenges.items(), key=lambda x:-x[1]):
                pct = int(cnt/len(bl_users)*100)
                st.markdown(f"- {ch}: **{cnt}** ({pct}%)")

    with tab3:
        st.markdown("### Endline Outcomes")
        el_users = [u for u in research_users if u.get("has_endline")]
        if not el_users:
            st.info("No endline surveys yet. Triggered after 5 questions.")
        else:
            st.metric("Endlines completed", len(el_users))
            conf_fields = {
                "conf_tax":"KRA Tax","conf_register":"Registration",
                "conf_loan":"Loan","conf_nssf":"NSSF",
                "conf_permit":"Permits","conf_ai":"AI Efficacy"
            }
            deltas = {f:[] for f in conf_fields}
            for u in el_users:
                b = get_baseline(u["user_id"])
                e = get_endline(u["user_id"])
                if b and e:
                    br = b.get("responses",{})
                    er = e.get("responses",{})
                    for f in conf_fields:
                        bv = br.get(f,0); ev = er.get(f,0)
                        if bv and ev: deltas[f].append(int(ev)-int(bv))
            st.markdown("**Confidence Change (Endline − Baseline)**")
            cols = st.columns(3)
            for i,(f,label) in enumerate(conf_fields.items()):
                vals = deltas[f]
                avg  = round(sum(vals)/len(vals),2) if vals else 0
                cols[i%3].metric(label, f"{avg:+.2f}", delta=avg)
            st.markdown("**Behavioural Outcomes**")
            outcomes = {
                "reg_change":"Business registered",
                "tax_change":"KRA filing improved",
                "loan_change":"Loan applied/approved",
                "nssf_change":"NSSF compliance improved"
            }
            for field, label in outcomes.items():
                pos = tot = 0
                for u in el_users:
                    e = get_endline(u["user_id"])
                    if e:
                        v = e.get("responses",{}).get(field,"")
                        tot += 1
                        if "Yes" in v: pos += 1
                if tot:
                    st.markdown(f"- **{label}**: {pos}/{tot} ({int(pos/tot*100)}%)")

    with tab4:
        st.markdown("### AI Literacy — Prompt Quality Trends")
        if not research_scores:
            st.info("No prompt scores yet.")
        else:
            all_s = [s["score"] for s in research_scores]
            avg   = round(sum(all_s)/len(all_s),2)
            st.metric("Overall Avg Prompt Quality", f"{avg}/10")
            dist = _dd(int)
            for s in research_scores: dist[s["score"]] += 1
            st.markdown("**Score Distribution**")
            for sv in range(1,11):
                cnt = dist.get(sv,0)
                bar = "█" * cnt
                st.markdown(f"**{sv}/10** {bar} ({cnt})")
            st.markdown("**Recent Questions**")
            for s in sorted(research_scores, key=lambda x:x.get("timestamp",""), reverse=True)[:10]:
                arm = "🟢 T1" if s.get("session_id") in t1_ids else "🔴 T2"
                st.markdown(f"{arm} Score **{s['score']}/10** | _{s.get('question','')[:80]}_")

    with tab5:
        st.markdown("### T1 vs T2 Comparison")
        t1_sc = [s["score"] for s in research_scores if s.get("session_id") in t1_ids]
        t2_sc = [s["score"] for s in research_scores if s.get("session_id") in t2_ids]
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🟢 T1 — Localised RAG")
            st.metric("Participants",    len(t1_users))
            st.metric("Total Questions", sum(u.get("total_questions",0) for u in t1_users))
            avg_t1 = round(sum(t1_sc)/len(t1_sc),2) if t1_sc else 0
            st.metric("Avg Prompt Score", f"{avg_t1}/10")
            st.metric("Baselines", sum(1 for u in t1_users if u.get("has_baseline")))
            st.metric("Endlines",  sum(1 for u in t1_users if u.get("has_endline")))
        with col2:
            st.markdown("### 🔴 T2 — Generic Claude")
            st.metric("Participants",    len(t2_users))
            st.metric("Total Questions", sum(u.get("total_questions",0) for u in t2_users))
            avg_t2 = round(sum(t2_sc)/len(t2_sc),2) if t2_sc else 0
            st.metric("Avg Prompt Score", f"{avg_t2}/10")
            st.metric("Baselines", sum(1 for u in t2_users if u.get("has_baseline")))
            st.metric("Endlines",  sum(1 for u in t2_users if u.get("has_endline")))
        if t1_sc and t2_sc:
            diff = round(avg_t1 - avg_t2, 2)
            st.markdown("---")
            if diff > 0:
                st.success(f"✅ T1 users score {diff} points higher than T2 on average.")
            elif diff < 0:
                st.warning(f"⚠️ T2 currently scores {abs(diff)} higher. More data needed.")
            else:
                st.info("T1 and T2 scoring equally. More data needed.")
