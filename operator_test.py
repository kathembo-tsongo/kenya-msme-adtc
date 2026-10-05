"""Operator-style routing test: 28 realistic questions (English, Kiswahili, typos, short forms) through the pack router.

Run from the kenya-msme-adtc folder:  python3 operator_test.py [--db rafiki_pack_new.db]
For each question it shows the detected language (same rules as the app's Responder.detectLang), the route,
the topic or confidence, and what we would expect. It writes operator_test_results.csv for your records.
This does NOT touch ../kenya_msme_advisor/logs/test_questions.csv (the research instrument).
Model answers are not generated here -- only routing, which is what decides whether an operator gets a
verified answer, a document, advice or "I don't know".
"""
import argparse
import csv
import re
import sqlite3

import query_pack as qp

# (question, what we expect: a verified topic name, or a route kind)
QUESTIONS = [
    ("how much is the kra pin", "kra_pin"),
    ("do i need a permit to sell vegetables at the market", "license / unified_business_permit"),
    ("my employee wants maternity leave how many days", "maternity_paternity_leave"),
    ("how do i pay paye", "paye_remit"),
    ("what happens if i file vat late", "vat_penalty"),
    ("can i get a loan without security", "loan / hustler_fund_business"),
    ("how to register a business name", "registration"),
    ("how much nssf do i deduct for 20000 salary", "nssf"),
    ("i want to open a chemist what do i need", "pharmacy_license"),
    ("how do i get a till number", "mpesa_paybill_till"),
    ("is etims for small shops", "etims_general"),
    ("what is turnover tax", "turnover_tax"),
    ("how can i sell my products in uganda", "FACTUAL / keproba"),
    ("my business is making losses what should i do", "ADVISORY"),
    ("nifanyeje kupata kibali cha biashara", "license / unified_business_permit"),
    ("kodi ya mauzo ni kiasi gani", "turnover_tax"),
    ("nawezaje kupata mkopo wa vijana", "yedf"),
    ("mfanyakazi wangu anataka likizo ya uzazi siku ngapi", "maternity_paternity_leave"),
    ("nikichelewa kulipa VAT nitatozwa faini gani", "vat_penalty"),
    ("jinsi ya kusajili jina la biashara", "registration"),
    ("nataka kufungua duka la dawa", "pharmacy_license"),
    ("nawezaje kupata till number ya mpesa", "mpesa_paybill_till"),
    ("biashara yangu haipati faida nifanye nini", "ADVISORY"),
    ("NHIF bado ipo?", "shif_rate"),
    ("kra pin how", "kra_pin"),
    ("paye rates 2026", "paye_bands"),
    ("hustler fund limit", "hustler_fund_business"),
    ("hw do i regista biznes", "registration"),
    ("is it a must to register for my business before I start operating?", "start_business"),
    ("how do I start a small business here in kenya", "start_business"),
    ("nataka kuanza biashara", "start_business"),
    ("kiwango cha VAT", "vat"),
]

# --- same rules as Responder.detectLang in the app (keep in sync) ---
SW = set("""na ya kwa ni je gani nini vipi naweza ninahitaji jinsi wapi lini kuna hii hiyo sana mimi yangu nataka
tafadhali habari asante ninawezaje nitasajili kupata kuanza kufungua biashara mkopo leseni kodi nawezaje ninaweza
unaweza tunaweza wateja mteja duka dukani maduka bidhaa faida hasara mauzo zaidi kwangu kwenye au pia sasa kila bila
hadi kama lakini kuhusu nina sina nani namna ndio hapana pesa fedha mtaji soko sokoni kampuni kusajili kulipa ushuru
mshahara wafanyakazi mfanyakazi kibali jina shilingi kiasi ngapi gharama bei chakula kilimo mwaka mwezi siku wangu
yetu yako ili hivyo bado ipo kiwango viwango cha vya ipi""".split())
EN = set("the is how what do i my for to and can of a in are does should which where when hello hi thanks thank".split())


def words(t):
    return re.findall(r"[a-z0-9']+", t.lower())


def sw_family(t):
    return len(t) >= 5 and (t.startswith(("nawe", "ninawe", "tunawe", "unawe"))
                            or (t.startswith("ku") and t[-1] in "aeiou") or t.endswith("ni"))


def detect_lang(q):
    w = words(q)
    s = sum(1 for x in w if x in SW or sw_family(x))
    e = sum(1 for x in w if x in EN)
    if s != e:
        return "sw" if s > e else "en"
    long = [x for x in w if len(x) >= 3 and x.isalpha()]
    if len(long) < 3:
        return "en"
    return "sw" if sum(1 for x in long if x[-1] in "aeiou") * 10 >= len(long) * 7 else "en"


def field(r, *names):
    for n in names:
        v = r.get(n) if isinstance(r, dict) else getattr(r, n, None)
        if v not in (None, "", []):
            return v
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="rafiki_pack_new.db")
    args = ap.parse_args()
    db = sqlite3.connect(args.db)

    rows = []
    for i, (q, expect) in enumerate(QUESTIONS, 1):
        lang = detect_lang(q)
        r = qp.route(db, q, lang)
        kind = str(field(r, "kind", "route"))
        topic = str(field(r, "topic", "suggest"))
        conf = str(field(r, "confidence", "level"))
        hits = field(r, "hits")
        src = ""
        if hits:
            h = hits[0]
            src = str(h.get("source") if isinstance(h, dict) else getattr(h, "source", ""))[:40]
        exp_topics = [e.strip() for e in expect.split("/")]
        got = topic if kind in ("VERIFIED", "SUGGEST") else kind
        ok = any(e and (e == topic or kind.startswith(e)) for e in exp_topics)
        rows.append([i, q, lang, kind, topic, conf, src, expect, "OK" if ok else "CHECK"])
        print(f"{i:2} {'OK   ' if ok else 'CHECK'} [{lang}] {kind:<16} {got:<28} expect: {expect:<34} | {q}")

    with open("operator_test_results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["n", "question", "lang", "route", "topic", "confidence", "top_source", "expected", "result"])
        w.writerows(rows)
    n_ok = sum(1 for r in rows if r[-1] == "OK")
    print(f"\n{n_ok}/{len(rows)} routed as expected. Saved operator_test_results.csv")


if __name__ == "__main__":
    main()
