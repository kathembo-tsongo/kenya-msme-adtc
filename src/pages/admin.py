"""
admin.py — Kenya MSME Advisor: Complete Admin Panel
Access at: http://localhost:8501/admin
Password: msme2024admin
"""

import csv
import json
import pickle
import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from collections import Counter
import streamlit as st
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from auth import (verify_password, update_password, update_username,
                  update_profile, list_users, load_credentials)

BASE_DIR   = Path(__file__).parent.parent.parent
DB_DIR     = BASE_DIR / "knowledge_base"
DOCS_DIR   = BASE_DIR / "documents"
LOG_DIR    = BASE_DIR / "logs"
LOG_FILE   = LOG_DIR  / "conversations.csv"
EVAL_FILE  = LOG_DIR  / "evaluation_results.csv"
Q_FILE     = LOG_DIR  / "test_questions.csv"

st.set_page_config(
    page_title="MSME Advisor — Admin",
    page_icon="⚙️",
    layout="wide"
)

# ── Hide streamlit default nav ─────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebarNav"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ── Login gate ─────────────────────────────────────────────────────────────────
if not st.session_state.get("logged_in"):
    st.switch_page("pages/login.py")
if st.session_state.get("role") != "admin":
    st.error("❌ Access denied. Admin role required.")
    if st.button("← Back to Login"):
        st.session_state.clear()
        st.switch_page("pages/login.py")
    st.stop()

# ── Password protection (fallback for direct URL access) ──────────────────────
if "admin_auth" not in st.session_state:
    st.session_state["admin_auth"] = False

