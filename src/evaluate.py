"""
evaluate.py — Kenya MSME Advisor: Flexible Evaluation Framework

Questions are loaded from:  logs/test_questions.csv
Add, remove or edit questions there — no code changes needed.

CSV columns:
  id, category, question, must_contain (pipe-separated), must_not_contain (pipe-separated)

Run with:
    python3 src/evaluate.py                    # run all questions
    python3 src/evaluate.py --category Tax     # run only Tax questions
    python3 src/evaluate.py --limit 10         # run first 10 questions

Outputs:
    logs/evaluation_results.csv
    logs/evaluation_report.txt
"""

import os
import csv
import sys
import json
import pickle
import time
import argparse
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
import anthropic

BASE_DIR       = Path(__file__).parent.parent
DB_DIR         = BASE_DIR / "knowledge_base"
LOG_DIR        = BASE_DIR / "logs"
QUESTIONS_FILE = LOG_DIR / "test_questions.csv"
LOG_DIR.mkdir(exist_ok=True)


# ── Load questions from CSV ────────────────────────────────────────────────────
def load_questions(category_filter=None, limit=None):
    """
    Load test questions from CSV file.
    Anyone can add questions by editing logs/test_questions.csv
    — no Python knowledge required.
    """
    if not QUESTIONS_FILE.exists():
        print(f"ERROR: Questions file not found: {QUESTIONS_FILE}")
        print("Create it with columns: id,category,question,must_contain,must_not_contain")
        sys.exit(1)

    questions = []
    with open(QUESTIONS_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Filter by category if specified
            if category_filter:
                if category_filter.lower() not in row["category"].lower():
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


# ── Load knowledge base ────────────────────────────────────────────────────────
def load_index():
    with open(DB_DIR / "vectorizer.pkl", "rb") as f: vectorizer = pickle.load(f)
    with open(DB_DIR / "matrix.pkl",     "rb") as f: matrix     = pickle.load(f)
    with open(DB_DIR / "chunks.json")         as f: data       = json.load(f)
    return vectorizer, matrix, data["chunks"], data["metadata"]


def retrieve(query, vectorizer, matrix, chunks, metadata, k=4):
    qvec = vectorizer.transform([query])
    sims = cosine_similarity(qvec, matrix).flatten()
    top  = sims.argsort()[-k:][::-1]
    ctx_parts, sources = [], []
    for i in top:
        if sims[i] > 0.01:
            ctx_parts.append(chunks[i])
            src = metadata[i].get("filename", "Unknown")
            if src not in sources:
                sources.append(src)
    return "\n\n---\n\n".join(ctx_parts), sources


# ── Scoring ────────────────────────────────────────────────────────────────────
def score_answer(answer, must_contain, must_not_contain):
    answer_lower = answer.lower()

    # 1. Keyword coverage (0-2)
    matched  = [kw for kw in must_contain if kw.lower() in answer_lower]
    missed   = [kw for kw in must_contain if kw.lower() not in answer_lower]
    kw_score = round((len(matched) / len(must_contain)) * 2) if must_contain else 2

    # 2. Relevance — no "I don't know" (0-1)
    rel_score = 0 if any(
        p.lower() in answer_lower for p in must_not_contain
    ) else 1

    # 3. Length — detailed enough (0-1)
    len_score = 1 if len(answer.split()) >= 100 else 0

    # 4. Kenya specificity (0-1)
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


# ── Main ───────────────────────────────────────────────────────────────────────
def run_evaluation(questions, api_key):
    client = anthropic.Anthropic(api_key=api_key)
    vectorizer, matrix, chunks, metadata = load_index()

    total_q   = len(questions)
    results   = []
    total_score = 0

    print(f"\n  Running {total_q} questions...")
    print("-" * 65)

    for test in questions:
        qid      = test["id"]
        question = test["question"]
        category = test["category"]

        print(f"\n[{qid:02d}/{total_q}] {category}: {question[:52]}...")

        context, sources = retrieve(
            question, vectorizer, matrix, chunks, metadata
        )

        start   = time.time()
        answer  = None
        elapsed = 0
        # Retry up to 3 times with increasing delay for 529 overload errors
        for attempt in range(3):
            try:
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=800,
                    system=f"""You are a Kenya MSME business advisor. Answer accurately
using the context. Be specific — mention actual Kenyan institutions,
laws, costs and processes.

CONTEXT:
{context if context else 'No specific documents found.'}""",
                    messages=[{"role": "user", "content": question}]
                )
                answer  = response.content[0].text
                elapsed = time.time() - start
                break
            except Exception as e:
                err_str = str(e)
                if "529" in err_str or "overload" in err_str.lower():
                    wait = (attempt + 1) * 10
                    print(f"  Overloaded — waiting {wait}s before retry {attempt+1}/3...")
                    time.sleep(wait)
                else:
                    print(f"  ERROR: {e}")
                    break
        if answer is None:
            answer  = "ERROR: API unavailable after 3 retries"
            elapsed = 0

        scoring = score_answer(
            answer,
            test["must_contain"],
            test["must_not_contain"]
        )
        score = scoring["score"]
        total_score += score

        print(f"  Score: {score}/5 ({scoring['rating']}) | "
              f"{elapsed:.1f}s | {scoring['word_count']} words")
        if scoring["kw_missed"]:
            print(f"  Missing: {scoring['kw_missed']}")

        results.append({
            "id":            qid,
            "category":      category,
            "question":      question,
            "score":         score,
            "max_score":     5,
            "rating":        scoring["rating"],
            "kw_score":      scoring["kw_score"],
            "rel_score":     scoring["rel_score"],
            "len_score":     scoring["len_score"],
            "ken_score":     scoring["ken_score"],
            "kw_matched":    ", ".join(scoring["kw_matched"]),
            "kw_missed":     ", ".join(scoring["kw_missed"]),
            "word_count":    scoring["word_count"],
            "response_time": round(elapsed, 2),
            "sources_found": len(sources),
            "sources":       " | ".join(sources),
            "answer_preview":answer[:200].replace("\n", " "),
        })
        time.sleep(3)

    return results, total_score


