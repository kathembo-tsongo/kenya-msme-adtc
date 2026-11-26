#!/usr/bin/env python3
"""
score_phone_eval.py -- score evaluation runs (phone or laptop) against eval/test_set.csv.

  Accuracy        an answer is ACCURATE when it contains every must_contain fact and no
                  must_not_contain fact (rows with no must_contain are "unscored"). Facts are
                  separated by "|"; inside a fact, alternatives are separated by " OR "
                  ("KES 5,000,000 OR 5 million"). Matching ignores case and thousands separators.
  Answer language for model-written answers only: was the answer written in the operator's
                  language? The model's text (footer, figure-check notes and app-added lines removed)
                  is classified as Kiswahili, English or mixed from common function words.
  Routing         the same outcomes as eval_testset.py (correct / suggested / answered / declined / wrong)
  Parity          English vs Kiswahili accuracy for the same question
  Consistency     with 2+ passes: share of questions whose route, topic and accuracy verdict are the
                  same in every pass (and, separately, whose answer text is identical)
  Latency         instant answers and model answers: median and 90th percentile; time to first token
  Speed drift     decode tokens/s of model answers across the run: first 20% vs last 20%
  Memory margin   available RAM / total RAM at its lowest point; peak app memory (PSS); low-memory flags
  Conditions      highest battery temperature and thermal status during the run

One run gives the full report. Several runs give a model comparison table (the base-model
selection step), and --samples writes Kiswahili answers side by side for a human check.

    python3 eval/score_phone_eval.py eval/phone_runs/rafiki_eval_<run>.jsonl
    python3 eval/score_phone_eval.py <run>.jsonl --split test --out eval/phone_runs/scored.csv
    python3 eval/score_phone_eval.py run_qwen.jsonl run_gemma.jsonl run_swgemma.jsonl \
        --samples eval/kiswahili_samples.md
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


# ---------------------------------------------------------------- answer language
# Common function words and very frequent words. Names of offices, laws, websites and amounts are
# the same in both languages, so they are ignored rather than counted.
SW_WORDS = set("""na ya wa kwa ni la za cha vya katika kwenye au pia kama ili hii hiyo hizi huu hayo kuwa kwamba
yako wako lako zako chako yake wake lake zake yao wao sisi wewe mimi unaweza unahitaji utahitaji inahitajika
lazima hatua kupitia baada kabla zaidi sana bila hadi ambayo ambao ambalo ambacho kila mfano yaani kisha halafu
hapa pale huko sasa bado tu ndiyo ndio hapana si siyo hakuna kuna ipo yupo nini gani vipi lini wapi jinsi namna
biashara kodi ushuru mkopo mikopo leseni kibali usajili kusajili kujisajili kulipa kupata kuanza kufungua
kuomba kutumia kujaza kuwasilisha kuhakikisha kufuata kuweka kutoa mwajiri mfanyakazi wafanyakazi mshahara
mapato mauzo gharama ada kiasi asilimia kila mwezi mwaka siku tarehe ofisi serikali kaunti mtandaoni fomu
taarifa hati nambari jina mmiliki kampuni ndogo kubwa mpya muhimu kwanza pili tatu nne tano hakikisha tembelea
wasiliana fuata jaza lipa omba andika chagua ingia ingiza bonyeza thibitisha""".split())
EN_WORDS = set("""the and of to is are for you your in with a an be can this that it on or by from as will
should must have has not if at which who what when where how do does get need needs also any all more each
their they them there these those then than into about after before only use using pay paid apply register
registration business tax loan licence license permit office online form fee amount month year""".split())


def model_text(answer):
    """The model's own words: drop the app footer, figure-check notes and app-added prefixes."""
    body = (answer or "").split("\n\n---\n")[0]
    lines = [l for l in body.splitlines() if not l.strip().startswith("⚠️")]
    body = "\n".join(lines).replace("*(amount not in the documents)*", " ")
    body = re.sub(r"https?://\S+|www\.\S+|\S+\.(?:go\.ke|co\.ke|com|org)\S*", " ", body)
    return body


