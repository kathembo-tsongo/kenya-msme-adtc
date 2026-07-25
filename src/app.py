"""
app.py — Kenya MSME Advisor: Operator Interface
The MSME Operator sees ONLY what they need:
  - Ask a question
  - Get an answer in their language
  - See sources cited
  - Sample questions to get started
  - Clear conversation

Run with: streamlit run src/app.py
"""

import json
import pickle
import time
import uuid
from pathlib import Path
import streamlit as st
from datetime import datetime
import anthropic
from sklearn.metrics.pairwise import cosine_similarity
import sys

BASE_DIR  = Path(__file__).parent.parent
DB_DIR    = BASE_DIR / "knowledge_base"
CONV_DIR  = BASE_DIR / "logs" / "conversations"
CONV_DIR.mkdir(parents=True, exist_ok=True)


# ── Conversation persistence ───────────────────────────────────────────────────
def save_conversation(session_id: str, history: list):
    """Save current conversation to disk."""
    if not history:
        return
    conv_file = CONV_DIR / f"{session_id}.json"
    data = {
        "session_id": session_id,
        "timestamp":  datetime.now().isoformat(),
        "title":      history[0]["user"][:50] if history else "New Conversation",
        "history":    history,
    }
    conv_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def load_all_conversations() -> list:
    """Load all saved conversations sorted by most recent."""
    convs = []
    for f in sorted(CONV_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime,
                    reverse=True):
        try:
            data = json.loads(f.read_text())
            convs.append(data)
        except Exception:
            pass
    return convs[:20]  # Show last 20 conversations


def load_conversation(session_id: str) -> list:
    """Load a specific conversation by session_id."""
    conv_file = CONV_DIR / f"{session_id}.json"
    if conv_file.exists():
        data = json.loads(conv_file.read_text())
        return data.get("history", [])
    return []

sys.path.insert(0, str(Path(__file__).parent))
from logger import log_conversation
from router import smart_retrieve
from coach import render_coach_panel, render_idea_validator
from kenya_msme_db import (get_or_create_user, update_user, has_baseline,
                            has_endline, log_prompt_score, get_prompt_scores)
from ask_generic import ask_generic_claude
from coach import score_prompt

st.set_page_config(
    page_title="Kenya MSME Business Advisor",
    page_icon="🇰🇪",
    layout="centered"
)

# ── Login gate ─────────────────────────────────────────────────────────────────
if not st.session_state.get("logged_in"):
    st.switch_page("pages/login.py")

# ── Session ID must exist before research checks ──────────────────────────────
import uuid as _uuid
if "session_id" not in st.session_state:
    st.session_state["session_id"]     = str(_uuid.uuid4())[:8]
if "history" not in st.session_state:
    st.session_state["history"]        = []
if "question_count" not in st.session_state:
    st.session_state["question_count"] = 0

# ── Research: Onboarding & Endline Triggers ────────────────────────────────────
_sid  = st.session_state["session_id"]
_user = get_or_create_user(_sid)

# Show baseline survey on first visit
if _user and not has_baseline(_sid) and not st.session_state.get("skip_baseline"):
    col_s1, col_s2 = st.columns([3,1])
    with col_s1:
        st.info("👋 Welcome! Please complete a quick 2-minute survey before starting.")
    with col_s2:
        if st.button("Skip Survey", key="skip_onboard"):
            st.session_state["skip_baseline"] = True
            st.rerun()
    if st.button("✅ Start Survey →", type="primary", key="go_onboard"):
        st.switch_page("pages/onboarding.py")
    st.stop()

# Show endline survey after 5 sessions
_qcount = st.session_state.get("question_count", 0)
if (_user and _qcount >= 5 and has_baseline(_sid)
        and not has_endline(_sid)
        and not st.session_state.get("skip_endline")):
    st.warning("📋 You have used this system 5 times. Please complete a quick follow-up survey.")
    col_e1, col_e2 = st.columns([3,1])
    with col_e1:
        if st.button("📝 Complete Follow-up Survey", type="primary", key="go_endline"):
            st.switch_page("pages/endline.py")
    with col_e2:
        if st.button("Later", key="skip_endline_btn"):
            st.session_state["skip_endline"] = True
            st.rerun()

