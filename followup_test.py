"""Follow-up test: does the router connect a second question to the first? (core repo: kenya-msme-adtc)

Run from the kenya-msme-adtc folder:  python3 followup_test.py [--db rafiki_pack_new.db]
Each case is a two-turn conversation. The first question is routed normally; the second is routed with the first
as context (prev_topic / prev_query), the way the app does it. Shows where follow-ups already work and where the
app loses the thread -- the baseline for adding conversation memory.
"""
import argparse
import sqlite3

import query_pack as qp
from operator_test import detect_lang, field

# (first question, follow-up, what the follow-up should reach)
CASES = [
    ("what is the VAT rate", "what if I pay late?", "vat_penalty"),
    ("paye rates", "and when do I pay it?", "paye_remit"),
    ("what is turnover tax", "how much is it for 2 million sales?", "turnover_tax"),
    ("nssf rates", "what is the penalty for paying late?", "nssf_penalty"),
    ("how do I get a hustler fund loan", "what is the limit?", "hustler_fund_business"),
    ("kiwango cha VAT ni kiasi gani", "na nikichelewa kulipa?", "vat_penalty"),
    ("do I need a permit for a food business", "what about in Nairobi?", "unified_business_permit"),
    ("how many days is maternity leave", "and for the father?", "maternity_paternity_leave"),
    ("how do I start a small business here in kenya", "my business is for mangos", "start_business"),
    ("how do I register a business name", "how long does it take?", "registration"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="rafiki_pack_new.db")
    args = ap.parse_args()
    db = sqlite3.connect(args.db)
    ok = 0
    for i, (q1, q2, expect) in enumerate(CASES, 1):
        l1 = detect_lang(q1)
        r1 = qp.route(db, q1, l1)
        t1 = str(field(r1, "topic", "suggest"))
        l2 = detect_lang(q2)
        r2 = qp.route(db, q2, l2, prev_topic=t1 or None, prev_query=q1)
        kind, t2 = str(field(r2, "kind")), str(field(r2, "topic", "suggest"))
        hit = expect in (t2, t1 if kind.startswith("FOLLOW") else "")
        ok += hit
        print(f"{i:2} {'OK   ' if hit else 'LOST '} 1st: {t1 or field(r1, 'kind'):<26} 2nd: {kind:<14} {t2:<24}"
              f" expect {expect:<24} | {q1}  ->  {q2}")
    print(f"\n{ok}/{len(CASES)} follow-ups connected to the conversation.")


if __name__ == "__main__":
    main()
