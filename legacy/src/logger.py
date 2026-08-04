"""
logger.py — Conversation Logger for Kenya MSME Advisor
Saves every question and answer to a CSV file for thesis analysis.
Tracks: timestamp, question, answer, language, sources, response time.
"""

import csv
import json
import time
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
LOG_DIR  = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "conversations.csv"

HEADERS = [
    "timestamp",
    "date",
    "time",
    "session_id",
    "question_number",
    "language_detected",
    "question",
    "answer",
    "sources",
    "response_time_seconds",
    "answer_length_words",
    "topic_category",
    "had_summary_card",
]


def detect_topic(question: str) -> str:
    """Categorize question into topic for thesis analysis."""
    q = question.lower()
    if any(w in q for w in ['register','registration','brs','ecitizen','incorporate']):
        return "Business Registration"
    elif any(w in q for w in ['tax','vat','paye','kra','turnover','etims','ushuru','kodi']):
        return "Taxation"
    elif any(w in q for w in ['loan','fund','finance','credit','sacco','hustler','yedf','wef','mkopo']):
        return "Financing"
    elif any(w in q for w in ['permit','license','county','nairobi','leseni']):
        return "Permits & Licenses"
    elif any(w in q for w in ['nssf','nhif','shif','nita','insurance','social']):
        return "Social Security"
    elif any(w in q for w in ['export','trade','afcfta','comesa','eac','market']):
        return "Trade & Markets"
    elif any(w in q for w in ['mpesa','m-pesa','digital','mobile','paybill']):
        return "Digital Finance"
    elif any(w in q for w in ['chama','jua kali','informal','culture','jamii']):
        return "Cultural Context"
    elif any(w in q for w in ['electricity','kplc','energy','road','infrastructure']):
        return "Infrastructure"
    elif any(w in q for w in ['skill','train','tvet','nita','worker','staff']):
        return "Human Capital"
    else:
        return "General Advisory"


def ensure_log_file():
    """Create log directory and CSV file with headers if not exists."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE.exists():
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS)
            writer.writeheader()


def log_conversation(
    session_id:      str,
    question_number: int,
    language:        str,
    question:        str,
    answer:          str,
    sources:         list,
    response_time:   float,
    had_card:        bool = False,
):
    """Log a single conversation turn to CSV."""
    ensure_log_file()

    now = datetime.now()
    row = {
        "timestamp":             now.isoformat(),
        "date":                  now.strftime("%Y-%m-%d"),
        "time":                  now.strftime("%H:%M:%S"),
        "session_id":            session_id,
        "question_number":       question_number,
        "language_detected":     language,
        "question":              question.replace("\n", " ").strip(),
        "answer":                answer[:500].replace("\n", " ").strip(),
        "sources":               " | ".join(sources) if sources else "none",
        "response_time_seconds": round(response_time, 2),
        "answer_length_words":   len(answer.split()),
        "topic_category":        detect_topic(question),
        "had_summary_card":      "yes" if had_card else "no",
    }

    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writerow(row)


def get_stats() -> dict:
    """
    Read the log file and return summary statistics for
    the sidebar analytics panel.
    """
    ensure_log_file()
    rows = []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except Exception:
        return {}

    if not rows:
        return {"total": 0}

    # Topic distribution
    topics = {}
    for r in rows:
        t = r.get("topic_category", "General")
        topics[t] = topics.get(t, 0) + 1

    # Language distribution
    languages = {}
    for r in rows:
        lang = r.get("language_detected", "english")
        languages[lang] = languages.get(lang, 0) + 1

    # Average response time
    times = []
    for r in rows:
        try:
            times.append(float(r["response_time_seconds"]))
        except (ValueError, KeyError):
            pass

    # Top topic
    top_topic = max(topics, key=topics.get) if topics else "N/A"

    return {
        "total":        len(rows),
        "topics":       dict(sorted(topics.items(),
                             key=lambda x: x[1], reverse=True)),
        "languages":    languages,
        "avg_time":     round(sum(times) / len(times), 1) if times else 0,
        "top_topic":    top_topic,
        "sessions":     len(set(r.get("session_id","") for r in rows)),
    }


def get_log_path() -> Path:
    """Return path to the log file."""
    ensure_log_file()
    return LOG_FILE
