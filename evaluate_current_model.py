"""
evaluate_current_model.py — Accuracy evaluation against the ACTUAL
on-device Rafiki wa Biashara system (fine-tuned Qwen2.5-1.5B via
llama.cpp + TF-IDF RAG), NOT the old cloud-based Claude system.

Reuses the same test_questions.csv and scoring rubric as the
original evaluate.py, but sends requests to the current local
RAG proxy at http://localhost:8091/v1/chat/completions instead
of calling the Anthropic API.

Run with your server already running (./start.sh in another terminal):
    python3 evaluate_current_model.py
"""

import csv
import sys
import time
import requests
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

BASE_DIR       = Path(__file__).parent
LOG_DIR        = BASE_DIR / "logs"
QUESTIONS_FILE = LOG_DIR / "test_questions.csv"
RAG_PROXY_URL  = "http://localhost:8091/v1/chat/completions"
LOG_DIR.mkdir(exist_ok=True)


def load_questions(category_filter=None, limit=None):
    if not QUESTIONS_FILE.exists():
        print(f"ERROR: Questions file not found: {QUESTIONS_FILE}")
        sys.exit(1)
    questions = []
    with open(QUESTIONS_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if category_filter and category_filter.lower() not in row["category"].lower():
                continue
            questions.append({
                "id":               int(row["id"]),
                "category":         row["category"],
                "question":         row["question"],
                "must_contain":     row["must_contain"].split("|"),
                "must_not_contain": row["must_not_contain"].split("|"),
            })
    if limit:
        questions = questions[:limit]
    return questions


def score_answer(answer, must_contain, must_not_contain):
    answer_lower = answer.lower()
    matched  = [kw for kw in must_contain if kw.lower() in answer_lower]
    missed   = [kw for kw in must_contain if kw.lower() not in answer_lower]
    kw_score = round((len(matched) / len(must_contain)) * 2) if must_contain else 2
    rel_score = 0 if any(p.lower() in answer_lower for p in must_not_contain) else 1
    len_score = 1 if len(answer.split()) >= 80 else 0
    kenya_terms = ["kenya","kra","brs","safaricom","mpesa","hustler",
                   "nairobi","ksh","kes","county","ecitizen","nhif",
                   "nssf","shif","nita","kebs","cbk","yedf","wef"]
    ken_score = 1 if any(t in answer_lower for t in kenya_terms) else 0
    total = kw_score + rel_score + len_score + ken_score

    if total >= 5:   rating = "Excellent"
    elif total >= 4: rating = "Good"
    elif total >= 3: rating = "Partial"
    elif total >= 2: rating = "Weak"
    else:            rating = "Poor"

    return {
        "score": total, "max_score": 5, "rating": rating,
        "kw_matched": matched, "kw_missed": missed,
        "kw_score": kw_score, "rel_score": rel_score,
        "len_score": len_score, "ken_score": ken_score,
        "word_count": len(answer.split()),
    }


def call_current_system(question):
    try:
        resp = requests.post(
            RAG_PROXY_URL,
            json={"messages": [{"role": "user", "content": question}]},
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return content, None
    except Exception as e:
        return f"ERROR: {e}", str(e)


def run_evaluation(questions):
    results = []
    total_score = 0
    print(f"\n  Running {len(questions)} questions against LIVE system at {RAG_PROXY_URL}...")
    print("-" * 65)

    for test in questions:
        qid, question, category = test["id"], test["question"], test["category"]
        print(f"\n[{qid:02d}/{len(questions)}] {category}: {question[:52]}...")

        start = time.time()
        answer, error = call_current_system(question)
        elapsed = time.time() - start

        scoring = score_answer(answer, test["must_contain"], test["must_not_contain"])
        score = scoring["score"]
        total_score += score

        print(f"  Score: {score}/5 ({scoring['rating']}) | {elapsed:.1f}s | {scoring['word_count']} words")
        if scoring["kw_missed"]:
            print(f"  Missing: {scoring['kw_missed']}")
        if error:
            print(f"  ERROR: {error}")

        results.append({
            "id": qid, "category": category, "question": question,
            "score": score, "max_score": 5, "rating": scoring["rating"],
            "kw_score": scoring["kw_score"], "rel_score": scoring["rel_score"],
            "len_score": scoring["len_score"], "ken_score": scoring["ken_score"],
            "kw_matched": ", ".join(scoring["kw_matched"]),
            "kw_missed": ", ".join(scoring["kw_missed"]),
            "word_count": scoring["word_count"],
            "response_time": round(elapsed, 2),
            "answer_preview": answer[:200].replace("\n", " "),
        })
        time.sleep(1)

    return results, total_score


def print_and_save_report(results, total_score):
    total_q = len(results)
    avg_score = total_score / total_q
    accuracy = sum(1 for r in results if r["score"] >= 4) / total_q * 100

    cat_scores = defaultdict(list)
    for r in results:
        cat_scores[r["category"]].append(r["score"])
    ratings = Counter(r["rating"] for r in results)

    print("\n" + "=" * 65)
    print("  EVALUATION SUMMARY — CURRENT ON-DEVICE MODEL")
    print("=" * 65)
    print(f"  Model:               msme-qwen2.5-1.5b-Q4_K_M (via llama.cpp)")
    print(f"  Questions tested:    {total_q}")
    print(f"  Total score:         {total_score}/{total_q * 5}")
    print(f"  Average score:       {avg_score:.2f}/5.00")
    print(f"  Overall accuracy:    {avg_score/5*100:.1f}%")
    print(f"  Good/Excellent rate: {accuracy:.0f}%")

    print("\n  By category:")
    for cat, scores in sorted(cat_scores.items()):
        avg = sum(scores) / len(scores)
        print(f"    {cat:<25} {avg:.1f}/5.0  ({len(scores)} Qs)")

    csv_path = LOG_DIR / "evaluation_results_current_model.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    rpt_path = LOG_DIR / "evaluation_report_current_model.txt"
    with open(rpt_path, "w", encoding="utf-8") as f:
        f.write("RAFIKI WA BIASHARA — ON-DEVICE MODEL EVALUATION REPORT\n")
        f.write("=" * 60 + "\n")
        f.write(f"Date:              {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"Model:             msme-qwen2.5-1.5b-Q4_K_M (llama.cpp, on-device)\n")
        f.write(f"Endpoint tested:   {RAG_PROXY_URL}\n")
        f.write(f"Questions tested:  {total_q}\n")
        f.write(f"Total score:       {total_score}/{total_q*5}\n")
        f.write(f"Average score:     {avg_score:.2f}/5.00\n")
        f.write(f"Overall accuracy:  {avg_score/5*100:.1f}%\n")
        f.write(f"Good/Excellent:    {accuracy:.0f}%\n\n")
        f.write("CATEGORY BREAKDOWN\n" + "-"*40 + "\n")
        for cat, scores in sorted(cat_scores.items()):
            avg = sum(scores)/len(scores)
            f.write(f"{cat:<25} {avg:.1f}/5.0  ({len(scores)} questions)\n")
        f.write("\nDETAILED RESULTS\n" + "-"*40 + "\n")
        for r in results:
            f.write(f"\nQ{r['id']:02d} [{r['category']}] {r['score']}/5 ({r['rating']})\n")
            f.write(f"     Q: {r['question'][:70]}\n")
            f.write(f"     Matched:  {r['kw_matched'] or 'none'}\n")
            f.write(f"     Missed:   {r['kw_missed'] or 'none'}\n")
            f.write(f"     Time:     {r['response_time']}s\n")

    print(f"\n  Saved: {csv_path}")
    print(f"  Saved: {rpt_path}")
    print("\n  Evaluation complete against the ACTUAL submitted on-device model.")


if __name__ == "__main__":
    print("=" * 65)
    print("  Rafiki wa Biashara — Current On-Device Model Evaluation")
    print("=" * 65)
    print(f"  Testing against: {RAG_PROXY_URL}")
    print(f"  (Make sure ./start.sh is running in another terminal first!)")

    try:
        health = requests.get("http://localhost:8090/health", timeout=5)
        print(f"  llama-server health check: {health.status_code}")
    except Exception as e:
        print(f"  WARNING: Could not reach llama-server — is it running? ({e})")
        sys.exit(1)

    questions = load_questions()
    print(f"  Questions loaded: {len(questions)}")

    results, total_score = run_evaluation(questions)
    print_and_save_report(results, total_score)
