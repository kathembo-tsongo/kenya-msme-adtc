#!/usr/bin/env python3
"""
eval_testset.py -- route the 108 English and 108 Kiswahili test questions (eval/test_set.csv)
through query_pack.route(), the exact phone routing, and score the ROUTING stage:

  route      did the question go where it should?
               VERIFIED expected -> VERIFIED with the expected topic          (correct)
                                    SUGGEST of the expected topic             (suggested)
               FACTUAL expected  -> FACTUAL STRONG / PARTIAL / DIGEST         (answered)
                                    FACTUAL WEAK (no verified information)    (declined)
                                    SUGGEST of a verified topic               (suggested)
               anything else                                                  (wrong)
  source     for rows with an expected_source: is it among the top-3 passages? (retrieval hit)
  parity     do the English and Kiswahili versions of a question get the same route and topic?
             (the cross-lingual consistency the proposal measures)

Answer quality (must_contain / must_not_contain) needs the model's answers, so it is scored
later from the phone's evaluation log; this script checks everything before the model.

Dev / test split: odd-numbered rows (1st, 3rd, ...) are the DEV half, used for tuning the router;
even-numbered rows are the TEST half, held out and only reported. Tune with --split dev; report
both halves in the thesis, and say which one was used for tuning.

Usage (from kenya-msme-adtc/):
    python3 eval/eval_testset.py                       # summary
    python3 eval/eval_testset.py --split dev --show wrong   # tune on the dev half only
    python3 eval/eval_testset.py --out eval/routing_results.csv
"""
import argparse
import csv
import os
import sqlite3
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import query_pack as qp  # noqa: E402

DOMAINS = ["registration", "compliance", "taxation", "social_security", "health_social", "financing"]
OUTCOMES = ["correct", "suggested", "answered", "declined", "wrong"]


def outcome(row, r):
    exp, topic = row["expected_route"].strip().upper(), row["expected_topic"].strip()
    kind = r["kind"]
    if exp == "VERIFIED":
        if kind == "VERIFIED" and r["topic"] == topic:
            return "correct"
        if kind == "SUGGEST" and r["suggest"] == topic:
            return "suggested"
        return "wrong"
    if exp == "FACTUAL":
        if kind in ("FACTUAL STRONG", "FACTUAL PARTIAL", "DIGEST"):
            return "answered"
        if kind == "FACTUAL WEAK":
            return "declined"
        if kind == "SUGGEST":
            return "suggested"
        if kind == "VERIFIED":  # a verified answer for a document question is fine if it is on-topic;
            return "correct" if not topic or r["topic"] == topic else "suggested"
        return "wrong"
    raise SystemExit(f"{row['id']}: expected_route must be VERIFIED or FACTUAL, not {exp!r}")


