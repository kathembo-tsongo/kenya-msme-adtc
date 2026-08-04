"""
build_index.py -- Build a TF-IDF retrieval index over documents/kb*/*.
Properly extracts text from PDFs (including files with a .txt extension
that actually contain raw PDF binary data due to an earlier scraping bug).
"""
import pickle
from pathlib import Path

from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer

DOCS_DIR = Path("documents")
INDEX_OUT = Path("rag_index.pkl")

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200


def is_pdf_content(raw_bytes: bytes) -> bool:
    """Detect PDF content regardless of file extension."""
    return b"%PDF" in raw_bytes[:2000]


def extract_pdf_text(path: Path) -> str:
    """Extract text from a PDF file using pypdf."""
    try:
        reader = PdfReader(str(path))
        pages_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)
        return "\n".join(pages_text)
    except Exception as e:
        print(f"    WARNING: failed to extract PDF text from {path.name}: {e}")
        return ""


def read_text_file(path: Path) -> str:
    """Read a plain text file, trying common encodings."""
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return ""


def read_document(path: Path) -> str:
    """Read any document, detecting real PDF content regardless of extension.
    Falls back to a sibling _ocr.txt file if normal PDF extraction returns
    little/no text (scanned/image-only PDFs with no text layer)."""
    with open(path, "rb") as f:
        raw_start = f.read(2000)

    if path.suffix.lower() == ".pdf" or is_pdf_content(raw_start):
        text = extract_pdf_text(path)
        if len(text.strip()) < 20:
            ocr_path = path.with_name(path.stem + "_ocr.txt")
            if ocr_path.exists():
                print(f"    Using OCR fallback for {path.name}")
                return read_text_file(ocr_path)
        return text
    else:
        return read_text_file(path)


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
    failed_files = []

    kb_dirs = sorted([d for d in DOCS_DIR.iterdir() if d.is_dir()])
    print(f"Found {len(kb_dirs)} knowledge base folders")

    for kb_dir in kb_dirs:
        kb_name = kb_dir.name
        files = [f for f in kb_dir.rglob("*") if f.is_file()]
        print(f"  {kb_name}: {len(files)} files")

        for fpath in files:
            text = read_document(fpath)
            if not text or len(text.strip()) < 20:
                failed_files.append(str(fpath.relative_to(DOCS_DIR)))
                continue
            chunks = chunk_text(text, kb_name, str(fpath.relative_to(DOCS_DIR)))
            all_chunks.extend(chunks)

    print(f"\nTotal chunks: {len(all_chunks)}")
    if failed_files:
        print(f"\nWARNING: {len(failed_files)} files produced no usable text:")
        for f in failed_files:
            print(f"  - {f}")

    if not all_chunks:
        print("ERROR: no chunks produced")
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
