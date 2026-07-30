"""
Stage 2: For each sampled chunk, generate grounded instruction-tuning examples
across three task types (summarization, drafting, analysis) matching the
ADTC Corporate/Enterprise track description. Uses the Anthropic API,
concurrently for speed.

Requires: ANTHROPIC_API_KEY environment variable set.
Install:  pip install anthropic --break-system-packages
"""
import json
import os
import time
import random
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import anthropic

random.seed(42)

INPUT_FILE = Path("finetune_data/sampled_chunks.jsonl")
OUTPUT_FILE = Path("finetune_data/training_data.jsonl")

MODEL = "claude-haiku-4-5-20251001"
TASK_TYPES = ["summarization", "drafting", "analysis"]
MAX_WORKERS = 8  # concurrent requests

SYSTEM_PROMPT = """You generate training examples for fine-tuning a Kenyan MSME \
regulatory advisory assistant. You will be given ONE raw text chunk from a \
Kenyan regulatory/legal/tax source. Generate exactly ONE instruction-tuning \
example of the requested task type, grounded STRICTLY in the provided text.

Rules:
- Never introduce facts, numbers, or claims not present in the source text.
- Write as if advising a real Kenyan MSME operator (retail shop, small \
  business, sole proprietor) — plain, practical language, not legalese.
- Output ONLY valid JSON, no markdown fences, no commentary.

Task type definitions:
- summarization: user asks for the key takeaway of a regulatory topic; \
  assistant gives a plain-language summary of what the source text says.
- drafting: user asks for a structured, actionable document (checklist, \
  step-by-step guide) that the source text's content supports.
- analysis: user describes a small, specific business scenario (e.g. "a \
  home-based catering business with 2 employees") and asks which \
  obligations/rules from the source text apply to it; assistant reasons \
  from the source text to the scenario.

Output JSON schema:
{"instruction": "<user message>", "response": "<assistant answer>"}
"""

client = anthropic.Anthropic()
write_lock = threading.Lock()


def generate_example(chunk_text: str, kb_name: str, task_type: str) -> dict | None:
    user_msg = f"""Task type: {task_type}
Source KB: {kb_name}
Source text:
\"\"\"
{chunk_text}
\"\"\"

Generate one {task_type} instruction-tuning example as specified."""

    for attempt in range(3):
        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=800,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
            )
            raw = resp.content[0].text.strip()
            raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            parsed = json.loads(raw)
            if "instruction" in parsed and "response" in parsed:
                return parsed
            return None
        except (json.JSONDecodeError, anthropic.APIError) as e:
            time.sleep(2 ** attempt)
    return None


def process_chunk(chunk: dict) -> list[dict]:
    chosen_tasks = random.sample(TASK_TYPES, k=random.choice([1, 2]))
    records = []
    for task_type in chosen_tasks:
        example = generate_example(chunk["text"], chunk["kb_name"], task_type)
        if example is None:
            continue
        records.append({
            "messages": [
                {"role": "system", "content": "You are a helpful assistant advising Kenyan MSME operators on tax, registration, financing, and regulatory compliance."},
                {"role": "user", "content": example["instruction"]},
                {"role": "assistant", "content": example["response"]},
            ],
            "_meta": {"kb_id": chunk["kb_id"], "task_type": task_type, "source_filename": chunk["source_filename"], "source_text": chunk["text"]},
        })
    return records


def main():
    chunks = [json.loads(line) for line in open(INPUT_FILE)]
    print(f"Processing {len(chunks)} chunks with {MAX_WORKERS} workers...")

    completed = 0
    with open(OUTPUT_FILE, "w") as out_f, ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_chunk, chunk): chunk for chunk in chunks}
        for future in as_completed(futures):
            records = future.result()
            with write_lock:
                for record in records:
                    out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                out_f.flush()
            completed += 1
            if completed % 50 == 0:
                print(f"Completed {completed}/{len(chunks)} chunks")

    print(f"\nDone. Training data written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