# ── Control Group — no chat access during study ───────────────────────────────
if _user and _user.get("arm") == "C":
    st.markdown("""
    <div style="background:#fff8e1;border:2px solid #f9a825;
    border-radius:12px;padding:2rem;text-align:center;margin:2rem 0;">
    <h3 style="color:#e65100">📋 Research Participant — Control Group</h3>
    <p style="font-size:1.1rem;color:#555">
    Thank you for participating in the Kenya MSME AI Literacy Study.<br><br>
    As part of our research design, your group will receive access to the 
    AI advisory tool <strong>after the study period ends</strong>.<br><br>
    You will be notified when full access is available.
    </p>
    <p style="color:#888;font-size:0.85rem;margin-top:1rem">
    Strathmore University · Kenya MSME Research Study 2026
    </p>
    </div>
    """, unsafe_allow_html=True)
    if (has_baseline(_sid) and not has_endline(_sid)
            and not st.session_state.get("skip_endline")):
        st.info("📋 Please complete our follow-up survey.")
        if st.button("📝 Complete Follow-up Survey",
                     type="primary", key="c_endline"):
            st.switch_page("pages/endline.py")
    st.stop()

# ── Styles ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.header {
    background: linear-gradient(135deg, #006600 0%, #cc0000 100%);
    color: white;
    padding: 1.2rem 1.5rem;
    border-radius: 10px;
    margin-bottom: 1rem;
}
    margin-top: 0.4rem;
}
.lang-badge {
    background: #fff8e1;
    border: 1px solid #f9a825;
    color: #e65100;
    padding: 0.15rem 0.5rem;
    border-radius: 20px;
    font-size: 0.72rem;
    margin-top: 0.3rem;
    display: inline-block;
}
.disclaimer {
    font-size: 0.75rem;
    color: #888;
    text-align: center;
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid #eee;
}
.sample-header {
    font-size: 0.8rem;
    font-weight: 600;
    color: #444;
    margin-bottom: 0.3rem;
}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header" style="text-align: center;">
    <h2 style="margin:0">🇰🇪 Kenya MSME Business Advisor</h2>
    <p style="margin:0.3rem 0 0 0;opacity:0.9;font-size:0.9rem">
        AI-powered guidance — English (full) · Kiswahili (full) · Dholuo, Kikuyu, Kalenjin, Kamba (partial)
    </p>
</div>

