"""
Stage 1: Load all knowledge_base/*/chunks.json, clean scraping artifacts,
remove near-duplicates, and take a stratified sample per KB for Q&A generation.
"""
import json
import re
import hashlib
import random
from pathlib import Path

random.seed(42)

KB_DIR = Path("knowledge_base")
OUTPUT_FILE = Path("finetune_data/sampled_chunks.jsonl")
OUTPUT_FILE.parent.mkdir(exist_ok=True)

MIN_CHARS = 250
MAX_CHARS = 1800
SAMPLE_PER_KB = 200  # adjust based on total time/cost budget

MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(https?://[^\)]+\)")
WHITESPACE_RE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    text = MD_LINK_RE.sub(r"\1", text)  # strip markdown links, keep visible text
    text = WHITESPACE_RE.sub(" ", text).strip()
    return text


def chunk_hash(text: str) -> str:
    normalized = re.sub(r"[^a-z0-9]", "", text.lower())[:300]
    return hashlib.md5(normalized.encode()).hexdigest()


all_sampled = []

for kb_file in sorted(KB_DIR.glob("*/chunks.json")):
    with open(kb_file) as f:
        data = json.load(f)

    kb_id = data.get("kb_id", kb_file.parent.name)
    kb_name = data.get("kb_name", kb_id)
    chunks = data["chunks"]
    metadata = data["metadata"]

    if len(chunks) != len(metadata):
        print(f"WARNING: {kb_id} — chunks ({len(chunks)}) != metadata ({len(metadata)}), skipping")
        continue

    seen_hashes = set()
    candidates = []
    for text, meta in zip(chunks, metadata):
        cleaned = clean_text(text)
        if not (MIN_CHARS <= len(cleaned) <= MAX_CHARS):
            continue
        h = chunk_hash(cleaned)
        if h in seen_hashes:
            continue
        seen_hashes.add(h)
        candidates.append({
            "kb_id": kb_id,
            "kb_name": kb_name,
            "source_filename": meta.get("filename", "unknown"),
            "text": cleaned,
        })

    sample_size = min(SAMPLE_PER_KB, len(candidates))
    sampled = random.sample(candidates, sample_size)
    all_sampled.extend(sampled)

    print(f"{kb_id:35s} raw={len(chunks):5d}  after-filter={len(candidates):5d}  sampled={sample_size:4d}")

with open(OUTPUT_FILE, "w") as f:
    for item in all_sampled:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print(f"\nTotal sampled chunks: {len(all_sampled)}")
print(f"Written to: {OUTPUT_FILE}")
