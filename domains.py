#!/usr/bin/env python3
"""
domains.py -- the six application domains of the study (proposal, Section 1.6 / Table "domain-scope"),
and the rules that give every verified answer and every document chunk exactly one domain.

  registration     business names, companies, partnerships, KRA PIN as a registration step, IP
  compliance       county permits and licences, sector licences, standards, trade, procurement
  taxation         KRA taxes, returns, eTIMS, penalties
  social_security  NSSF, employment law, wages, leave, Housing Levy
  health_social    SHIF/SHA, health services, social protection, disability
  financing        loans, funds, SACCOs, banks, payments, insurance
  general          anything else (general business advice, surveys, culture): answered as
                   general advice, and reported separately -- it is outside the six domains

Chunks are tagged from their source path: the first SOURCE_RULES pattern that matches wins,
otherwise the default of their knowledge-base folder (KB_DEFAULT). Run the report to see the
result and the largest sources that fell back to their folder default:

    python3 domains.py --report                 # uses rafiki_pack.db
    python3 domains.py --report --db other.db
"""
import argparse
import re
import sqlite3
from collections import Counter, defaultdict

DOMAINS = ["registration", "compliance", "taxation", "social_security", "health_social", "financing"]
ALL_LABELS = DOMAINS + ["general"]

# Every verified answer (CANNED_ANSWERS topic in rag_server.py) -> its domain.
# build_pack.py stops with an error if a topic is missing here, so a new answer cannot go untagged.
TOPIC_DOMAIN = {
    # registration
    "registration": "registration", "start_business": "registration", "capital": "registration",
    "sole_prop_vs_limited": "registration", "sole_prop_to_llc": "registration",
    "sole_prop_llc_mistakes": "registration",
    # compliance
    "license": "compliance", "unified_business_permit": "compliance", "food_business_license": "compliance",
    "pharmacy_license": "compliance", "ca_license": "compliance", "relocation_county": "compliance",
    "no_permit_penalty": "compliance", "class_r_permit": "compliance", "keproba": "compliance",
    "afcfta": "compliance", "agpo": "compliance", "regulations_not_exhaustive": "compliance",
    # taxation
    "kra_pin": "taxation", "vat": "taxation", "vat_penalty": "taxation", "turnover_tax": "taxation",
    "paye_bands": "taxation", "paye_remit": "taxation", "etims_general": "taxation",
    "tcc_application": "taxation", "late_filing_penalty": "taxation", "barber_salon_taxes": "taxation",
    "compliance_software": "taxation",
    # social security and employment
    "nssf": "social_security", "nssf_penalty": "social_security", "nssf_registration": "social_security",
    "housing_levy": "social_security", "leave": "social_security",
    "maternity_paternity_leave": "social_security", "minimum_wage": "social_security",
    "probation_period": "social_security", "termination": "social_security",
    "employee_compliance_checklist": "social_security",
    # health and social services
    "shif_rate": "health_social",
    # financing
    "loan": "financing", "yedf": "financing", "wef": "financing", "hustler_fund_business": "financing",
    "sacco_vs_bank": "financing", "mpesa_paybill_till": "financing", "business_insurance": "financing",
}

# (pattern on the lower-case source path, domain). First match wins, so specific rules come first.
SOURCE_RULES = [
    # Background material, not operator guidance: research journals, skills and TVET reports, sector
    # statistics, strategic plans, climate policy. Checked first so a word like "ca_" or "finance"
    # in the name cannot pull it into one of the six domains.
    (r"tvet|journal|employability|skills|strategic_plan|masterplan|climate|unfccc|adaptation|"
     r"annual_report|market_structure|mobile_economy|sdgs|msme_day|_launch", "general"),
    (r"county.*(finance|fee|permit|licen)|(finance|fee|permit|licen).*county", "compliance"),
    (r"shif|social_health|\bsha\b|sha_|nhif|health_insurance|disabilit|ncpwd|social_protection|"
     r"social_assistance|inua_jamii|cash_transfer|older_person|elderly", "health_social"),
    (r"nssf|employment|labour|labor|wage|leave|wiba|work_injur|pension|retirement|rba_|"
     r"housing_levy|affordable_housing|occupational_safety|osha", "social_security"),
    (r"kra|tax|vat|paye|etims|itax|excise|turnover|finance_act|tcc", "taxation"),
    (r"brs|business_registration|registrar|companies_act|company|companies|business_name|"
     r"partnership|llp|incorporat|kipi|trademark|copyright|kecobo|ecitizen", "registration"),
    (r"loan|credit|fund|yedf|wef|uwezo|hustler|sacco|bank|cbk|microfinance|mfi|insurance|ira_|"
     r"mpesa|m-pesa|pochi|fintech|lending|grant|chama", "financing"),
    (r"permit|licen|kebs|standard|nema|environment|fire|food|pharma|ppb|poisons|keproba|export|"
     r"import|afcfta|trade|agpo|procure|tender|data_protection|odpc|communications_authority|"
     r"county", "compliance"),
]
_RULES = [(re.compile(p), d) for p, d in SOURCE_RULES]