""", unsafe_allow_html=True)


# ── Session ID ─────────────────────────────────────────────────────────────────
if "session_id"     not in st.session_state:
    st.session_state["session_id"]     = str(uuid.uuid4())[:8]
if "history"        not in st.session_state:
    st.session_state["history"]        = []
if "question_count" not in st.session_state:
    st.session_state["question_count"] = 0


# ── API key ────────────────────────────────────────────────────────────────────
def get_api_key():
    # 1. Try .env file (local development) - check first
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                key = line.split("=", 1)[1].strip()
                if key and key != "your_actual_key_here" and len(key) > 20:
                    return key
    # 2. Try environment variable
    import os
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    # 3. Try Streamlit secrets (cloud deployment)
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return None


# ── Knowledge base ─────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading knowledge base...")
def load_index():
    try:
        with open(DB_DIR / "vectorizer.pkl", "rb") as f:
            vectorizer = pickle.load(f)
        with open(DB_DIR / "matrix.pkl", "rb") as f:
            matrix = pickle.load(f)
        with open(DB_DIR / "chunks.json") as f:
            data = json.load(f)
        return vectorizer, matrix, data["chunks"], data["metadata"]
    except FileNotFoundError:
        return None, None, [], []


def retrieve(query, vectorizer, matrix, chunks, metadata, k=4):
    if vectorizer is None:
        return "", []
    qvec = vectorizer.transform([query])
    sims = cosine_similarity(qvec, matrix).flatten()
    top  = sims.argsort()[-k:][::-1]
    ctx_parts, sources = [], []
    for i in top:
        if sims[i] > 0.01:
            ctx_parts.append(chunks[i])
            src = metadata[i].get("filename", "Unknown")
            if src not in sources:
                sources.append(src)
    return "\n\n---\n\n".join(ctx_parts), sources


# ── Language detection ─────────────────────────────────────────────────────────
def detect_language(text: str) -> str:
    t = text.lower()
    scores = {
        "dholuo":    sum(1 for w in ["ere","kaka","nyalo","tero","chandruok",
                                      "osiep","awuon","bende","adhi","ohala"]
                         if w in t),
        "kikuyu":    sum(1 for w in [
                             "niwega","niguo","ndungata","ngwataniro",
                             "murata","niwahota","thogora","mboroto",
                             "gukora","guika","mahiu","mucii","murimi",
                             "ngumo","ugaruruku","thimu","kirigo",
                         ] if w in t),
        "kalenjin":  sum(1 for w in ["amun","mising","tugul","kamusto","nebo"]
                         if w in t),
        "kamba":     sum(1 for w in [
                             "mwi aseo","mwi","aseo","kwata","mwende",
                             "mwethya","mwatu","nesa","niki","ndeto",
                             "muthanga","ngwatanio","muunda","musyi",
                             "mbesa","utunga","utethya","niwe","niko",
                             "mawio","nthini","mwaki","muuo","kiveti",
                         ] if w in t),
        "kiswahili": sum(1 for w in ["biashara","kodi","ushuru","mkopo","akiba",
                                      "benki","leseni","usajili","nina","nataka",
                                      "niambie","ninaweza","pesa","shilingi",
                                      "malipo","habari","hustler","jinsi",
                                      "naweza","kuanza","ndiyo","lakini",
                                      "hapa","kama","yangu","yako","wako",
                                      "kwamba","hivyo","pia","zaidi","sasa",
                                      "tafadhali","asante","karibu","pamoja",
                                      "kuhusu","kutoka","kwenye","katika"]
                         if w in t),
    }
    best  = max(scores, key=scores.get)
    # For indigenous languages, even 1 word match is enough
    if scores[best] >= 1 and best not in ["kiswahili", "english"]:
        return best
    return best if scores[best] >= 2 else "english"


LANG_DISPLAY = {
    "english":   "🇬🇧 English",
    "kiswahili": "🇰🇪 Kiswahili",
    "dholuo":    "🐟 Dholuo",
    "kikuyu":    "🏔️ Kikuyu",
    "kalenjin":  "🏃 Kalenjin",
    "kamba":     "🎨 Kamba",
}

LANG_INSTRUCTIONS = {
    "kiswahili": "Jibu kwa Kiswahili kamili. Tumia maneno rahisi.",
    "dholuo":    "Greet briefly in Dholuo ('Amosi!') then answer fully in Kiswahili.",
    "kikuyu":    "Greet briefly in Kikuyu ('Niwega!') then answer fully in Kiswahili.",
    "kalenjin":  "Acknowledge briefly then answer fully in Kiswahili.",
    "kamba":     "Acknowledge briefly then answer fully in Kiswahili.",
    "english":   "Respond in clear, simple English.",
}


# ── Claude ─────────────────────────────────────────────────────────────────────
def ask_claude(api_key, question, context, history, lang):
    client  = anthropic.Anthropic(api_key=api_key)
    system  = f"""You are a knowledgeable and friendly business advisor
specialising in helping Micro, Small, and Medium Enterprises (MSMEs) in Kenya.

LANGUAGE: {LANG_INSTRUCTIONS.get(lang, LANG_INSTRUCTIONS['english'])}

