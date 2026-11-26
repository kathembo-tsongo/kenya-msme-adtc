#!/usr/bin/env python3
"""
score_phone_eval.py -- score an evaluation run from the phone against eval/test_set.csv.

  Accuracy        an answer is ACCURATE when it contains every must_contain fact and no
                  must_not_contain fact (rows with no must_contain are "unscored"). Facts are
                  separated by "|"; inside a fact, alternatives are separated by " OR "
                  ("KES 5,000,000 OR 5 million"). Matching ignores case and thousands separators.
  Routing         the same outcomes as eval_testset.py (correct / suggested / answered / declined / wrong)
  Parity          English vs Kiswahili accuracy for the same question
  Consistency     with 2+ passes: share of questions whose route, topic and accuracy verdict are the
                  same in every pass (and, separately, whose answer text is identical)
  Latency         instant answers and model answers: median and 90th percentile; time to first token
  Speed drift     decode tokens/s of model answers across the run: first 20% vs last 20%
  Memory margin   available RAM / total RAM at its lowest point; peak app memory (PSS); low-memory flags
  Conditions      highest battery temperature and thermal status during the run

    python3 eval/score_phone_eval.py eval/phone_runs/rafiki_eval_<run>.jsonl
    python3 eval/score_phone_eval.py <run>.jsonl --split test --out eval/phone_runs/scored.csv
"""
import argparse
import csv
import json
import os
import re
import statistics
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from eval_testset import DOMAINS, OUTCOMES, outcome  # noqa: E402


def norm(s):
    s = (s or "").lower().replace(" ", " ")
    s = re.sub(r"(?<=\d),(?=\d{3})", "", s)          # 5,000,000 -> 5000000
    s = re.sub(r"[*_`]", "", s)                       # markdown emphasis
    return re.sub(r"\s+", " ", s)


def facts(cell):
    return [[norm(alt).strip() for alt in f.split(" OR ") if alt.strip()]
            for f in (cell or "").split("|") if f.strip()]


def verdict(answer, must, must_not):
    if not must:
        return "unscored"
    a = norm(answer)
    has_all = all(any(alt in a for alt in f) for f in must)
    has_bad = any(any(alt in a for alt in f) for f in must_not)
    return "accurate" if has_all and not has_bad else "inaccurate"


