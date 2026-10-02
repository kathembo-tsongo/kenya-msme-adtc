#!/usr/bin/env python3
"""
eval_pack.py -- run test questions and real ALFA operator questions through
query_pack.route() (the exact phone routing) and report what happens.

Inputs (defaults assume you run it from kenya-msme-adtc/):
  ../kenya_msme_advisor/logs/test_questions.csv   id, category, question, must_contain, must_not_contain
  ../kenya_msme_advisor/logs/conversations.csv    only question, language_detected, session_id,
                                                  topic_category are read

Rows in conversations.csv that are just the test questions (the harness logged
them, often with a "11. " prefix) are removed, so the ALFA set is real operators only.

Output: eval_routing.csv with a blank 'expected' and 'notes' column for labelling.
It contains participant questions -- keep it local, never commit it.

Usage:
    python3 eval_pack.py
    python3 eval_pack.py --show real       # print every real operator question and its route
"""
import argparse
import csv
import re
import sqlite3
import statistics
import time
from collections import Counter

import query_pack as qp

NUMBER_PREFIX = re.compile(r"^\s*\d+\.\s*")


def split_terms(s):
    s = (s or "").strip()
    if not s:
        return []
    for sep in ("|", ";"):
        if sep in s:
            return [x.strip().lower() for x in s.split(sep) if x.strip()]
    return [x.strip().lower() for x in s.split(",") if x.strip()]


def lang_of(value, question):
    v = (value or "").lower()
    if v.startswith("sw") or "swahili" in v:
        return "sw"
    if v.startswith("en"):
        return "en"
    w = set(qp.words(question))
    return "sw" if w & {"na", "ya", "kwa", "ni", "je", "gani", "nini", "vipi", "biashara", "naweza"} else "en"


# Equivalent wording accepted by the lenient score only. The test CSV is never edited.
# Each entry: expected word -> words that carry the same meaning in a correct answer.
EQUIV = {
    "license": ["licence", "permit", "certificate"],
    "fine": ["penalty", "penalties"],
    "regulation": ["regulated", "regulates", "regulator", "regulatory"],
    "buy goods": ["till"],
    "salary": ["salaries", "wage", "wages", "emoluments"],
}


def check(r, must, must_not):
    if not must and not must_not:
        return ""
    text = (r["answer"] or (r["hits"][0]["body"] if r["hits"] else "")).lower()
    missing = [m for m in must if m not in text]
    present = [m for m in must_not if m in text]
    if not missing and not present:
        return "PASS"
    # Lenient pass: every missing word has a listed equivalent in the answer (strict score unchanged).
    via = {m: next((e for e in EQUIV.get(m, []) if e in text), None) for m in missing}
    if not present and missing and all(via.values()):
        return "PASS~ " + ", ".join(f"{m}->{e}" for m, e in via.items())
    return "FAIL" + (f" missing={missing}" if missing else "") + (f" forbidden={present}" if present else "")