You provide practical, accurate guidance on:
- Business registration and licensing (BRS, eCitizen, county permits)
- KRA tax obligations (VAT, income tax, PAYE, Turnover Tax, eTIMS)
- Access to financing (Hustler Fund, YEDF, WEF, SACCOs, banks, chama)
- Social security (NSSF, SHA, NITA)
- Trade and market access (EAC, COMESA, AfCFTA, e-commerce)
- Cultural business practices (chama, Jua Kali, community networks)
- Infrastructure and technology for MSMEs

RULES:
1. Base answers primarily on the CONTEXT documents below.
2. If context does not cover the question, say so and give general guidance.
3. Always be specific to Kenya — mention actual institutions, laws, processes.
4. Use simple, clear language any MSME owner can understand.
5. Always recommend consulting a lawyer or accountant for complex decisions.

CONTEXT FROM KNOWLEDGE BASE:
{context if context else "No specific documents found for this query."}"""

    messages = []
    for turn in history:
        messages += [
            {"role": "user",      "content": turn["user"]},
            {"role": "assistant", "content": turn["assistant"]},
        ]
    messages.append({"role": "user", "content": question})

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1200,
        system=system,
        messages=messages,
    )
    return response.content[0].text


# ── Load API key early (needed in sidebar) ───────────────────────────────────
api_key = get_api_key()

# ── Hide admin and analytics from sidebar using CSS ───────────────────────────
st.markdown("""
<style>
[data-testid="stSidebarNav"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar — operator focused ─────────────────────────────────────────────────
with st.sidebar:

    # ── Branding ───────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="padding:0.5rem 0 0.8rem 0;">
        <span style="font-size:1.3rem;font-weight:700;color:#006600">
        🇰🇪 MSME Advisor
        </span>
    </div>
    """, unsafe_allow_html=True)

    # ── New conversation ───────────────────────────────────────────────────────
    if st.button("＋  New Conversation",
                 use_container_width=True, type="primary"):
        if st.session_state.get("history"):
            save_conversation(
                st.session_state["session_id"],
                st.session_state["history"]
            )
        st.session_state["history"]        = []
        st.session_state["question_count"] = 0
        st.session_state["session_id"]     = str(uuid.uuid4())[:8]
        st.rerun()
    # ── Persistent conversations — like ChatGPT ──────────────────────────────
    current   = st.session_state.get("session_id", "")
    all_convs = load_all_conversations()

    if all_convs:
        st.markdown(
            "<div style='font-size:0.72rem;color:#888;"
            "margin:0.8rem 0 0.3rem 0;font-weight:600;"
            "text-transform:uppercase;letter-spacing:0.05em'>"
            "Conversations</div>",
            unsafe_allow_html=True
        )
        for conv in all_convs:
            sid   = conv.get("session_id", "")
            title = conv.get("title", "Conversation")
            short = title[:36] + "…" if len(title) > 36 else title
            is_active = sid == current
            if is_active:
                col_a, col_b = st.columns([5, 1])
                col_a.markdown(
                    f"<div style='background:#e8f5e9;border-left:3px solid"
                    f" #006600;padding:6px 10px;border-radius:4px;"
                    f"font-size:0.82rem;'>"
                    f"▶ {short}</div>",
                    unsafe_allow_html=True
                )
                if col_b.button("🗑️", key=f"del_{sid}",
                                help="Delete this conversation"):
                    (CONV_DIR / f"{sid}.json").unlink(missing_ok=True)
                    st.session_state["history"]        = []
                    st.session_state["question_count"] = 0
                    st.session_state["session_id"]     = str(uuid.uuid4())[:8]
                    st.rerun()
            else:
                col_a, col_b = st.columns([5, 1])
                if col_a.button(f"💬 {short}", key=f"conv_{sid}",
                                use_container_width=True):
                    if st.session_state.get("history"):
                        save_conversation(current,
                                          st.session_state["history"])
                    st.session_state["history"]        = load_conversation(sid)
                    st.session_state["session_id"]     = sid
                    st.session_state["question_count"] = len(
                        st.session_state["history"])
                    st.rerun()
                if col_b.button("🗑️", key=f"del_{sid}",
                                help="Delete this conversation"):
                    (CONV_DIR / f"{sid}.json").unlink(missing_ok=True)
                    st.rerun()

    st.markdown("---")

    # ── Language selector ──────────────────────────────────────────────────────
    st.markdown("#### 🌍 Select Language")
    lang_choice = st.radio(
        "Choose your language",
        options=["English", "Kiswahili"],
        label_visibility="collapsed",
        horizontal=True,
    )
    if lang_choice == "Kiswahili":
        st.session_state["force_lang"] = "kiswahili"
    else:
        st.session_state["force_lang"] = None

    st.markdown("---")

    # ── Coach Mode toggle ──────────────────────────────────────────────────────
    st.markdown("#### 🎓 Coach Mode")
    coach_mode = st.toggle(
        "Enable AI Literacy Coach",
        key="coach_mode_toggle",
        value=st.session_state.get("coach_mode", False),
        help="Get prompt quality scores, follow-up suggestions, and lean innovation tips after each answer"
    )
    st.session_state["coach_mode"] = coach_mode
    if coach_mode:
        st.caption("✅ Coach active — you'll get AI literacy tips after each answer")
    
    # ── Business Idea Validator ────────────────────────────────────────────────
    with st.expander("💡 Validate a Business Idea"):
        st.session_state["show_idea_validator"] = True
        st.caption("👇 Scroll down to use the idea validator")

    st.markdown("---")

    st.markdown("---")

    # ── Quick topics ───────────────────────────────────────────────────────────
    st.markdown("#### 💡 Quick Topics")

    TOPICS = {
        "📋 Business Registration": [
            "How do I register a sole proprietorship in Kenya?",
            "What documents do I need to register a business?",
            "How much does business registration cost?",
        ],
        "💰 Financing & Loans": [
            "How do I apply for the Hustler Fund?",
            "What loans does the Youth Enterprise Development Fund offer?",
            "How can a women-owned business get the Women Enterprise Fund?",
            "What is a SACCO and how can it help my business?",
        ],
        "🏛️ Tax & KRA": [
            "What taxes does a small business pay to KRA?",
            "What is Turnover Tax and who qualifies?",
            "When must I register for VAT?",
            "What is eTIMS and does my business need it?",
        ],
        "🪪 Permits & Licenses": [
            "What licenses do I need to open a shop?",
            "What is the Unified Business Permit in Nairobi?",
            "What happens if I operate without a county permit?",
        ],
        "👥 Social Security": [
            "How do I register for NSSF?",
            "What is SHIF and how does it replace NHIF?",
            "What is the NITA levy?",
        ],
        "📦 Trade & Export": [
            "How do I export my products to other countries?",
            "What is AfCFTA and how does it help Kenyan businesses?",
            "What does KEPROBA do for Kenyan exporters?",
        ],
        "📱 Digital Finance": [
            "How do I set up an M-Pesa Paybill for my business?",
            "What is the difference between Paybill and Buy Goods Till?",
            "How are mobile loan apps regulated in Kenya?",
        ],
    }

    for topic, questions in TOPICS.items():
        with st.expander(topic):
            for q in questions:
                if st.button(q, key=f"topic_{q}",
                             use_container_width=True):
                    st.session_state["prefill"] = q
                    st.rerun()

    st.markdown("---")

    # ── Recent questions this session ──────────────────────────────────────────
    if st.session_state.get("history"):
        st.markdown("#### 💬 Recent Questions")
        recent = st.session_state["history"][-5:][::-1]
        for i, turn in enumerate(recent):
            short = turn["user"][:45] + "…"                     if len(turn["user"]) > 45 else turn["user"]
            if st.button(f"↩ {short}", key=f"recent_{i}",
                         use_container_width=True):
                st.session_state["prefill"] = turn["user"]
                st.rerun()
        st.markdown("---")

    # ── Disclaimer ─────────────────────────────────────────────────────────────
    st.caption(
        "⚠️ General guidance only. Consult a qualified lawyer "
        "or accountant for complex decisions."
    )


# ── Load resources ─────────────────────────────────────────────────────────────
vectorizer, matrix, chunks, metadata = load_index()

# ── Chat history ───────────────────────────────────────────────────────────────
for turn in st.session_state["history"]:
    with st.chat_message("user"):
        st.write(turn["user"])
        if turn.get("lang") and turn["lang"] != "english":
            st.markdown(
                f"<div class='lang-badge'>"
                f"Detected: {LANG_DISPLAY.get(turn['lang'], turn['lang'])}"
                f"</div>",
                unsafe_allow_html=True,
            )
    with st.chat_message("assistant", avatar="🇰🇪"):
        st.write(turn["assistant"])

# ── Input ──────────────────────────────────────────────────────────────────────
prefill  = st.session_state.pop("prefill", "")
question = st.chat_input(
    "Ask about business registration, tax, financing..."
)
question = question or prefill

if question:
    if not api_key:
        st.error(
            "⚠️ The advisory service is temporarily unavailable. "
            "Please contact the system administrator."
        )
        st.stop()

    # Respect forced language from sidebar selector
    forced = st.session_state.get("force_lang")
    lang   = forced if forced else detect_language(question)
    st.session_state["question_count"] += 1

    with st.chat_message("user"):
        st.write(question)
        if lang != "english":
            st.markdown(
                f"<div class='lang-badge'>"
                f"Detected: {LANG_DISPLAY.get(lang, lang)}"
                f"</div>",
                unsafe_allow_html=True,
            )

    with st.chat_message("assistant", avatar="🇰🇪"):
        with st.spinner("Searching knowledge base..."):
            start  = time.time()
            _u     = get_or_create_user(st.session_state.get("session_id",""))
            _arm   = _u.get("arm", "T1") if _u else "T1"

            if _arm == "T2":
                # T2 — Generic Claude without RAG (comparison arm)
                context, sources, kb_used = "", [], "Generic"
                answer = ask_generic_claude(
                    api_key, question,
                    st.session_state["history"], lang
                )
            else:
                # T1 — Localised RAG system (treatment arm)
                context, sources, kb_used = smart_retrieve(question)
                answer = ask_claude(
                    api_key, question, context,
                    st.session_state["history"], lang
                )
            elapsed = time.time() - start

            # Log prompt quality score to kenya_msme_db
            _score = score_prompt(question)
            log_prompt_score(
                st.session_state.get("session_id",""),
                question,
                _score["score"]
            )
            # Update user question count
            update_user(
                st.session_state.get("session_id",""),
                {"total_questions": _u.get("total_questions",0)+1
                 if _u else 1}
            )

        st.write(answer)

    # Log silently — operator never sees this
    log_conversation(
        session_id      = st.session_state["session_id"],
        question_number = st.session_state["question_count"],
        language        = lang,
        question        = question,
        answer          = answer,
        sources         = sources,
        response_time   = elapsed,
        had_card        = False,
    )

    # Show coach panel if coach mode is on
    if st.session_state.get("coach_mode") and api_key:
        render_coach_panel(api_key, question, answer, lang)

    # Show coach panel if coach mode is on

    st.session_state["history"].append({
        "user":      question,
        "assistant": answer,
        "sources":   sources,
        "lang":      lang,
    })

    # Auto-save conversation after every message
    save_conversation(
        st.session_state["session_id"],
        st.session_state["history"]
    )

# ── Disclaimer ─────────────────────────────────────────────────────────────────
st.markdown(
    "<div class='disclaimer'>"
    "⚠️ This tool provides general guidance only. "
    "Consult a qualified lawyer or accountant for complex decisions.<br>"
    "Developed by Kathembo Tsongo Dieudonne — Strathmore University, 2026"
    "</div>",
    unsafe_allow_html=True,
)