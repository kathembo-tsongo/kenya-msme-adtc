"""
Pre-filter for generated training examples. Three-way split:
  1. DISCARD  — degenerate examples (refusals about "corrupted"/"unreadable"
     source text) that should never be in the training set at all.
  2. CLEAN    — no unsupported numbers found (checking against BOTH the
     source chunk text AND the user's own turn, since analysis-type
     scenarios legitimately introduce numbers the assistant may reference).
  3. FLAGGED  — genuinely unsupported numbers; needs manual review.
"""
import json
import re
from pathlib import Path

INPUT_FILE = Path("finetune_data/training_data.jsonl")
CLEAN_FILE = Path("finetune_data/training_data_clean.jsonl")
FLAGGED_FILE = Path("finetune_data/flagged_for_review.jsonl")
DISCARD_FILE = Path("finetune_data/discarded_degenerate.jsonl")

NUMERIC_RE = re.compile(
    r"\b(?:KES|Ksh|Sh\.?)\s?[\d,]+(?:\.\d+)?\b"
    r"|\b\d+(?:\.\d+)?%"
    r"|\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b"
    r"|\b\d{4}\b"
    r"|\b\d+(?:\.\d+)?\b",
    re.IGNORECASE,
)

DEGENERATE_PATTERNS = re.compile(
    r"\b(corrupt(ed)?|unreadable|can't (read|extract)|cannot (read|extract)|"
    r"doesn't contain clear|improperly formatted|garbled|not legible)\b",
    re.IGNORECASE,
)


def normalize(s: str) -> str:
    return re.sub(r"[,\s]", "", s.lower())


def extract_numeric_tokens(text: str) -> set[str]:
    return {normalize(m) for m in NUMERIC_RE.findall(text)}


def is_degenerate(assistant_msg: str) -> bool:
    return bool(DEGENERATE_PATTERNS.search(assistant_msg))


LIST_MARKER_RE = re.compile(r"(?m)^\s*(?:[-*]\s*)?\d{1,2}\.\s+")


def strip_list_markers(text: str) -> str:
    return LIST_MARKER_RE.sub('', text)


def check_grounding(response: str, source_text: str, user_msg: str) -> list[str]:
    response_clean = strip_list_markers(response)
    response_tokens = extract_numeric_tokens(response_clean)
    allowed = normalize(source_text) + "|" + normalize(user_msg)

    unsupported = []
    for token in response_tokens:
        digits_only = re.sub(r"[a-z%]", "", token)
        if digits_only and digits_only not in allowed:
            unsupported.append(token)
    return unsupported


def main():
    total = 0
    discarded = 0
    flagged = 0

    with open(INPUT_FILE) as in_f, \
         open(CLEAN_FILE, "w") as clean_f, \
         open(FLAGGED_FILE, "w") as flagged_f, \
         open(DISCARD_FILE, "w") as discard_f:

        for line in in_f:
            record = json.loads(line)
            total += 1

            user_msg = next((m["content"] for m in record["messages"] if m["role"] == "user"), "")
            assistant_msg = next((m["content"] for m in record["messages"] if m["role"] == "assistant"), "")
            source_text = record["_meta"].get("source_text", "")

            if is_degenerate(assistant_msg):
                discarded += 1
                discard_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                continue

            unsupported = check_grounding(assistant_msg, source_text, user_msg)

            if unsupported:
                flagged += 1
                record["_meta"]["unsupported_numeric_tokens"] = unsupported
                flagged_f.write(json.dumps(record, ensure_ascii=False) + "\n")
            else:
                clean_f.write(json.dumps(record, ensure_ascii=False) + "\n")

    clean_count = total - discarded - flagged
    print(f"Total examples:      {total}")
    print(f"Discarded (degenerate): {discarded} ({100*discarded/total:.1f}%)")
    print(f"Flagged for review:  {flagged} ({100*flagged/total:.1f}%)")
    print(f"Clean (auto-pass):   {clean_count} ({100*clean_count/total:.1f}%)")
    print(f"\nClean data:    {CLEAN_FILE}")
    print(f"Flagged data:  {FLAGGED_FILE}  <- review these by hand")
    print(f"Discarded:     {DISCARD_FILE}  <- degenerate, not used")


if __name__ == "__main__":
    main()