if not st.session_state["admin_auth"]:
    st.markdown("""
    <div style="background:#1a1a2e;color:white;padding:1.5rem;
    border-radius:10px;margin-bottom:2rem;text-align:center;">
        <h2 style="margin:0">⚙️ Admin Panel</h2>
        <p style="margin:0.3rem 0 0 0;opacity:0.7">
            Kenya MSME Advisor — System Administration
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.info("🔐 Restricted to System Administrators only.")
    pwd = st.text_input("Admin password", type="password")
    if st.button("Login", type="primary"):
        if pwd == "msme2024admin":
            st.session_state["admin_auth"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:0.5rem 0 1rem 0;'>
        <span style='font-size:1.1rem;font-weight:700;color:#1a1a2e'>
        ⚙️ Admin Panel
        </span><br>
        <span style='font-size:0.75rem;color:#888'>System Administration</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"👤 **{st.session_state.get('user_name','Admin')}**")
    st.caption("System Administrator")
    st.markdown("---")

    st.markdown("**Navigate to**")
    if st.button("🇰🇪 Operator Chat", use_container_width=True):
        st.switch_page("app.py")
    if st.button("📊 Analytics", use_container_width=True):
        st.switch_page("pages/analytics.py")

    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.switch_page("pages/login.py")

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:#1a1a2e;color:white;padding:1.2rem 1.5rem;
border-radius:10px;margin-bottom:1.5rem;">
    <h2 style="margin:0">⚙️ Kenya MSME Advisor — Admin Panel</h2>
    <p style="margin:0.3rem 0 0 0;opacity:0.7;font-size:0.9rem">
        System Administration — Full Access
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── Four tabs ──────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 System Status",
    "📄 Document Management",
    "📝 Test Questions",
    "🗂️ Data Management",
    "👤 User Management"
])

# ==============================================================================
# TAB 1 — SYSTEM STATUS
# ==============================================================================
with tab1:
    st.subheader("📊 System Status")

    # Knowledge base stats
    kb_ok     = (DB_DIR / "chunks.json").exists()
    vec_ok    = (DB_DIR / "vectorizer.pkl").exists()
    mat_ok    = (DB_DIR / "matrix.pkl").exists()

    chunk_count = 0
    doc_count   = 0
    if kb_ok:
        try:
            with open(DB_DIR / "chunks.json") as f:
                d = json.load(f)
            chunk_count = len(d["chunks"])
            doc_count   = len(set(m["filename"] for m in d["metadata"]))
        except Exception:
            pass

    # API key status
    env_file = BASE_DIR / ".env"
    api_ok   = False
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                key = line.split("=", 1)[1].strip()
                api_ok = key and key != "your_actual_key_here"

    # Display metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📦 Chunks",    f"{chunk_count:,}" if kb_ok else "Not built")
    m2.metric("📄 Documents", f"{doc_count:,}"   if kb_ok else "Not built")
    m3.metric("🔑 API Key",   "✅ Connected" if api_ok else "❌ Missing")
    m4.metric("🗄️ KB Status", "✅ Ready" if (kb_ok and vec_ok and mat_ok) else "⚠️ Incomplete")

    st.markdown("---")

    # Component status
    st.markdown("**Component Status:**")
    components = [
        ("Knowledge Base chunks.json",  kb_ok),
        ("TF-IDF Vectorizer",           vec_ok),
        ("Document Matrix",             mat_ok),
        ("Anthropic API Key",           api_ok),
        ("Conversation Log",            LOG_FILE.exists()),
        ("Evaluation Results",          EVAL_FILE.exists()),
        ("Test Questions CSV",          Q_FILE.exists()),
    ]
    for name, status in components:
        icon = "✅" if status else "❌"
        st.markdown(f"{icon} {name}")

    st.markdown("---")

    # Rebuild knowledge base
    st.subheader("🔄 Rebuild Knowledge Base")
    st.warning("⚠️ This will re-index all 245+ documents. Takes 3-5 minutes.")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        if st.button("🔄 Rebuild Knowledge Base", type="primary",
                     use_container_width=True):
            with st.spinner("Rebuilding knowledge base... please wait"):
                try:
                    ingest_script = BASE_DIR / "src" / "ingest.py"
                    result = subprocess.run(
                        ["python3", str(ingest_script)],
                        capture_output=True, text=True,
                        cwd=str(BASE_DIR)
                    )
                    if result.returncode == 0:
                        st.success("✅ Knowledge base rebuilt successfully!")
                        st.code(result.stdout[-500:] if result.stdout else "Done")
                    else:
                        st.error("❌ Rebuild failed")
                        st.code(result.stderr[-500:] if result.stderr else "Unknown error")
                except Exception as e:
                    st.error(f"Error: {e}")
    with col_r2:
        st.info(f"📁 Documents folder: `{DOCS_DIR}`\n\n"
                f"Add new PDFs or TXT files there, then rebuild.")

    st.markdown("---")

    # API Key management
    st.subheader("🔑 API Key Management")
    current_key = ""
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                current_key = line.split("=", 1)[1].strip()

    st.markdown(f"**Current key:** `{current_key[:12]}...`" if current_key else
                "**Current key:** Not set")
    new_key = st.text_input("New Anthropic API Key", type="password",
                             placeholder="sk-ant-...")
    if st.button("💾 Save API Key"):
        if new_key.startswith("sk-ant-"):
            content = env_file.read_text() if env_file.exists() else ""
            if "ANTHROPIC_API_KEY=" in content:
                lines = content.splitlines()
                lines = [f"ANTHROPIC_API_KEY={new_key}"
                         if l.startswith("ANTHROPIC_API_KEY=") else l
                         for l in lines]
                env_file.write_text("\n".join(lines))
            else:
                with open(env_file, "a") as f:
                    f.write(f"\nANTHROPIC_API_KEY={new_key}\n")
            st.success("✅ API key saved. Restart the app to apply.")
        else:
            st.error("Invalid key — must start with sk-ant-")

# ==============================================================================
# TAB 2 — DOCUMENT MANAGEMENT
# ==============================================================================
with tab2:
    st.subheader("📄 Document Management")

    # Count documents by type
    if DOCS_DIR.exists():
        all_files = list(DOCS_DIR.rglob("*"))
        pdfs  = [f for f in all_files if f.suffix.lower() == ".pdf"]
        txts  = [f for f in all_files if f.suffix.lower() == ".txt"]
        docxs = [f for f in all_files if f.suffix.lower() == ".docx"]

        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Total Files",  len(pdfs) + len(txts) + len(docxs))
        d2.metric("PDF Files",    len(pdfs))
        d3.metric("TXT Files",    len(txts))
        d4.metric("DOCX Files",   len(docxs))

        st.markdown("---")

        # Upload new document
        st.subheader("📤 Upload New Document")
        uploaded = st.file_uploader(
            "Upload PDF, TXT or DOCX document",
            type=["pdf", "txt", "docx"],
            help="Document will be saved to the documents folder"
        )
        if uploaded:
            save_path = DOCS_DIR / uploaded.name
            if save_path.exists():
                st.warning(f"⚠️ File `{uploaded.name}` already exists.")
            else:
                with open(save_path, "wb") as f:
                    f.write(uploaded.getbuffer())
                st.success(f"✅ Saved `{uploaded.name}` — rebuild knowledge "
                           f"base to index it.")

        st.markdown("---")

        # Document list
        st.subheader("📋 All Documents")
        search = st.text_input("🔍 Search documents", placeholder="e.g. kra, hustler, county")

        # Load chunk counts from knowledge base
        chunk_map = {}
        if kb_ok:
            try:
                with open(DB_DIR / "chunks.json") as f:
                    d = json.load(f)
                for m in d["metadata"]:
                    fn = m["filename"]
                    chunk_map[fn] = chunk_map.get(fn, 0) + 1
            except Exception:
                pass

        all_docs = sorted(pdfs + txts + docxs, key=lambda x: x.name)
        if search:
            all_docs = [f for f in all_docs
                        if search.lower() in f.name.lower()]

        st.caption(f"Showing {len(all_docs)} documents")

        for doc in all_docs:
            size_kb  = doc.stat().st_size / 1024
            chunks   = chunk_map.get(doc.name, 0)
            indexed  = "✅" if chunks > 0 else "⚠️ Not indexed"
            col_n, col_s, col_c, col_d = st.columns([4, 1, 1, 1])
            col_n.markdown(f"📄 `{doc.name}`")
            col_s.caption(f"{size_kb:.0f} KB")
            col_c.caption(f"{chunks} chunks" if chunks else indexed)
            if col_d.button("🗑️", key=f"del_{doc.parent.name}_{doc.name}",
                            help=f"Delete {doc.name}"):
                doc.unlink()
                st.warning(f"Deleted `{doc.name}` — rebuild to update index.")
                st.rerun()
    else:
        st.error("Documents folder not found.")

# ==============================================================================
# TAB 3 — TEST QUESTIONS
# ==============================================================================
with tab3:
    st.subheader("📝 Evaluation Test Questions")

    if Q_FILE.exists():
        with open(Q_FILE, encoding="utf-8") as f:
            q_rows = list(csv.DictReader(f))

        # Stats
        cats = Counter(r["category"] for r in q_rows)
        q1, q2 = st.columns(2)
        q1.metric("Total Questions", len(q_rows))
        q2.metric("Categories",      len(cats))

        st.markdown("**Questions by category:**")
        for cat, count in cats.most_common():
            st.markdown(f"- **{cat}**: {count} questions")

        st.markdown("---")

        # Add new question
        st.subheader("➕ Add New Test Question")
        with st.form("add_question"):
            new_id  = st.number_input("ID", value=len(q_rows) + 1, step=1)
            new_cat = st.selectbox("Category", options=sorted(cats.keys()))
            new_q   = st.text_area("Question", placeholder="Type your test question here...")
            new_mc  = st.text_input("Must contain (pipe-separated)",
                                     placeholder="KRA|VAT|tax")
            new_mn  = st.text_input("Must not contain (pipe-separated)",
                                     placeholder="I don't know|no information")
            submitted = st.form_submit_button("➕ Add Question")
            if submitted:
                if new_q and new_mc and new_mn:
                    with open(Q_FILE, "a", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(
                            f,
                            fieldnames=["id","category","question",
                                        "must_contain","must_not_contain"]
                        )
                        writer.writerow({
                            "id":             int(new_id),
                            "category":       new_cat,
                            "question":       new_q,
                            "must_contain":   new_mc,
                            "must_not_contain": new_mn,
                        })
                    st.success(f"✅ Question {new_id} added!")
                    st.rerun()
                else:
                    st.error("Please fill in all fields.")

        st.markdown("---")

        # View all questions
        st.subheader("📋 All Test Questions")
        filter_cat = st.selectbox(
            "Filter by category",
            ["All"] + sorted(cats.keys())
        )
        filtered = q_rows if filter_cat == "All" else [
            r for r in q_rows if r["category"] == filter_cat
        ]

        for r in filtered:
            with st.expander(
                f"Q{r['id']:02s} [{r['category']}] — {r['question'][:55]}..."
            ):
                st.markdown(f"**Question:** {r['question']}")
                st.markdown(f"**Must contain:** `{r['must_contain']}`")
                st.markdown(f"**Must not contain:** `{r['must_not_contain']}`")
                if st.button("🗑️ Delete", key=f"delq_{r['id']}"):
                    new_rows = [x for x in q_rows if x["id"] != r["id"]]
                    with open(Q_FILE, "w", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(
                            f,
                            fieldnames=["id","category","question",
                                        "must_contain","must_not_contain"]
                        )
                        writer.writeheader()
                        writer.writerows(new_rows)
                    st.rerun()

        st.markdown("---")

        # Download questions CSV
        with open(Q_FILE, "rb") as f:
            st.download_button(
                "📥 Download Test Questions (CSV)",
                data=f,
                file_name="test_questions.csv",
                mime="text/csv",
                use_container_width=True,
            )

        # Run evaluation button
        st.markdown("---")
        st.subheader("🧪 Run Evaluation")
        st.info("Running evaluation calls the API for each question. "
                "Takes 5-10 minutes for 30 questions.")
        if st.button("▶️ Run Evaluation Now", type="primary",
                     use_container_width=True):
            with st.spinner("Running evaluation... please wait"):
                try:
                    eval_script = BASE_DIR / "src" / "evaluate.py"
                    result = subprocess.run(
                        ["python3", str(eval_script)],
                        capture_output=True, text=True,
                        cwd=str(BASE_DIR)
                    )
                    if result.returncode == 0:
                        st.success("✅ Evaluation complete!")
                        st.code(result.stdout[-1000:] if result.stdout else "Done")
                    else:
                        st.error("❌ Evaluation failed")
                        st.code(result.stderr[-500:] if result.stderr else "Unknown error")
                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        st.warning("Test questions file not found. "
                   "Run the evaluation script first.")

# ==============================================================================
# TAB 4 — DATA MANAGEMENT
# ==============================================================================
with tab4:
    st.subheader("🗂️ Data Management")

    # Conversation log
    st.markdown("### 💬 Conversation Log")
    if LOG_FILE.exists():
        with open(LOG_FILE, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        st.metric("Total conversations logged", len(rows))

        col_dl, col_cl = st.columns(2)
        with col_dl:
            with open(LOG_FILE, "rb") as f:
                st.download_button(
                    "📥 Download Conversation Log (CSV)",
                    data=f,
                    file_name="msme_conversations.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
        with col_cl:
            if st.button("🗑️ Clear Conversation Log",
                         use_container_width=True):
                with open(LOG_FILE, "w", newline="",
                          encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=[
                        "timestamp","date","time","session_id",
                        "question_number","language_detected","question",
                        "answer","sources","response_time_seconds",
                        "answer_length_words","topic_category","had_summary_card"
                    ])
                    writer.writeheader()
                st.success("✅ Conversation log cleared.")
                st.rerun()
    else:
        st.info("No conversation log found yet.")

    st.markdown("---")

    # Evaluation results
    st.markdown("### 🧪 Evaluation Results")
    if EVAL_FILE.exists():
        with open(EVAL_FILE, encoding="utf-8") as f:
            eval_rows = list(csv.DictReader(f))
        scores    = [int(r["score"]) for r in eval_rows]
        avg_score = sum(scores) / len(scores) if scores else 0
        st.metric("Questions evaluated", len(eval_rows))
        st.metric("Average score",       f"{avg_score:.2f}/5.0")

        with open(EVAL_FILE, "rb") as f:
            st.download_button(
                "📥 Download Evaluation Results (CSV)",
                data=f,
                file_name="evaluation_results.csv",
                mime="text/csv",
                use_container_width=True,
            )
    else:
        st.info("No evaluation results yet. Run evaluation from Tab 3.")

    st.markdown("---")

    # Backup
    st.markdown("### 💾 Backup System Data")
    if st.button("📦 Create Backup", use_container_width=True):
        backup_dir = BASE_DIR / "backups"
        backup_dir.mkdir(exist_ok=True)
        timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"backup_{timestamp}"
        backup_path.mkdir(exist_ok=True)

        backed = []
        for src in [LOG_FILE, EVAL_FILE, Q_FILE]:
            if src.exists():
                shutil.copy(src, backup_path / src.name)
                backed.append(src.name)

        if backed:
            st.success(f"✅ Backed up: {', '.join(backed)} → "
                       f"`backups/backup_{timestamp}/`")
        else:
            st.warning("No files found to back up.")

    st.markdown("---")

    # System info
    st.markdown("### ℹ️ System Information")
    st.code(f"""
Kenya MSME Advisor — System Information
========================================
Base directory:     {BASE_DIR}
Documents folder:   {DOCS_DIR}
Knowledge base:     {DB_DIR}
Logs folder:        {LOG_DIR}
App version:        1.0.0
Built:              May 2026
Author:             Kathembo Tsongo Dieudonne (112721)
Institution:        Strathmore University
""")

# ==============================================================================
# TAB 5 — USER MANAGEMENT
# ==============================================================================
with tab5:
    st.subheader("👤 User Management")
    st.caption("Change usernames, passwords and profiles without touching the code.")

    current_user = st.session_state.get("username", "admin")

    col1, col2 = st.columns(2)

    # ── Change own password ────────────────────────────────────────────────────
    with col1:
        st.markdown("### 🔑 Change Your Password")
        with st.form("change_password"):
            old_pwd  = st.text_input("Current password", type="password")
            new_pwd  = st.text_input("New password",     type="password",
                                     help="At least 6 characters")
            conf_pwd = st.text_input("Confirm new password", type="password")
            if st.form_submit_button("Update Password", type="primary",
                                     use_container_width=True):
                if not old_pwd or not new_pwd or not conf_pwd:
                    st.error("Please fill in all fields.")
                elif not verify_password(current_user, old_pwd):
                    st.error("❌ Current password is incorrect.")
                elif new_pwd != conf_pwd:
                    st.error("❌ New passwords do not match.")
                elif len(new_pwd) < 6:
                    st.error("❌ Password must be at least 6 characters.")
                else:
                    update_password(current_user, new_pwd)
                    st.success("✅ Password updated successfully.")

    # ── Update profile ─────────────────────────────────────────────────────────
    with col2:
        st.markdown("### 📋 Update Your Profile")
        creds   = load_credentials()
        my_info = creds["users"].get(current_user, {})
        with st.form("update_profile"):
            new_name  = st.text_input("Display name",
                                      value=my_info.get("name", ""))
            new_email = st.text_input("Email address",
                                      value=my_info.get("email", ""))
            if st.form_submit_button("Save Profile", use_container_width=True):
                update_profile(current_user, new_name, new_email)
                st.session_state["user_name"] = new_name
                st.success("✅ Profile updated.")

    st.markdown("---")

    # ── Change username ────────────────────────────────────────────────────────
    st.markdown("### 🏷️ Change Your Username")
    with st.form("change_username"):
        confirm_pwd  = st.text_input("Confirm current password",
                                     type="password")
        new_username = st.text_input("New username",
                                     placeholder="e.g. john_admin")
        if st.form_submit_button("Update Username"):
            if not confirm_pwd or not new_username:
                st.error("Please fill in all fields.")
            elif not verify_password(current_user, confirm_pwd):
                st.error("❌ Password incorrect.")
            elif " " in new_username:
                st.error("❌ Username cannot contain spaces.")
            else:
                from auth import update_username
                if update_username(current_user, new_username):
                    st.session_state["username"] = new_username
                    st.success(
                        f"✅ Username changed to **{new_username}**. "
                        "Use this username next time you log in."
                    )
                else:
                    st.error("❌ Username already taken.")

    st.markdown("---")

    # ── All users ──────────────────────────────────────────────────────────────
    st.markdown("### 👥 All System Users")
    users = list_users()
    for u in users:
        role_icon = "⚙️" if u["role"] == "admin" else "🔬"
        with st.expander(
            f"{role_icon} **{u['name']}** — "
            f"@{u['username']} ({u['role']})"
        ):
            st.markdown(f"**Username:** `{u['username']}`")
            st.markdown(f"**Role:** {u['role']}")
            st.markdown(f"**Email:** {u.get('email','Not set')}")

            if u["username"] != current_user:
                st.markdown("**Reset password for this user:**")
                new_p = st.text_input(
                    "New password",
                    type="password",
                    key=f"reset_{u['username']}"
                )
                if st.button(
                    f"🔑 Reset {u['username']} password",
                    key=f"btn_{u['username']}"
                ):
                    if new_p and len(new_p) >= 6:
                        update_password(u["username"], new_p)
                        st.success(
                            f"✅ Password reset for {u['username']}."
                        )
                    else:
                        st.error("Minimum 6 characters required.")