def answer_language(answer):
    """'sw', 'en', 'mixed' or 'short' (too few common words to tell)."""
    w = re.findall(r"[a-zA-Z']+", model_text(answer).lower())
    sw = sum(t in SW_WORDS for t in w)
    en = sum(t in EN_WORDS for t in w)
    if sw + en < 6:
        return "short"
    share = sw / (sw + en)
    return "sw" if share >= 0.75 else "en" if share <= 0.25 else "mixed"


# ---------------------------------------------------------------- loading
def load_tests(path):
    tests = {}
    for i, row in enumerate(csv.DictReader(open(path, encoding="utf-8"))):
        row["split"] = "dev" if i % 2 == 0 else "test"
        tests[row["id"]] = row
    return tests


def load_run(path, tests, split):
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip().startswith("{")]
    rows = [r for r in rows if r.get("id") in tests and (split == "all" or tests[r["id"]]["split"] == split)]
    for r in rows:
        t = tests[r["id"]]
        route = dict(kind=r.get("route", ""), topic=r.get("topic", ""), suggest=r.get("suggest", ""))
        if route["kind"].startswith("FACTUAL") and route["kind"] not in ("FACTUAL STRONG", "FACTUAL PARTIAL", "FACTUAL WEAK"):
            route["kind"] = route["kind"].split(" (")[0]
        r["outcome"] = outcome(t, route)
        r["verdict"] = verdict(r.get("answer", ""), facts(t["must_contain"]), facts(t["must_not_contain"]))
        r["domain"] = t["domain"]
        r["split"] = t["split"]
        r["answer_language"] = answer_language(r.get("answer", "")) if r.get("model") == "yes" else ""
    return rows


def run_label(rows, path):
    model = rows[0].get("model_file") or "phone model"
    mode = rows[0].get("answer_mode")
    mode = {"operator": "operator language", "en": "English"}.get(mode, "as logged")
    return model, mode, os.path.basename(path)


def lang_share(rows, qlang, want):
    """Share of model answers to qlang questions written in `want`, and how many there were."""
    rs = [r for r in rows if r.get("model") == "yes" and r["lang"] == qlang]
    return (sum(r["answer_language"] == want for r in rs) / len(rs) if rs else None), len(rs)


def fmt_share(x):
    return "  -  " if x is None else f"{x:.0%}"


# ---------------------------------------------------------------- one run: full report
def report(rows, path, out):
    passes = sorted({r.get("pass", 1) for r in rows})
    android = f" (Android {rows[0]['android']})" if rows[0].get("android") else ""
    model, mode, _ = run_label(rows, path)
    print(f"Run {rows[0].get('run', '?')} | {rows[0].get('device', '?')}{android} | "
          f"pack {rows[0].get('pack', '?')} | {len(rows)} answers, passes {passes}")
    if rows[0].get("model_file"):
        print(f"Model {model} | answers in {mode}")

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

    # ---------------- answer language
    print("\nLanguage of model-written answers (by question language)")
    for qlang in ("en", "sw"):
        rs = [r for r in rows if r.get("model") == "yes" and r["lang"] == qlang]
        if not rs:
            print(f"  {qlang}  no model answers")
            continue
        parts = "  ".join(f"{l} {sum(r['answer_language'] == l for r in rs) / len(rs):.0%}"
                          for l in ("sw", "en", "mixed", "short"))
        print(f"  {qlang}  {parts}   (n {len(rs)})")
    sw_ok, sw_n = lang_share(rows, "sw", "sw")
    if sw_n:
        print(f"  Kiswahili questions answered in Kiswahili: {fmt_share(sw_ok)}")

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

    if out:
        write_csv(rows, out)


