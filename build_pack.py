#!/usr/bin/env python3
"""
build_pack.py -- build the Rafiki wa Biashara knowledge pack for the phone app.

Produces a single SQLite file (rafiki_pack.db) containing:
  - canned (verified) answers in English and Kiswahili
  - the topic keyword map used to route questions to canned answers
  - the digest-override keyword list
  - cleaned corpus chunks with an FTS4 full-text index (BM25 ranking done in app code)
  - metadata: pack version, "accurate as of" date, source commit, counts

It READS rag_server.py with the ast module -- it never imports or runs it,
so no server starts and no model loads.

Usage (from ~/Programming Projects/kenya-msme-adtc):
    python3 build_pack.py --as-of 2026-09-29
"""
import argparse
import ast
import datetime as dt
import hashlib
import json
import os
import pickle
import re
import sqlite3
import subprocess
import sys
import warnings
from collections import defaultdict

import query_pack as qp

WANTED = ["CANNED_ANSWERS", "CANNED_ANSWERS_SW", "TOPIC_KEYWORDS", "DIGEST_OVERRIDE_KEYWORDS", "CANNED_SOURCES", "CANNED_FOLLOWUPS"]
TEXT_KEYS = ("text", "content", "chunk", "page_content")
SOURCE_KEYS = ("source", "file", "filename", "doc", "document", "path")
KB_KEYS = ("kb", "category", "collection", "folder")
PACK_FORMAT = "2"   # 2: adds the routing `config` table


# ---------------------------------------------------------------- extraction
def extract_literals(path):
    """Pull the top-level dict/list literals out of rag_server.py without running it."""
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=path)
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names, value = [node.target.id], node.value
        else:
            continue
        for name in names:
            if name in WANTED:
                try:
                    found[name] = ast.literal_eval(value)  # later assignment wins, as at runtime
                except ValueError as e:
                    sys.exit(f"ERROR: {name} in {path} is not a plain literal ({e}).\n"
                             f"Paste its definition and the script can be adapted.")
    missing = [n for n in WANTED if n not in found]
    if missing:
        sys.exit(f"ERROR: not found at top level of {path}: {missing}")
    return found


def _pick(d, keys):
    for k in keys:
        if k in d and d[k]:
            return d[k]
    return None