# Fallback by knowledge-base folder (kb1 ... kb9), when no rule above matches.
KB_DEFAULT = {
    "kb1": "compliance",       # legal / regulatory
    "kb2": "taxation",         # tax / KRA
    "kb3": "financing",        # financing / credit
    "kb4": "social_security",  # social security / employment
    "kb5": "compliance",       # digital / trade
    "kb6": "general",          # county / geospatial data and surveys
    "kb7": "general",          # culture / context
    "kb8": "general",          # national policy
    "kb9": "general",
}


def kb_folder(kb, source=""):
    m = re.search(r"kb\d+", f"{kb} {source}".lower())
    return m.group(0) if m else ""


def chunk_domain(kb, source):
    """(domain, how) for one chunk: how is 'rule' or 'folder'."""
    s = (source or "").lower()
    for rx, d in _RULES:
        if rx.search(s):
            return d, "rule"
    return KB_DEFAULT.get(kb_folder(kb, source), "general"), "folder"


def check_topics(topics):
    """Topics with no domain (stops the pack build) and domains with no verified answer."""
    missing = sorted(t for t in topics if t not in TOPIC_DOMAIN)
    empty = [d for d in DOMAINS if d not in {TOPIC_DOMAIN[t] for t in topics if t in TOPIC_DOMAIN}]
    return missing, empty


# ---------------------------------------------------------------- report
def report(db_path):
    db = sqlite3.connect(db_path)
    cols = [r[1] for r in db.execute("PRAGMA table_info(chunks)")]
    if "domain" not in cols:
        raise SystemExit(f"{db_path} has no chunk domains: rebuild it with build_pack.py first.")
    total = db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    print(f"Pack: {db_path} | chunks: {total}\n")
    print(f"{'domain':<17}{'chunks':>8}{'share':>8}{'sources':>9}{'verified answers':>18}")
    topics = defaultdict(list)
    for t, d in db.execute("SELECT topic, domain FROM topic_domain"):
        topics[d].append(t)
    for d in ALL_LABELS:
        n, s = db.execute("SELECT COUNT(*), COUNT(DISTINCT source) FROM chunks WHERE domain = ?", (d,)).fetchone()
        print(f"{d:<17}{n:>8}{n / max(total, 1):>8.0%}{s:>9}{len(topics[d]):>18}")
    print("\nVerified answers by domain:")
    for d in DOMAINS:
        print(f"  {d}: {', '.join(sorted(topics[d])) or '(none)'}")

    print("\nLargest sources tagged only by their folder default (check these; add a rule if wrong):")
    rows = db.execute("SELECT source, kb, domain, COUNT(*) FROM chunks GROUP BY source "
                      "ORDER BY COUNT(*) DESC").fetchall()
    shown = 0
    for source, kb, domain, n in rows:
        if chunk_domain(kb, source)[1] == "folder":
            print(f"  {n:>5}  {domain:<16} {source}")
            shown += 1
            if shown == 40:
                break
    folder = sum(n for source, kb, _, n in rows if chunk_domain(kb, source)[1] == "folder")
    print(f"\n{folder} of {total} chunks ({folder / max(total, 1):.0%}) are tagged by folder default only.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--db", default="rafiki_pack.db")
    a = ap.parse_args()
    if a.report:
        report(a.db)
    else:
        ap.print_help()