def pct(xs, p):
    if not xs:
        return 0
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(p / 100 * (len(xs) - 1))))]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run")
    ap.add_argument("--tests", default=os.path.join(HERE, "test_set.csv"))
    ap.add_argument("--split", choices=["all", "dev", "test"], default="all")
    ap.add_argument("--out", help="write one scored row per answer to this CSV")
    a = ap.parse_args()

    tests = {}
    for i, row in enumerate(csv.DictReader(open(a.tests, encoding="utf-8"))):
        row["split"] = "dev" if i % 2 == 0 else "test"
        tests[row["id"]] = row
    rows = [json.loads(l) for l in open(a.run, encoding="utf-8") if l.strip().startswith("{")]
    rows = [r for r in rows if r.get("id") in tests and (a.split == "all" or tests[r["id"]]["split"] == a.split)]
    if not rows:
        raise SystemExit("No answers match the test set (or the split).")

    for r in rows:
        t = tests[r["id"]]
        route = dict(kind=r.get("route", ""), topic=r.get("topic", ""), suggest=r.get("suggest", ""))
        if route["kind"].startswith("FACTUAL") and route["kind"] not in ("FACTUAL STRONG", "FACTUAL PARTIAL", "FACTUAL WEAK"):
            route["kind"] = route["kind"].split(" (")[0]
        r["outcome"] = outcome(t, route)
        r["verdict"] = verdict(r.get("answer", ""), facts(t["must_contain"]), facts(t["must_not_contain"]))
        r["domain"] = t["domain"]
        r["split"] = t["split"]

    passes = sorted({r.get("pass", 1) for r in rows})
    android = f" (Android {rows[0]['android']})" if rows[0].get("android") else ""
    print(f"Run {rows[0].get('run', '?')} | {rows[0].get('device', '?')}{android} | "
          f"pack {rows[0].get('pack', '?')} | split {a.split} | {len(rows)} answers, passes {passes}")

    # ---------------- accuracy
    def acc_table(title, key):
        print(f"\n{title}")
        print(f"  {'':<17}{'accurate':>10}{'inaccurate':>12}{'unscored':>10}{'accuracy*':>11}{'n':>6}")
        groups = defaultdict(list)
        for r in rows:
            groups[key(r)].append(r)
        order = DOMAINS + ["en", "sw"]
        for g in sorted(groups, key=lambda x: order.index(x) if x in order else 99):
            rs = groups[g]
            ok = sum(r["verdict"] == "accurate" for r in rs)
            bad = sum(r["verdict"] == "inaccurate" for r in rs)
            un = len(rs) - ok - bad
            print(f"  {g:<17}{ok:>10}{bad:>12}{un:>10}{(ok / (ok + bad) if ok + bad else 0):>11.0%}{len(rs):>6}")
    acc_table("Answer accuracy by language", lambda r: r["lang"])
    acc_table("Answer accuracy by domain", lambda r: r["domain"])
    print("  * accuracy = accurate / scored; fill must_contain in test_set.csv to score more rows")

    print("\nRouting outcome by language")
    for lang in ("en", "sw"):
        rs = [r for r in rows if r["lang"] == lang]
        print(f"  {lang}  " + "  ".join(f"{o} {sum(r['outcome'] == o for r in rs) / max(len(rs), 1):.0%}" for o in OUTCOMES))

    # ---------------- parity (first pass)
    first = {(r["id"], r["lang"]): r for r in rows if r.get("pass", 1) == passes[0]}
    pairs = [(first[(i, "en")], first[(i, "sw")]) for i in {k[0] for k in first}
             if (i, "en") in first and (i, "sw") in first]
    scored = [(e, s) for e, s in pairs if e["verdict"] != "unscored"]
    same_route = sum((e.get("route"), e.get("topic")) == (s.get("route"), s.get("topic")) for e, s in pairs)
    same_verdict = sum(e["verdict"] == s["verdict"] for e, s in scored)
    print(f"\nCross-lingual parity (pass {passes[0]}): same route and topic {same_route}/{len(pairs)}"
          + (f"; same accuracy verdict {same_verdict}/{len(scored)} scored pairs" if scored else ""))

    # ---------------- consistency
    if len(passes) > 1:
        by_q = defaultdict(list)
        for r in rows:
            by_q[(r["id"], r["lang"])].append(r)
        full = [v for v in by_q.values() if len(v) == len(passes)]
        cons = sum(len({(x.get("route"), x.get("topic"), x["verdict"]) for x in v}) == 1 for v in full)
        ident = sum(len({x.get("answer", "") for x in v}) == 1 for v in full)
        model_q = [v for v in full if v[0].get("model") == "yes"]
        model_ident = sum(len({x.get("answer", "") for x in v}) == 1 for v in model_q)
        print(f"\nConsistency rate over {len(passes)} passes: {cons}/{len(full)} ({cons / max(len(full), 1):.0%}) "
              f"same route, topic and verdict; identical answer text {ident}/{len(full)} "
              f"(model answers only: {model_ident}/{len(model_q)})")
    else:
        print("\nConsistency rate: needs a run with 2 or more passes")

    # ---------------- latency
    inst = [r["total_ms"] for r in rows if r.get("model") != "yes"]
    mod = [r["total_ms"] for r in rows if r.get("model") == "yes"]
    ttft = [r["ttft_ms"] for r in rows if r.get("model") == "yes" and r.get("ttft_ms", -1) >= 0]
    print("\nLatency")
    if inst:
        print(f"  instant answers ({len(inst)}): median {statistics.median(inst):.0f} ms, p90 {pct(inst, 90):.0f} ms")
    if mod:
        print(f"  model answers   ({len(mod)}): median {statistics.median(mod) / 1000:.1f} s, "
              f"p90 {pct(mod, 90) / 1000:.1f} s, time to first word median {statistics.median(ttft) / 1000:.1f} s")

    # ---------------- speed drift
    seq = sorted([r for r in rows if r.get("model") == "yes" and r.get("decode_tps", 0) > 0],
                 key=lambda r: r.get("time", ""))
    if len(seq) >= 10:
        k = max(1, len(seq) // 5)
        early = statistics.mean(r["decode_tps"] for r in seq[:k])
        late = statistics.mean(r["decode_tps"] for r in seq[-k:])
        tps = [r["decode_tps"] for r in seq]
        print(f"\nDecode speed: median {statistics.median(tps):.2f} tokens/s (min {min(tps):.2f}, max {max(tps):.2f})")
        print(f"Speed drift: first 20% {early:.2f} -> last 20% {late:.2f} tokens/s ({(late - early) / early:+.0%})")
    else:
        print("\nSpeed drift: needs at least 10 model answers")

    # ---------------- memory and conditions
    if any("avail_mb" in r for r in rows):
        low = min(rows, key=lambda r: r.get("avail_mb", 1e9))
        margin = low["avail_mb"] / max(low.get("total_mb", 1), 1)
        print(f"\nMemory: total {low.get('total_mb')} MB; lowest available {low['avail_mb']} MB "
              f"(margin {margin:.0%}, system low-memory threshold {low.get('threshold_mb')} MB); "
              f"peak app PSS {max(r.get('pss_mb', 0) for r in rows)} MB; "
              f"low-memory flag in {sum(bool(r.get('low_memory')) for r in rows)} answers")
        print(f"Conditions: battery up to {max(r.get('battery_c', 0) for r in rows):.1f} C, "
              f"thermal status up to {max(r.get('thermal', 0) for r in rows)} (0 = none, 3 = severe), "
              f"charging in {sum(bool(r.get('charging')) for r in rows)}/{len(rows)} answers")

    if a.out:
        cols = ["run", "pass", "split", "id", "lang", "domain", "question", "route", "topic", "suggest",
                "outcome", "verdict", "model", "total_ms", "ttft_ms", "gen_tokens", "decode_tps", "pss_mb",
                "avail_mb", "battery_c", "thermal", "answer"]
        with open(a.out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        print(f"\nWrote {a.out}")


if __name__ == "__main__":
    main()