def print_and_save_report(results, total_score):
    total_q   = len(results)
    avg_score = total_score / total_q
    accuracy  = sum(1 for r in results if r["score"] >= 4) / total_q * 100

    cat_scores = defaultdict(list)
    for r in results:
        cat_scores[r["category"]].append(r["score"])
    ratings = Counter(r["rating"] for r in results)

    print("\n" + "=" * 65)
    print("  EVALUATION SUMMARY")
    print("=" * 65)
    print(f"  Questions tested:    {total_q}")
    print(f"  Total score:         {total_score}/{total_q * 5}")
    print(f"  Average score:       {avg_score:.2f}/5.00")
    print(f"  Overall accuracy:    {avg_score/5*100:.1f}%")
    print(f"  Good/Excellent rate: {accuracy:.0f}%")

    print("\n  Rating distribution:")
    for rating in ["Excellent", "Good", "Partial", "Weak", "Poor"]:
        count = ratings.get(rating, 0)
        bar   = "█" * count
        print(f"    {rating:<12} {count:>2}  {bar}")

    print("\n  By category:")
    for cat, scores in sorted(cat_scores.items()):
        avg = sum(scores) / len(scores)
        print(f"    {cat:<25} {avg:.1f}/5.0  ({len(scores)} Qs)")

    # Save CSV
    csv_path = LOG_DIR / "evaluation_results.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    # Save report
    rpt_path = LOG_DIR / "evaluation_report.txt"
    with open(rpt_path, "w", encoding="utf-8") as f:
        f.write("KENYA MSME ADVISOR — EVALUATION REPORT\n")
        f.write("=" * 60 + "\n")
        f.write(f"Date:              {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"Questions tested:  {total_q}\n")
        f.write(f"Total score:       {total_score}/{total_q*5}\n")
        f.write(f"Average score:     {avg_score:.2f}/5.00\n")
        f.write(f"Overall accuracy:  {avg_score/5*100:.1f}%\n")
        f.write(f"Good/Excellent:    {accuracy:.0f}%\n\n")
        f.write("RATING DISTRIBUTION\n" + "-"*40 + "\n")
        for rating in ["Excellent","Good","Partial","Weak","Poor"]:
            count = ratings.get(rating, 0)
            f.write(f"{rating:<12} {count:>2} ({count/total_q*100:.0f}%)\n")
        f.write("\nCATEGORY BREAKDOWN\n" + "-"*40 + "\n")
        for cat, scores in sorted(cat_scores.items()):
            avg = sum(scores)/len(scores)
            f.write(f"{cat:<25} {avg:.1f}/5.0  ({len(scores)} questions)\n")
        f.write("\nDETAILED RESULTS\n" + "-"*40 + "\n")
        for r in results:
            f.write(f"\nQ{r['id']:02d} [{r['category']}] {r['score']}/5 ({r['rating']})\n")
            f.write(f"     Q: {r['question'][:70]}\n")
            f.write(f"     Matched:  {r['kw_matched'] or 'none'}\n")
            f.write(f"     Missed:   {r['kw_missed'] or 'none'}\n")
            f.write(f"     Sources:  {r['sources_found']}\n")
            f.write(f"     Time:     {r['response_time']}s\n")

    print(f"\n  Saved: {csv_path}")
    print(f"  Saved: {rpt_path}")
    print("\n✅ Evaluation complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Kenya MSME Advisor — Evaluation Framework"
    )
    parser.add_argument(
        "--category", type=str, default=None,
        help="Filter by category (e.g. 'Tax', 'Financing')"
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Limit number of questions to run"
    )
    args = parser.parse_args()

    # Load API key
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key or api_key == "your_actual_key_here":
        env_file = BASE_DIR / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()

    if not api_key or api_key == "your_actual_key_here":
        print("ERROR: No API key found.")
        sys.exit(1)

    print("=" * 65)
    print("  Kenya MSME Advisor — Evaluation Framework")
    print("=" * 65)
    print(f"  Questions file: {QUESTIONS_FILE}")

    questions = load_questions(
        category_filter=args.category,
        limit=args.limit
    )

    if not questions:
        print("No questions found matching your filters.")
        sys.exit(0)

    print(f"  Questions loaded: {len(questions)}")
    if args.category:
        print(f"  Category filter:  {args.category}")
    if args.limit:
        print(f"  Limit:            {args.limit}")

    results, total_score = run_evaluation(questions, api_key)
    print_and_save_report(results, total_score)
