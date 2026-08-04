"""
onboarding.py — Kenya MSME Advisor Baseline Survey
Shown to MSME operators on their first visit.
Collects pre-intervention data for Kenya MSME research study.
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from kenya_msme_db import save_baseline, get_or_create_user

st.set_page_config(
    page_title="Kenya MSME Advisor — Welcome",
    page_icon="🇰🇪",
    layout="centered"
)

st.markdown("""
<style>
[data-testid="stSidebarNav"] { display: none !important; }
header { visibility: hidden; }
.survey-box {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    border-left: 4px solid #006600;
}
</style>
""", unsafe_allow_html=True)

if not st.session_state.get("logged_in"):
    st.switch_page("pages/login.py")

session_id = st.session_state.get("session_id", "unknown")

# Header
st.markdown("""
<div style="background:linear-gradient(135deg,#006600,#cc0000);
color:white;padding:1.5rem;border-radius:12px;text-align:center;
margin-bottom:1.5rem;">
<h2 style="margin:0">🇰🇪 Welcome to Kenya MSME Advisor</h2>
<p style="margin:0.5rem 0 0;opacity:0.9">
Before you start, please answer 6 quick questions.<br>
This helps us understand how AI tools help Kenyan businesses.
</p>
</div>
""", unsafe_allow_html=True)

st.caption("⏱ Takes about 2 minutes · Your answers are confidential · Used for research only")

with st.form("baseline_form"):

    st.markdown("###  About You and Your Business")

    col1, col2 = st.columns(2)
    with col1:
        county = st.selectbox("Which county is your business in?", [
            "Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret/Uasin Gishu",
            "Kiambu", "Machakos", "Meru", "Kakamega", "Nyeri",
            "Kericho", "Garissa", "Malindi", "Other"
        ])
    with col2:
        business_type = st.selectbox("What type of business do you run?", [
            "Retail shop / Duka",
            "Food & Beverages (mama mboga, restaurant, catering)",
            "Jua Kali / Artisan / Repair",
            "Transport / Boda boda",
            "Agriculture / Farming",
            "Professional services (salon, tailoring, etc.)",
            "Technology / Digital services",
            "Trading / Import-Export",
            "Other"
        ])

    employees = st.radio(
        "How many people work in your business (including yourself)?",
        ["Just me", "2-5 people", "6-10 people", "More than 10"],
        horizontal=True
    )

    st.markdown("### 💰 Business Registration & Finance")

    registered = st.radio(
        "Is your business formally registered? (BRS, eCitizen, county permit)",
        ["Yes, fully registered", "Partially registered", "Not registered yet", "I don't know"],
        horizontal=False
    )

    loan_applied = st.radio(
        "Have you ever applied for a business loan or fund? (Hustler Fund, bank, SACCO, etc.)",
        ["Yes, and I was approved", "Yes, but I was rejected", "No, I have never applied", "I didn't know I could apply"],
        horizontal=False
    )

    st.markdown("### Your Confidence Level")
    st.caption("Rate your confidence from 1 (not at all confident) to 5 (very confident)")

    col_a, col_b = st.columns(2)
    with col_a:
        conf_tax = st.slider(
            "Handling KRA tax requirements",
            1, 5, 2,
            help="VAT, income tax, PAYE, eTIMS"
        )
        conf_register = st.slider(
            "Registering or formalising your business",
            1, 5, 2
        )
        conf_loan = st.slider(
            "Applying for a business loan or fund",
            1, 5, 2
        )
    with col_b:
        conf_nssf = st.slider(
            "Managing NSSF and SHIF contributions",
            1, 5, 2
        )
        conf_permit = st.slider(
            "Getting county business permits",
            1, 5, 2
        )
        conf_ai = st.slider(
            "Using AI or digital tools for business",
            1, 5, 2,
            help="AI self-efficacy baseline"
        )

    st.markdown("### 📱 Optional Contact (for follow-up research)")
    phone = st.text_input(
        "Phone number (optional — for follow-up survey in 3 months)",
        placeholder="07XX XXX XXX",
        help="We will send one follow-up SMS. You can decline."
    )

    primary_challenge = st.selectbox(
        "What is your biggest business challenge right now?",
        [
            "Getting financing / loans",
            "Understanding taxes and KRA",
            "Registering my business",
            "Finding customers",
            "Managing cash flow",
            "Understanding permits and licenses",
            "Growing / scaling my business",
            "Other"
        ]
    )

    submitted = st.form_submit_button(
        "✅ Start Using the Advisor →",
        type="primary",
        use_container_width=True
    )

    if submitted:
        responses = {
            "county":            county,
            "business_type":     business_type,
            "employees":         employees,
            "registered":        registered,
            "loan_applied":      loan_applied,
            "conf_tax":          conf_tax,
            "conf_register":     conf_register,
            "conf_loan":         conf_loan,
            "conf_nssf":         conf_nssf,
            "conf_permit":       conf_permit,
            "conf_ai":           conf_ai,
            "phone":             phone,
            "primary_challenge": primary_challenge,
        }
        save_baseline(session_id, responses)
        user = get_or_create_user(session_id)

        st.session_state["baseline_done"]     = True
        st.session_state["user_county"]       = county
        st.session_state["user_business"]     = business_type
        st.session_state["user_arm"]          = user.get("arm", "T1")
        st.session_state["primary_challenge"] = primary_challenge

        st.success("✅ Thank you! Taking you to the advisor now...")
        st.switch_page("app.py")

st.markdown("---")
st.caption("🔒 Your responses are stored securely and used only for academic research at Strathmore University.")