def write_csv(rows, out):
    cols = ["run", "model_file", "answer_mode", "pass", "split", "id", "lang", "domain", "question", "route",
            "topic", "suggest", "outcome", "verdict", "model", "answer_language", "total_ms", "ttft_ms",
            "gen_tokens", "decode_tps", "pss_mb", "avail_mb", "battery_c", "thermal", "answer"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {out}")


# ---------------------------------------------------------------- several runs: model comparison
def compare(runs):
    """runs = [(path, rows)]. One line per run: the numbers the base-model choice rests on."""
    print("Model comparison (model-written answers only; instant answers are the same for every model)\n")
    head = (f"  {'model':<34}{'answers in':<19}{'n':>5}{'sw->sw':>8}{'en->en':>8}"
            f"{'acc en':>8}{'acc sw':>8}{'median s':>10}{'tok/s':>7}")
    print(head)
    print("  " + "-" * (len(head) - 2))
    for path, rows in runs:
        model, mode, _ = run_label(rows, path)
        m = [r for r in rows if r.get("model") == "yes"]
        sw_ok, _ = lang_share(rows, "sw", "sw")
        en_ok, _ = lang_share(rows, "en", "en")

        def acc(lang):
            rs = [r for r in m if r["lang"] == lang and r["verdict"] != "unscored"]
            return f"{sum(r['verdict'] == 'accurate' for r in rs) / len(rs):.0%}" if rs else "  -"
        med = f"{statistics.median(r['total_ms'] for r in m) / 1000:.1f}" if m else "-"
        tps = [r["decode_tps"] for r in m if r.get("decode_tps", 0) > 0]
        tps = f"{statistics.median(tps):.1f}" if tps else "-"
        print(f"  {model[:33]:<34}{mode:<19}{len(m):>5}{fmt_share(sw_ok):>8}{fmt_share(en_ok):>8}"
              f"{acc('en'):>8}{acc('sw'):>8}{med:>10}{tps:>7}")
    print("\n  sw->sw = Kiswahili questions answered in Kiswahili; en->en = English questions answered in English")
    print("  acc = accurate / scored (rows with must_contain); laptop speed is not phone speed")
    print("  The language check counts common words only: read the samples (--samples) before choosing.")


def write_samples(runs, path, n):
    """Kiswahili model answers side by side, one section per question, for the human check."""
    by_run = []
    for p, rows in runs:
        model, mode, _ = run_label(rows, p)
        first = {}
        for r in rows:
            if r.get("model") == "yes" and r["lang"] == "sw" and r["id"] not in first:
                first[r["id"]] = r
        by_run.append((f"{model} ({mode})", first))
    ids = sorted(set().union(*(f.keys() for _, f in by_run)))
    if n:
        ids = ids[:n]
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Kiswahili answers for review\n\n")
        f.write("For each answer, mark: **Lugha** (natural Kiswahili / understandable / poor / not Kiswahili) "
                "and **Usahihi** (correct / partly / wrong).\n\n")
        for qid in ids:
            q = next((fr[qid]["question"] for _, fr in by_run if qid in fr), "")
            f.write(f"## {qid}: {q}\n\n")
            for label, fr in by_run:
                r = fr.get(qid)
                f.write(f"**{label}** · detected: {r['answer_language'] if r else '-'}\n\n")
                text = model_text(r["answer"]).strip() if r else "*(not in this run)*"
                f.write("> " + text.replace("\n", "\n> ") + "\n\n")
                f.write("Lugha: ______  Usahihi: ______\n\n")
            f.write("---\n\n")
    print(f"\nWrote {len(ids)} questions x {len(by_run)} runs of Kiswahili answers to {path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+", help="one run for the full report, several for a model comparison")
    ap.add_argument("--tests", default=os.path.join(HERE, "test_set.csv"))
    ap.add_argument("--split", choices=["all", "dev", "test"], default="all")
    ap.add_argument("--out", help="write one scored row per answer to this CSV (all runs together)")
    ap.add_argument("--samples", help="write Kiswahili model answers side by side to this Markdown file")
    ap.add_argument("--n-samples", type=int, default=0, help="limit --samples to the first N questions")
    a = ap.parse_args()

    tests = load_tests(a.tests)
    runs = []
    for p in a.runs:
        rows = load_run(p, tests, a.split)
        if not rows:
            raise SystemExit(f"{p}: no answers match the test set (or the split).")
        runs.append((p, rows))

    if len(runs) == 1:
        print(f"Split {a.split}")
        report(runs[0][1], runs[0][0], a.out)
    else:
        print(f"Split {a.split} | {len(runs)} runs\n")
        compare(runs)
        if a.out:
            write_csv([r for _, rows in runs for r in rows], a.out)
    if a.samples:
        write_samples(runs, a.samples, a.n_samples)


if __name__ == "__main__":
    main()
