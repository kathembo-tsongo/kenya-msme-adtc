"""
generate_compound_scenarios.py — Supplementary training data targeting
the compound-question deferral pattern observed in live testing.

Reuses the existing sampled chunks (finetune_data/sampled_chunks.jsonl)
but generates a NEW task type: realistic multi-detail business scenarios
(business type + county + other specifics combined) where the assistant
answers DIRECTLY using all provided details, never asking for more info.

Skips kb9_bank_lending — that KB has only 14 source chunks total, a hard
ceiling in the source corpus, not something more generation can fix.
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import anthropic

client = anthropic.Anthropic()

INPUT_FILE = "finetune_data/sampled_chunks.jsonl"
OUTPUT_FILE = "finetune_data/compound_scenarios.jsonl"
MODEL = "claude-haiku-4-5-20251001"
MAX_WORKERS = 8

SYSTEM_PROMPT = """You generate training examples for fine-tuning a Kenyan MSME \
regulatory advisory assistant. You will be given ONE raw text chunk from a \
Kenyan regulatory/legal/tax source. Generate exactly ONE realistic, compound \
scenario question paired with a direct, confident answer.

The user question MUST combine multiple specific business details in one \
message — for example: business type (retail shop, salon, transport, \
consultancy, etc.) AND a Kenyan county/location AND at least one more detail \
(employee count, revenue figure, or similar). Write it the way a real business \
owner would naturally phrase it, all in one message.

Rules:
- Never introduce facts, numbers, or claims not present in the source text.
- CRITICAL: The assistant MUST answer directly and completely using the \
details already given in the question. NEVER ask for more information, \
NEVER request the business name, NEVER say you need more details before \
you can help. The user has already given you everything you need — use it.
- CRITICAL: Never refer to "the source text", "the source material", or any \
variant of these phrases. Answer as if this is your own expert knowledge.
- A brief closing suggestion to confirm details with the relevant authority \
is fine ONLY as the final sentence, never as a substitute for a real answer.
- Write as if advising a real Kenyan MSME operator — plain, practical \
language, not legalese.
- Output ONLY valid JSON with keys "instruction" and "response". No markdown \
fences, no commentary.
"""

COUNTIES = [
    "Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret", "Kajiado",
    "Machakos", "Kiambu", "Meru", "Nyeri", "Kakamega", "Kericho",
]

BUSINESS_TYPES = [
    "retail shop", "salon", "transport (matatu) business", "restaurant",
    "consultancy", "wholesale trading business", "agri-input supply shop",
    "tailoring business", "hardware store", "boutique",
]


def generate_example(chunk_record, idx):
    county = COUNTIES[idx % len(COUNTIES)]
    biz_type = BUSINESS_TYPES[idx % len(BUSINESS_TYPES)]

    user_msg = (
        f"Source text:\n\"\"\"{chunk_record['text'][:2000]}\"\"\"\n\n"
        f"Generate one compound scenario example. The business owner should "
        f"mention running a {biz_type} in {county} County, plus at least one "
        f"other specific detail (employees, revenue, or similar), all in one "
        f"natural question."
    )

    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=600,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        text = resp.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        parsed = json.loads(text)
        if "instruction" in parsed and "response" in parsed and parsed["response"]:
            return {
                "messages": [
                    {"role": "system", "content": (
                        "You are a helpful assistant advising Kenyan MSME "
                        "operators on tax, registration, financing, and "
                        "regulatory compliance."
                    )},
                    {"role": "user", "content": parsed["instruction"]},
                    {"role": "assistant", "content": parsed["response"]},
                ],
                "_meta": {
                    "kb_id": chunk_record["kb_id"],
                    "kb_name": chunk_record["kb_name"],
                    "task_type": "compound_scenario",
                },
            }
    except Exception as e:
        print(f"  Error on chunk {idx}: {e}")
    return None


def main():
    chunks = []
    with open(INPUT_FILE) as f:
        for line in f:
            record = json.loads(line)
            if record["kb_id"] != "kb9_bank_lending":
                chunks.append(record)

    print(f"Generating compound-scenario examples from {len(chunks)} chunks "
          f"(excluding kb9_bank_lending)...")

    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(generate_example, chunk, i): i
            for i, chunk in enumerate(chunks)
        }
        completed = 0
        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)
            completed += 1
            if completed % 50 == 0:
                print(f"Completed {completed}/{len(chunks)} chunks")

    with open(OUTPUT_FILE, "w") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Done. {len(results)} compound-scenario examples written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
