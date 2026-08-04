"""
kenya_msme_db.py — Kenya MSME Research Database
Stores user profiles, baseline surveys, endline surveys,
and prompt quality trends for Kenya MSME research study.

Storage: JSON files in logs/kenya_msme_bd/ directory
- users/{phone_or_id}.json     — user profile + arm assignment
- baseline/{user_id}.json      — baseline survey responses
- endline/{user_id}.json       — endline survey responses  
- sessions/{session_id}.json   — per-session prompt quality scores
"""

import json
import uuid
from pathlib import Path
from datetime import datetime

BASE_DIR  = Path(__file__).parent.parent
DB_DIR    = BASE_DIR / "logs" / "kenya_msme_bd"
USERS_DIR = DB_DIR / "users"
BASE_SUR  = DB_DIR / "baseline"
END_SUR   = DB_DIR / "endline"
SESS_DIR  = DB_DIR / "sessions"

for d in [USERS_DIR, BASE_SUR, END_SUR, SESS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ── User Management ────────────────────────────────────────────────────────────

def create_user(session_id: str, arm: str = "T1") -> dict:
    """Create a new user profile."""
    user = {
        "user_id":        session_id,
        "arm":            arm,          # T1=localised, T2=generic, C=control
        "created_at":     datetime.now().isoformat(),
        "county":         None,
        "business_type":  None,
        "phone":          None,
        "has_baseline":   False,
        "has_endline":    False,
        "session_count":  0,
        "total_questions": 0,
    }
    save_user(user)
    return user


def save_user(user: dict):
    path = USERS_DIR / f"{user['user_id']}.json"
    path.write_text(json.dumps(user, indent=2))


def get_user(session_id: str) -> dict:
    path = USERS_DIR / f"{session_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


def get_or_create_user(session_id: str) -> dict:
    user = get_user(session_id)
    if not user:
        # Assign arm: rotate T1/T2/C for balanced groups
        all_users = list_all_users()
        t1 = sum(1 for u in all_users if u.get("arm") == "T1")
        t2 = sum(1 for u in all_users if u.get("arm") == "T2")
        c  = sum(1 for u in all_users if u.get("arm") == "C")
        # Assign to smallest group
        if t1 <= t2 and t1 <= c:
            arm = "T1"
        elif t2 <= t1 and t2 <= c:
            arm = "T2"
        else:
            arm = "C"
        user = create_user(session_id, arm)
    return user


def list_all_users() -> list:
    users = []
    for f in USERS_DIR.glob("*.json"):
        try:
            users.append(json.loads(f.read_text()))
        except Exception:
            pass
    return users


def update_user(session_id: str, updates: dict):
    user = get_user(session_id)
    if user:
        user.update(updates)
        save_user(user)


# ── Baseline Survey ────────────────────────────────────────────────────────────

def save_baseline(session_id: str, responses: dict):
    data = {
        "user_id":    session_id,
        "timestamp":  datetime.now().isoformat(),
        "responses":  responses,
    }
    path = BASE_SUR / f"{session_id}.json"
    path.write_text(json.dumps(data, indent=2))
    update_user(session_id, {"has_baseline": True,
                              "county": responses.get("county"),
                              "business_type": responses.get("business_type"),
                              "phone": responses.get("phone")})


def get_baseline(session_id: str) -> dict:
    path = BASE_SUR / f"{session_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


def has_baseline(session_id: str) -> bool:
    return (BASE_SUR / f"{session_id}.json").exists()


# ── Endline Survey ─────────────────────────────────────────────────────────────

def save_endline(session_id: str, responses: dict):
    data = {
        "user_id":   session_id,
        "timestamp": datetime.now().isoformat(),
        "responses": responses,
    }
    path = END_SUR / f"{session_id}.json"
    path.write_text(json.dumps(data, indent=2))
    update_user(session_id, {"has_endline": True})


def get_endline(session_id: str) -> dict:
    path = END_SUR / f"{session_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


def has_endline(session_id: str) -> bool:
    return (END_SUR / f"{session_id}.json").exists()


# ── Session Quality Tracking ───────────────────────────────────────────────────

def log_prompt_score(session_id: str, question: str, score: int):
    """Log prompt quality score for trend analysis."""
    path = SESS_DIR / f"{session_id}.json"
    if path.exists():
        data = json.loads(path.read_text())
    else:
        data = {"session_id": session_id, "scores": []}

    data["scores"].append({
        "timestamp": datetime.now().isoformat(),
        "question":  question[:100],
        "score":     score,
    })
    path.write_text(json.dumps(data, indent=2))


def get_prompt_scores(session_id: str) -> list:
    path = SESS_DIR / f"{session_id}.json"
    if path.exists():
        return json.loads(path.read_text()).get("scores", [])
    return []


def get_all_prompt_scores() -> list:
    all_scores = []
    for f in SESS_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            for s in data.get("scores", []):
                s["session_id"] = data["session_id"]
                all_scores.append(s)
        except Exception:
            pass
    return all_scores


# ── Research Summary ───────────────────────────────────────────────────────────

def get_research_summary() -> dict:
    users = list_all_users()
    t1 = [u for u in users if u.get("arm") == "T1"]
    t2 = [u for u in users if u.get("arm") == "T2"]

    baseline_count = sum(1 for u in users if u.get("has_baseline"))
    endline_count  = sum(1 for u in users if u.get("has_endline"))

    all_scores = get_all_prompt_scores()
    scores_t1  = []
    scores_t2  = []

    t1_ids = {u["user_id"] for u in t1}
    t2_ids = {u["user_id"] for u in t2}

    for s in all_scores:
        if s["session_id"] in t1_ids:
            scores_t1.append(s["score"])
        elif s["session_id"] in t2_ids:
            scores_t2.append(s["score"])

    c = [u for u in users if u.get("arm") == "C"]

    return {
        "total_users":    len(users),
        "t1_count":       len(t1),
        "t2_count":       len(t2),
        "c_count":        len(c),
        "baseline_count": baseline_count,
        "endline_count":  endline_count,
        "avg_score_t1":   round(sum(scores_t1)/len(scores_t1), 2) if scores_t1 else 0,
        "avg_score_t2":   round(sum(scores_t2)/len(scores_t2), 2) if scores_t2 else 0,
        "total_questions": sum(u.get("total_questions", 0) for u in users),
    }
