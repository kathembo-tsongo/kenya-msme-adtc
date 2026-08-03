"""
build_index.py — Build a TF-IDF retrieval index over documents/kb*/*.
"""
import json
import os
import pickle
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer

DOCS_DIR = Path("documents")
INDEX_OUT = Path("rag_index.pkl")

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200


def read_text_file(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return ""


def chunk_text(text: str, kb_name: str, source_file: str):
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end].strip()
        if chunk:
            chunks.append({
                "text": chunk,
                "kb": kb_name,
                "source": source_file,
            })
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def build_index():
    all_chunks = []

    kb_dirs = sorted([d for d in DOCS_DIR.iterdir() if d.is_dir()])
    print(f"Found {len(kb_dirs)} knowledge base folders")

    for kb_dir in kb_dirs:
        kb_name = kb_dir.name
        files = list(kb_dir.rglob("*"))
        files = [f for f in files if f.is_file()]
        print(f"  {kb_name}: {len(files)} files")

        for fpath in files:
            text = read_text_file(fpath)
            if not text:
                continue
            chunks = chunk_text(text, kb_name, str(fpath.relative_to(DOCS_DIR)))
            all_chunks.extend(chunks)

    print(f"\nTotal chunks: {len(all_chunks)}")

    if not all_chunks:
        print("ERROR: no chunks produced — check documents/ contains readable text files")
        return

    texts = [c["text"] for c in all_chunks]

    vectorizer = TfidfVectorizer(
        max_features=50000,
        ngram_range=(1, 2),
        stop_words="english",
        sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform(texts)

    print(f"TF-IDF matrix shape: {matrix.shape}")

    with open(INDEX_OUT, "wb") as f:
        pickle.dump({
            "vectorizer": vectorizer,
            "matrix": matrix,
            "chunks": all_chunks,
        }, f)

    print(f"Saved index to {INDEX_OUT}")


if __name__ == "__main__":
    build_index()
