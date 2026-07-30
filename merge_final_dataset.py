"""
Merge clean + flagged (minus manually-excluded indices) into the final
fine-tuning dataset. Strips the _meta field before writing (not needed
for actual fine-tuning, and keeps the file lean).
"""
import json
from pathlib import Path

CLEAN_FILE = Path("finetune_data/training_data_clean.jsonl")
FLAGGED_FILE = Path("finetune_data/flagged_for_review.jsonl")
FINAL_FILE = Path("finetune_data/training_data_final.jsonl")

# Indices (0-based, matching the order in flagged_for_review.jsonl / the
# _readable.txt export) to EXCLUDE as genuine fabrications after manual review.
EXCLUDED_FLAGGED_INDICES = {4}  # update this set after checking #4's full source

def main():
    clean = [json.loads(line) for line in open(CLEAN_FILE)]
    flagged = [json.loads(line) for line in open(FLAGGED_FILE)]

    kept_flagged = [r for i, r in enumerate(flagged) if i not in EXCLUDED_FLAGGED_INDICES]

    final = clean + kept_flagged

    with open(FINAL_FILE, "w") as out:
        for r in final:
            r.pop("_meta", None)
            out.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Clean:            {len(clean)}")
    print(f"Flagged, kept:    {len(kept_flagged)} (excluded {len(EXCLUDED_FLAGGED_INDICES)})")
    print(f"Final total:      {len(final)}")
    print(f"Written to: {FINAL_FILE}")

if __name__ == "__main__":
    main()