def load_chunks(path):
    """Load chunk texts + source metadata from rag_index.pkl (vectorizer/matrix are ignored)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # sklearn version-mismatch warnings don't matter here
        with open(path, "rb") as f:
            data = pickle.load(f)
    chunks = data["chunks"]
    first = chunks[0]
    if isinstance(first, dict):
        print(f"Chunk fields found: {sorted(first.keys())}")
    else:
        print(f"Chunk type: {type(first).__name__}")

    out = []
    for c in chunks:
        if isinstance(c, str):
            text, source, kb = c, "", ""
        elif isinstance(c, dict):
            text = _pick(c, TEXT_KEYS)
            source = _pick(c, SOURCE_KEYS) or ""
            kb = _pick(c, KB_KEYS) or ""
        elif isinstance(c, (tuple, list)):
            text = c[0]
            source = c[1] if len(c) > 1 else ""
            kb = ""
        else:
            sys.exit(f"ERROR: unexpected chunk type {type(c).__name__}; paste one chunk and "
                     f"the loader can be adapted.")
        if not text:
            continue
        source = str(source)
        if not kb:
            m = re.search(r"(kb\d+)", source, re.IGNORECASE)
            kb = m.group(1).lower() if m else ""
        out.append((str(text), source, str(kb)))

    if out and not any(t[1] for t in out):
        print("WARNING: no source field detected in chunks -- provenance labels will be empty.")
    return out


# ---------------------------------------------------------------- cleaning
def strip_boilerplate(chunks, min_sources, max_len, min_chunk_chars):
    """Remove short lines that repeat across many different documents
    (e.g. KRA navigation menus), then drop chunks left too short, and exact duplicates."""
    line_docs = defaultdict(set)
    for i, (text, source, _) in enumerate(chunks):
        doc = source or f"#{i}"
        for line in {l.strip() for l in text.splitlines()}:
            # Only multi-word lines can be boilerplate. Bare numbers are often table cells
            # (rates, days, amounts), and single words ("and", "Total", "Mombasa") are often
            # wrapped-sentence fragments or table labels -- never strip those.
            if line and len(line) <= max_len and len(re.findall(r"[A-Za-z]{2,}", line)) >= 2:
                line_docs[line].add(doc)
    boiler = {l for l, docs in line_docs.items() if len(docs) >= min_sources}

    cleaned, seen, dropped_short, dropped_dup = [], set(), 0, 0
    for text, source, kb in chunks:
        kept = [l for l in text.splitlines() if l.strip() not in boiler]
        new = re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()
        if len(new) < min_chunk_chars:
            dropped_short += 1
            continue
        key = hashlib.sha1(new.encode("utf-8")).hexdigest()
        if key in seen:
            dropped_dup += 1
            continue
        seen.add(key)
        cleaned.append((new, source, kb))

    top = sorted(boiler, key=lambda l: -len(line_docs[l]))[:40]
    return cleaned, boiler, top, line_docs, dropped_short, dropped_dup


# ---------------------------------------------------------------- writing
def git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return "unknown"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_pack(out, lit, chunks, meta, general):
    if os.path.exists(out):
        os.remove(out)
    db = sqlite3.connect(out)
    db.executescript("""
        CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE canned(topic TEXT PRIMARY KEY, answer_en TEXT, answer_sw TEXT);
        CREATE TABLE topic_keywords(topic TEXT NOT NULL, priority INTEGER NOT NULL,
                                    keyword TEXT NOT NULL);
        CREATE INDEX idx_topic_keywords_priority ON topic_keywords(priority);
        CREATE TABLE digest_override_keywords(keyword TEXT NOT NULL);
        CREATE TABLE general_topics(topic TEXT PRIMARY KEY);
        CREATE TABLE config(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE config_list(key TEXT NOT NULL, pos INTEGER NOT NULL, item TEXT NOT NULL);
        CREATE TABLE config_num(key TEXT PRIMARY KEY, value REAL NOT NULL);
        CREATE TABLE config_str(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE chunks(id INTEGER PRIMARY KEY, kb TEXT, source TEXT, body TEXT NOT NULL);
        CREATE VIRTUAL TABLE chunks_fts USING fts4(content="chunks", body, tokenize=porter);
        CREATE VIRTUAL TABLE canned_fts USING fts4(body, tokenize=porter);
    """)

    # Provenance: where each verified answer was checked (optional in rag_server.py).
    # Contextual follow-ups (optional in rag_server.py).
    db.execute("CREATE TABLE followups(topic TEXT, target TEXT, cue TEXT, ord INTEGER)")
    _n = 0
    for topic, targets in lit.get("CANNED_FOLLOWUPS", {}).items():
        for target, cues in targets.items():
            for cue in cues:
                _n += 1
                db.execute("INSERT INTO followups VALUES (?,?,?,?)", (topic, target, cue.lower(), _n))
    db.execute("CREATE TABLE canned_sources(topic TEXT PRIMARY KEY, source TEXT NOT NULL, "
               "url TEXT NOT NULL, checked TEXT NOT NULL)")
    for topic, (source, url, checked) in lit.get("CANNED_SOURCES", {}).items():
        db.execute("INSERT INTO canned_sources VALUES (?,?,?,?)", (topic, source, url, checked))
    en, sw = lit["CANNED_ANSWERS"], lit["CANNED_ANSWERS_SW"]
    for topic in list(en) + [t for t in sw if t not in en]:
        db.execute("INSERT INTO canned VALUES (?,?,?)", (topic, en.get(topic), sw.get(topic)))

    for priority, (topic, kws) in enumerate(lit["TOPIC_KEYWORDS"].items()):
        for kw in kws:
            db.execute("INSERT INTO topic_keywords VALUES (?,?,?)", (topic, priority, kw))

    # Searchable copy of each verified answer (topic name + keywords + both languages),
    # so a question that misses every keyword can still find its verified answer.
    for rowid, topic, a_en, a_sw in db.execute(
            "SELECT rowid, topic, answer_en, answer_sw FROM canned").fetchall():
        kws = " ".join(k for (k,) in db.execute(
            "SELECT keyword FROM topic_keywords WHERE topic = ?", (topic,)))
        db.execute("INSERT INTO canned_fts(docid, body) VALUES (?,?)",
                   (rowid, f"{topic.replace('_', ' ')} {kws} {a_en or ''} {a_sw or ''}"))

    for kw in lit["DIGEST_OVERRIDE_KEYWORDS"]:
        db.execute("INSERT INTO digest_override_keywords VALUES (?)", (kw,))

    for topic in general:
        db.execute("INSERT INTO general_topics VALUES (?)", (topic,))

    # Routing word lists and thresholds, from query_pack.py (the single source of truth).
    # The phone reads these, so a routing fix ships as a new pack, not a new app.
    for key, value in qp.config_values().items():
        db.execute("INSERT INTO config VALUES (?,?)", (key, json.dumps(value, ensure_ascii=False)))
        # the same values in flat tables, so the Kotlin router needs no JSON parser
        if isinstance(value, list):
            db.executemany("INSERT INTO config_list VALUES (?,?,?)",
                           [(key, i, item) for i, item in enumerate(value)])
        elif isinstance(value, dict):
            db.executemany("INSERT INTO config_num VALUES (?,?)", list(value.items()))
        else:
            db.execute("INSERT INTO config_str VALUES (?,?)", (key, value))

    db.executemany("INSERT INTO chunks(kb, source, body) VALUES (?,?,?)",
                   [(kb, src, text) for text, src, kb in chunks])
    db.execute("INSERT INTO chunks_fts(docid, body) SELECT id, body FROM chunks")
    db.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('optimize')")

    for k, v in meta.items():
        db.execute("INSERT INTO meta VALUES (?,?)", (k, str(v)))
    db.commit()
    db.execute("VACUUM")
    db.close()


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--server", default="rag_server.py")
    ap.add_argument("--index", default="rag_index.pkl")
    ap.add_argument("--out", default="rafiki_pack.db")
    ap.add_argument("--as-of", required=True,
                    help="date the verified facts were last checked, YYYY-MM-DD (shown to operators)")
    ap.add_argument("--boiler-min-sources", type=int, default=15,
                    help="a short line repeated in at least this many documents is treated as boilerplate")
    ap.add_argument("--boiler-max-len", type=int, default=120)
    ap.add_argument("--min-chunk-chars", type=int, default=80)
    ap.add_argument("--general", default="license,nssf,loan",
                    help="comma-separated umbrella topics: they answer only when no more "
                         "specific topic also matches the question")
    args = ap.parse_args()

    dt.date.fromisoformat(args.as_of)  # fail early on a bad date

    lit = extract_literals(args.server)
    en, sw, kw = lit["CANNED_ANSWERS"], lit["CANNED_ANSWERS_SW"], lit["TOPIC_KEYWORDS"]
    print(f"Canned answers: {len(en)} EN, {len(sw)} SW | keyword topics: {len(kw)} | "
          f"digest-override keywords: {len(lit['DIGEST_OVERRIDE_KEYWORDS'])}")

    unreachable = sorted((set(en) | set(sw)) - set(kw))
    no_answer = sorted(set(kw) - set(en) - set(sw))
    sw_missing = sorted(set(en) - set(sw))
    if unreachable:
        print(f"WARNING: canned topics with no keywords (can never be matched): {unreachable}")
    if no_answer:
        print(f"WARNING: keyword topics with no canned answer: {no_answer}")
    if sw_missing:
        print(f"NOTE: {len(sw_missing)} topics have no Kiswahili answer (English will be shown): {sw_missing}")

    general = [t.strip() for t in args.general.split(",") if t.strip()]
    unknown = [t for t in general if t not in kw]
    if unknown:
        sys.exit(f"ERROR: --general names topics that don't exist: {unknown}")
    print(f"General (umbrella) topics: {general}")

    raw = load_chunks(args.index)
    print(f"Chunks loaded: {len(raw)}")
    chunks, boiler, top, line_docs, short, dup = strip_boilerplate(
        raw, args.boiler_min_sources, args.boiler_max_len, args.min_chunk_chars)
    print(f"Boilerplate lines removed: {len(boiler)} distinct | chunks dropped: "
          f"{short} too short, {dup} duplicates | chunks kept: {len(chunks)}")
    if top:
        print("\nMost-repeated boilerplate lines (check none of these are real content):")
        for line in top:
            print(f"  [{len(line_docs[line]):>4} docs] {line[:90]}")
        print()

    meta = {
        "pack_format": PACK_FORMAT,
        "built_at": dt.datetime.now().isoformat(timespec="seconds"),
        "as_of": args.as_of,
        "source_commit": git_commit(),
        "rag_server_sha256": sha256_file(args.server),
        "canned_count": len(set(en) | set(sw)),
        "chunk_count": len(chunks),
        "boilerplate_lines_removed": len(boiler),
    }
    meta["general_topics"] = ",".join(general)
    write_pack(args.out, lit, chunks, meta, general)
    size_mb = os.path.getsize(args.out) / 1e6
    print(f"Wrote {args.out} ({size_mb:.1f} MB)")
    for k, v in meta.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