def source_hit(row, r):
    want = row.get("expected_source", "").strip().lower()
    if not want:
        return ""
    srcs = [h["source"].lower() for h in r["hits"]]
    if r.get("followup"):
        srcs += [h["source"].lower() for h in r["followup"]["hits"]]
    return "hit" if any(want in s for s in srcs) else "miss"


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=os.path.join(os.path.dirname(here), "rafiki_pack.db"))
    ap.add_argument("--tests", default=os.path.join(here, "test_set.csv"))
    ap.add_argument("--show", choices=["wrong", "all", "parity"], help="list rows")
    ap.add_argument("--split", choices=["all", "dev", "test"], default="all",
                    help="dev = odd-numbered rows (for tuning), test = even-numbered rows (held out)")
    ap.add_argument("--out", help="write one row per question (216) to this CSV")
    a = ap.parse_args()

    db = sqlite3.connect(a.db)
    rows = list(csv.DictReader(open(a.tests, encoding="utf-8")))
    for i, row in enumerate(rows):
        row["split"] = "dev" if i % 2 == 0 else "test"
    if a.split != "all":
        rows = [row for row in rows if row["split"] == a.split]
    results = []
    for row in rows:
        per = {}
        for lang in ("en", "sw"):
            q = row[f"question_{lang}"].strip()
            if not q:
                continue
            r = qp.route(db, q, lang)
            top = r["hits"][0]["source"] if r["hits"] else ""
            per[lang] = r
            results.append(dict(id=row["id"], split=row["split"], domain=row["domain"], type=row["type"], lang=lang,
                                question=q, expected_route=row["expected_route"],
                                expected_topic=row["expected_topic"], kind=r["kind"], topic=r["topic"],
                                suggest=r["suggest"], confidence=r["confidence"], routed_domain=r["domain"],
                                expanded=" ".join(r.get("expanded", [])), top_source=top,
                                outcome=outcome(row, r), source=source_hit(row, r)))
        if len(per) == 2:
            same = (per["en"]["kind"], per["en"]["topic"], per["en"]["suggest"]) == \
                   (per["sw"]["kind"], per["sw"]["topic"], per["sw"]["suggest"])
            for res in results[-2:]:
                res["parity"] = "same" if same else "differs"

    # ---------------- summary
    def table(title, key):
        print(f"\n{title}")
        print(f"  {'':<17}" + "".join(f"{o:>10}" for o in OUTCOMES) + f"{'n':>6}")
        groups = defaultdict(list)
        for res in results:
            groups[key(res)].append(res)
        for g in sorted(groups, key=lambda x: (DOMAINS + ["en", "sw"]).index(x) if x in DOMAINS + ["en", "sw"] else 99):
            rs = groups[g]
            print(f"  {g:<17}" + "".join(f"{sum(r['outcome'] == o for r in rs) / len(rs):>10.0%}"
                                         for o in OUTCOMES) + f"{len(rs):>6}")

    print(f"Pack: {a.db} | test set: {a.tests} | split: {a.split} | {len(rows)} rows, {len(results)} questions")
    table("Routing outcome by language", lambda r: r["lang"])
    table("Routing outcome by domain (both languages)", lambda r: r["domain"])

    pairs = [r for r in results if r["lang"] == "en" and "parity" in r]
    same = sum(r["parity"] == "same" for r in pairs)
    print(f"\nCross-lingual parity: {same}/{len(pairs)} pairs ({same / max(len(pairs), 1):.0%}) "
          f"get the same route and topic in English and Kiswahili")
    by_dom = defaultdict(list)
    for r in pairs:
        by_dom[r["domain"]].append(r["parity"] == "same")
    print("  " + " | ".join(f"{d} {sum(v)}/{len(v)}" for d, v in sorted(by_dom.items(), key=lambda x: DOMAINS.index(x[0]))))

    with_src = [r for r in results if r["source"]]
    if with_src:
        hits = sum(r["source"] == "hit" for r in with_src)
        print(f"\nRetrieval: expected source in the top 3 for {hits}/{len(with_src)} questions "
              f"({hits / len(with_src):.0%})")
    else:
        print("\nRetrieval: no expected_source filled in yet -- fill that column to score retrieval")

    if a.show:
        print()
        for r in results:
            if a.show == "all" or (a.show == "wrong" and r["outcome"] in ("wrong", "declined")) or \
                    (a.show == "parity" and r.get("parity") == "differs"):
                got = r["kind"] + (f" {r['topic']}" if r["topic"] else "") + (f" ?{r['suggest']}" if r["suggest"] else "")
                want = r["expected_route"] + (f" {r['expected_topic']}" if r["expected_topic"] else "")
                print(f"{r['id']} {r['lang']} [{r['outcome']}] want {want} | got {got} | {r['question']}")

    if a.out:
        cols = list(results[0].keys()) if results else []
        if "parity" not in cols:
            cols.append("parity")
        with open(a.out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(results)
        print(f"\nWrote {a.out}")


if __name__ == "__main__":
    main()
