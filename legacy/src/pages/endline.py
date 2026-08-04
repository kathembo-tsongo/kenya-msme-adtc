"""
endline.py — Kenya MSME Advisor Follow-up Survey
Shown to MSME operators after 5+ sessions.
Measures post-intervention outcomes for Kenya MSME research study.
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from kenya_msme_db import save_endline, get_baseline, get_prompt_scores

st.set_page_config(
    page_title="Kenya MSME Advisor — Follow-up Survey",
    page_icon="🇰🇪",
    layout="centered"
)

st.markdown("""
<style>
[data-testid="stSidebarNav"] { display: none !important; }
header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

if not st.session_state.get("logged_in"):
    st.switch_page("pages/login.py")

session_id = st.session_state.get("session_id", "unknown")
baseline   = get_baseline(session_id)

st.markdown("""
<div style="background:linear-gradient(135deg,#006600,#cc0000);
color:white;padding:1.5rem;border-radius:12px;text-align:center;
margin-bottom:1.5rem;">
<h2 style="margin:0">🇰🇪 Quick Follow-up Survey</h2>
<p style="margin:0.5rem 0 0;opacity:0.9">
You have been using the Kenya MSME Advisor for a while.<br>
Tell us what has changed in your business — takes 3 minutes.
</p>
</div>
""", unsafe_allow_html=True)

# Show baseline reminder if available
if baseline:
    resp = baseline.get("responses", {})
    st.info(f"📋 When you started, your biggest challenge was: **{resp.get('primary_challenge', 'N/A')}**")

with st.form("endline_form"):

    st.markdown("### ✅ What Has Changed Since You Started Using This System?")

    st.markdown("**Business Registration**")
    reg_change = st.radio(
        "Has your business registration status changed?",
        [
            "Yes — I registered my business after using this system",
            "Yes — I completed a registration step I was stuck on",
            "No change yet — still working on it",
            "No change — my business was already registered",
            "No change — registration is not relevant for me",
        ],
        horizontal=False
    )

    st.markdown("**Tax & KRA**")
    tax_change = st.radio(
        "Has your relationship with KRA changed?",
        [
            "Yes — I filed my returns for the first time",
            "Yes — I registered for eTIMS after learning about it here",
            "Yes — I now understand my tax obligations better",
            "No change yet",
            "Not applicable",
        ],
        horizontal=False
    )

    st.markdown("**Financing & Loans**")
    loan_change = st.radio(
        "Has anything changed regarding financing for your business?",
        [
            "Yes — I applied for a loan/fund after using this system",
            "Yes — My loan application was approved",
            "Yes — I learned about financing options I did not know existed",
            "No change yet — still considering",
            "No change",
        ],
        horizontal=False
    )

    st.markdown("**Social Security**")
    nssf_change = st.radio(
        "Has your NSSF or SHIF compliance changed?",
        [
            "Yes — I registered for NSSF after learning here",
            "Yes — I started contributing after learning the requirements",
            "Yes — I now understand what I need to contribute",
            "No change",
            "Not applicable",
        ],
        horizontal=False
    )

    st.markdown("### 🎯 Your Confidence Now")
    st.caption("Rate your confidence from 1 (not confident) to 5 (very confident)")

    col_a, col_b = st.columns(2)
    with col_a:
        conf_tax_now = st.slider("Handling KRA tax requirements", 1, 5, 3)
        conf_register_now = st.slider("Registering/formalising your business", 1, 5, 3)
        conf_loan_now = st.slider("Applying for a business loan or fund", 1, 5, 3)
    with col_b:
        conf_nssf_now = st.slider("Managing NSSF and SHIF contributions", 1, 5, 3)
        conf_permit_now = st.slider("Getting county business permits", 1, 5, 3)
        conf_ai_now = st.slider("Using AI or digital tools for business", 1, 5, 3)

    st.markdown("### 📈 Business Performance")

    revenue_change = st.radio(
        "Has your business revenue changed since you started using this system?",
        [
            "Increased significantly",
            "Increased slightly",
            "About the same",
            "Decreased slightly",
            "Decreased significantly",
            "Too early to tell",
        ],
        horizontal=False
    )

    ai_continued = st.radio(
        "Will you continue using AI tools for your business?",
        [
            "Yes — definitely, I use it regularly now",
            "Yes — occasionally for specific questions",
            "Maybe — I need to learn more",
            "No — I prefer other sources of information",
        ],
        horizontal=False
    )

    recommend = st.radio(
        "Would you recommend this system to other business owners?",
        ["Yes — strongly", "Yes — with some reservations", "Not sure", "No"],
        horizontal=True
    )

    most_useful = st.selectbox(
        "Which topic was most useful to you?",
        [
            "Business Registration",
            "Tax & KRA",
            "Financing & Loans",
            "Social Security (NSSF/SHIF)",
            "County Permits",
            "Digital Finance (M-Pesa)",
            "Trade & Export",
            "Business Idea Validation",
            "AI Coaching Tips",
        ]
    )

    feedback = st.text_area(
        "Any other feedback? What would make this system more useful for you?",
        placeholder="Your feedback helps improve the system...",
        height=80
    )

    submitted = st.form_submit_button(
        "✅ Submit Follow-up Survey",
        type="primary",
        use_container_width=True
    )

    if submitted:
        # Calculate confidence changes vs baseline
        conf_changes = {}
        if baseline:
            br = baseline.get("responses", {})
            conf_changes = {
                "tax_change":      conf_tax_now - br.get("conf_tax", 0),
                "register_change": conf_register_now - br.get("conf_register", 0),
                "loan_change":     conf_loan_now - br.get("conf_loan", 0),
                "nssf_change":     conf_nssf_now - br.get("conf_nssf", 0),
                "permit_change":   conf_permit_now - br.get("conf_permit", 0),
                "ai_change":       conf_ai_now - br.get("conf_ai", 0),
            }

        responses = {
            "reg_change":       reg_change,
            "tax_change":       tax_change,
            "loan_change":      loan_change,
            "nssf_change":      nssf_change,
            "conf_tax":         conf_tax_now,
            "conf_register":    conf_register_now,
            "conf_loan":        conf_loan_now,
            "conf_nssf":        conf_nssf_now,
            "conf_permit":      conf_permit_now,
            "conf_ai":          conf_ai_now,
            "confidence_delta": conf_changes,
            "revenue_change":   revenue_change,
            "ai_continued":     ai_continued,
            "recommend":        recommend,
            "most_useful":      most_useful,
            "feedback":         feedback,
        }

        save_endline(session_id, responses)
        st.session_state["endline_done"] = True

        st.success("✅ Thank you! Your responses have been recorded.")
        st.balloons()
        st.info("Your feedback will help improve AI advisory tools for Kenyan businesses.")
        st.session_state["go_to_app"] = True
        st.rerun()

# Redirect after form submission
if st.session_state.get("go_to_app"):
    st.session_state.pop("go_to_app", None)
    if st.button("← Continue to Advisor", type="primary", use_container_width=True):
        st.switch_page("app.py")

st.markdown("---")
st.caption("🔒 All responses are stored securely and used only for academic research at Strathmore University.")