def outcome(r):
    s = r["kind"]
    if r.get("clarified"):
        s = "(clarified) " + s
    if r.get("suggest"):
        s += f" ({r['confidence']})"
    if r.get("followup"):
        s += f" + follow-up {r['followup']['confidence']}"
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="rafiki_pack.db")
    ap.add_argument("--tests", default="../kenya_msme_advisor/logs/test_questions.csv")
    ap.add_argument("--convs", default="../kenya_msme_advisor/logs/conversations.csv")
    ap.add_argument("--out", default="eval_routing.csv")
    ap.add_argument("--show", choices=["real", "fail", "weak"], action="append", default=[])
    args = ap.parse_args()
    db = sqlite3.connect(args.db)
    rows = []

    # ---- labelled test questions
    with open(args.tests, encoding="utf-8", newline="") as f:
        tests = list(csv.DictReader(f))
    test_qs = {t["question"].strip().lower() for t in tests}
    for t in tests:
        q = t["question"].strip()
        lang = lang_of("", q)
        t0 = time.perf_counter()
        r = qp.route(db, q, lang)
        r.update(set="test", id=t["id"], category=t.get("category", ""), language=lang, question=q,
                 ms=(time.perf_counter() - t0) * 1000,
                 check=check(r, split_terms(t.get("must_contain")), split_terms(t.get("must_not_contain"))))
        rows.append(r)

    # ---- real operator questions (test-harness copies and duplicates removed)
    removed_copies = 0
    seen, last_topic, last_query = set(), {}, {}
    with open(args.convs, encoding="utf-8", newline="") as f:
        for i, c in enumerate(csv.DictReader(f), 1):
            raw = (c.get("question") or "").strip()
            q = NUMBER_PREFIX.sub("", raw).strip()
            if not q:
                continue
            if q.lower() in test_qs:
                removed_copies += 1
                continue
            if q.lower() in seen:
                continue
            seen.add(q.lower())
            session = c.get("session_id", "")
            lang = lang_of(c.get("language_detected"), q)
            t0 = time.perf_counter()
            r = qp.route(db, q, lang, prev_topic=last_topic.get(session),
                         prev_query=last_query.get(session))
            r.update(set="alfa", id=f"c{i}", category=c.get("topic_category", ""), language=lang,
                     question=q, ms=(time.perf_counter() - t0) * 1000, check="")
            if r["topic"]:
                last_topic[session] = r["topic"]
            if r["kind"] not in ("CHAT", "APP_INFO", "NOT_UNDERSTOOD"):
                last_query[session] = q
            rows.append(r)

    # ---- write the labelling file
    cols = ["set", "id", "category", "language", "question", "outcome", "topic", "also_matched",
            "focus", "top_source", "check", "ms", "expected", "notes"]
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            top = r["hits"][0]["source"] if r["hits"] else (
                r["followup"]["hits"][0]["source"] if r.get("followup") and r["followup"]["hits"] else "")
            w.writerow(dict(set=r["set"], id=r["id"], category=r["category"], language=r["language"],
                            question=r["question"], outcome=outcome(r),
                            topic=r["topic"] or (f"suggest:{r['suggest']}" if r["suggest"] else ""),
                            also_matched=";".join(r["also_matched"]), focus=r["focus"],
                            top_source=top, check=r["check"], ms=f"{r['ms']:.1f}",
                            expected="", notes=""))

    # ---- summary
    for name in ("test", "alfa"):
        subset = [r for r in rows if r["set"] == name]
        print("=" * 70)
        label = "TEST set" if name == "test" else f"REAL OPERATOR set ({removed_copies} test-harness copies removed)"
        print(f"{label}: {len(subset)} questions {dict(Counter(r['language'] for r in subset))}")
        for k, n in Counter(outcome(r) for r in subset).most_common():
            print(f"  {n:>3}  {n / len(subset):>4.0%}  {k}")
        checks = [r["check"] for r in subset if r["check"]]
        if checks:
            print(f"  must_contain checks: {sum(c == 'PASS' for c in checks)}/{len(checks)} pass (strict)"
                  f"  |  {sum(c.startswith('PASS') for c in checks)}/{len(checks)} with listed equivalents")

    ms = [r["ms"] for r in rows]
    print("=" * 70)
    print(f"Laptop routing time: median {statistics.median(ms):.1f} ms, max {max(ms):.1f} ms")
    print(f"Wrote {args.out}")

    for kind in args.show:
        pick = {
            "real": lambda r: r["set"] == "alfa",
            "fail": lambda r: r["check"].startswith("FAIL"),
            "weak": lambda r: "WEAK" in outcome(r),
        }[kind]
        chosen = [r for r in rows if pick(r)]
        print("=" * 70)
        print(f"{kind.upper()} ({len(chosen)}):")
        for r in chosen:
            detail = r["check"] if kind == "fail" else (
                r["topic"] or (f"suggest:{r['suggest']}" if r["suggest"] else f"focus '{r['focus']}'"))
            print(f"  [{r['id']}] {outcome(r):<32} {detail:<24} {r['question'][:70]}")


if __name__ == "__main__":
    main()
