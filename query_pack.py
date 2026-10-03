#!/usr/bin/env python3
"""
query_pack.py -- the phone app's routing logic, runnable from the terminal.

route() is the single source of truth: the Android app will port it line for
line, and eval_pack.py tests it. Order of checks:

  1. CHAT            greetings / thanks only            -> friendly reply, no search
  2. NOT_UNDERSTOOD  no word appears anywhere in pack   -> ask for English or Kiswahili
  3. FOLLOW_UP       "the above", "those links", ...    -> reuse the previous topic
  4. VERIFIED        topic keyword match                -> verified answer, no model
                     (+ follow-up search for specific words the answer doesn't cover)
  5. VERIFIED_SEARCH no keyword, but a verified answer's text closely matches
  6. FACTUAL         tax / licence / NSSF / loans ...   -> strict STRONG / PARTIAL / WEAK
                     (DIGEST flag: model + digest, no retrieval)
  7. ADVISORY        general business advice            -> model answers, labelled
                                                           "general advice, not verified"

Usage:
    python3 query_pack.py "What is the VAT registration threshold?"
    python3 query_pack.py --lang sw "Nitasajili biashara vipi?"
    python3 query_pack.py --info
"""
import argparse
import json
import math
import re
import sqlite3
import struct
import time

K1, B = 1.2, 0.75

# First-guess thresholds -- to be calibrated on the labelled set, not by hand.
STRONG_NORM, STRONG_COVERAGE, STRONG_FOCUS_TF = 0.65, 0.7, 2
PARTIAL_NORM, PARTIAL_COVERAGE = 0.45, 0.5
CANNED_SEARCH_NORM, CANNED_SEARCH_COVERAGE = 0.4, 0.6
MIN_SPECIFIC_IDF = 4.5   # a follow-up only fires for words at least this specific

STOPWORDS = set("""
ku na ya la wa za cha vya kwa ni
kufungua fungua kuanzisha anzisha
a an and are as at be by can do does for from how i if in is it me my of on or
should the to what when where which who why will with you your we our there this
that need much many get am was were has have had so but not no yes just also
now then about into than too very really please thank thanks hello hi hey dear
ok okay great good happens happen want wants go going know tell give
na ya wa kwa ni za la katika kama je gani nini vipi mimi yangu wangu nina
tafadhali asante sana naomba nataka
""".split())

SMALL_TALK = set("""
hello hi hey hallo thanks thank you ok okay great dear good morning afternoon evening
night nice cool fine understood noted welcome bye goodbye cheers alright sure yes no too
asante sana habari jambo sawa poa safi karibu mambo shikamoo nzuri ndiyo hapana pia
""".split())

# Asked of the phone, not the advisor: the app answers these from its own clock.
# The model has no clock and would invent an answer.
APP_INFO = re.compile(
    r"what time is it|what(?:'s| is) the time|tell me the time|time now|"
    r"what(?:'s| is) (?:the )?date|today'?s date|what day is (?:it|today)|saa ngapi|tarehe gani")

REFERENTIAL = [
    "the above", "details above", "mentioned above", "those links", "the links", "that link",
    "share the link", "more details on that", "tell me more", "explain more", "more on that",
    "hiyo", "hapo juu", "zaidi kuhusu hiyo",
]

# "I mean pochi la biashara" refines the previous question rather than starting a new one.
CLARIFICATION = re.compile(r"^\s*(?:i mean|i meant|what i mean is|namaanisha|nilimaanisha|yaani)\b[\s,:]*")

# Words that make a question FACTUAL: a wrong answer can cost money or break the law.
FACTUAL_WORDS = set("""
tax taxes kra vat paye itax etims pin tcc licence license licensing permit register
registration registered nssf shif sha nhif levy levies duty duties penalty penalty fine
fines law laws act legal compliance comply contract employ employee employer employment
wage wages salary payroll leave maternity paternity termination dismiss probation
fund funds loan loans lender interest rate rates insurance kebs import export customs
certificate tender tenders agpo hustler yedf wef uwezo sacco saccos bank banks mpesa
paybill till county government regulation regulations regulated
pochi safaricom ecitizen brs cbk kebs nema kephis keproba
kodi ushuru leseni kibali vibali usajili sajili kusajili kujisajili adhabu faini sheria
mkopo mikopo riba bima mshahara wafanyakazi mfanyakazi likizo serikali kaunti
""".split())


# ---------------------------------------------------------------- shared config
# The constants above are the defaults. build_pack.py writes them into the pack's
# `config` table, and route() loads them back from whatever pack it is given. The
# Android router reads the same table, so Python and phone can never drift apart.
def config_values():
    """Everything the router depends on, as JSON-serialisable values."""
    return {
        "stopwords": sorted(STOPWORDS),
        "small_talk": sorted(SMALL_TALK),
        "factual_words": sorted(FACTUAL_WORDS),
        "referential": list(REFERENTIAL),
        "app_info_regex": APP_INFO.pattern,
        "clarification_regex": CLARIFICATION.pattern,
        "thresholds": dict(
            k1=K1, b=B, strong_norm=STRONG_NORM, strong_coverage=STRONG_COVERAGE,
            strong_focus_tf=STRONG_FOCUS_TF, partial_norm=PARTIAL_NORM,
            partial_coverage=PARTIAL_COVERAGE, canned_search_norm=CANNED_SEARCH_NORM,
            canned_search_coverage=CANNED_SEARCH_COVERAGE, min_specific_idf=MIN_SPECIFIC_IDF),
    }


_loaded_from = None


def load_config(db):
    """Override the module defaults with the pack's config table (once per pack)."""
    global _loaded_from, STOPWORDS, SMALL_TALK, FACTUAL_WORDS, REFERENTIAL, APP_INFO, CLARIFICATION
    global K1, B, STRONG_NORM, STRONG_COVERAGE, STRONG_FOCUS_TF, PARTIAL_NORM, PARTIAL_COVERAGE
    global CANNED_SEARCH_NORM, CANNED_SEARCH_COVERAGE, MIN_SPECIFIC_IDF
    if _loaded_from is db:
        return
    _loaded_from = db
    try:
        cfg = {k: json.loads(v) for k, v in db.execute("SELECT key, value FROM config")}
    except sqlite3.OperationalError:
        return  # older pack without a config table: keep the defaults
    STOPWORDS, SMALL_TALK = set(cfg["stopwords"]), set(cfg["small_talk"])
    FACTUAL_WORDS, REFERENTIAL = set(cfg["factual_words"]), list(cfg["referential"])
    APP_INFO, CLARIFICATION = re.compile(cfg["app_info_regex"]), re.compile(cfg["clarification_regex"])
    t = cfg["thresholds"]
    K1, B = t["k1"], t["b"]
    STRONG_NORM, STRONG_COVERAGE, STRONG_FOCUS_TF = t["strong_norm"], t["strong_coverage"], t["strong_focus_tf"]
    PARTIAL_NORM, PARTIAL_COVERAGE = t["partial_norm"], t["partial_coverage"]
    CANNED_SEARCH_NORM, CANNED_SEARCH_COVERAGE = t["canned_search_norm"], t["canned_search_coverage"]
    MIN_SPECIFIC_IDF = t["min_specific_idf"]


# ---------------------------------------------------------------- text helpers
def words(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def query_terms(query, limit=12):
    terms, seen = [], set()
    for t in words(query):
        if len(t) < 2 or t in STOPWORDS or t in seen:
            continue
        seen.add(t)
        terms.append(t)
    return terms[:limit]


def is_small_talk(query):
    w = words(query)
    return bool(w) and all(t in SMALL_TALK for t in w)


def is_referential(query):
    q = query.lower()
    return any(p in q for p in REFERENTIAL)


def is_factual(query):
    return any(t in FACTUAL_WORDS or t.rstrip("s") in FACTUAL_WORDS for t in words(query))


# ---------------------------------------------------------------- verified answers
def canned_matches(db, query):
    """All verified topics whose keywords match, best first.
    - exact-substring pass first; the no-space pass runs only if nothing matched
    - a general (umbrella) topic loses to any specific topic that also matches
    - among the rest: longest matched keyword wins, then original order"""
    q = query.lower()
    q_ns = q.replace(" ", "")
    rows = db.execute(
        "SELECT topic, priority, keyword FROM topic_keywords ORDER BY priority, rowid").fetchall()
    general = {t for (t,) in db.execute("SELECT topic FROM general_topics")}
    for no_space in (False, True):
        best = {}
        for topic, priority, kw in rows:
            hit = kw.replace(" ", "") in q_ns if no_space else kw in q
            if hit and (topic not in best or len(kw) > best[topic][0]):
                best[topic] = (len(kw), priority)
        if best:
            return sorted(best, key=lambda t: (t in general, -best[t][0], best[t][1]))
    return []


def canned_source(db, topic):
    """(source, url, checked) for a verified answer, or None (also for packs built before sources)."""
    try:
        return db.execute("SELECT source, url, checked FROM canned_sources WHERE topic = ?",
                          (topic,)).fetchone()
    except Exception:
        return None


def canned_answer(db, topic, lang):
    en, sw = db.execute("SELECT answer_en, answer_sw FROM canned WHERE topic = ?", (topic,)).fetchone()
    return ((sw or en) if lang == "sw" else (en or sw)), en, sw


def uncovered_terms(query, topic, answer_text, db):
    """Question words that neither the verified answer nor the topic's keywords cover."""
    covered = set(words(answer_text or ""))
    for (kw,) in db.execute("SELECT keyword FROM topic_keywords WHERE topic = ?", (topic,)):
        covered.update(words(kw))

    def is_covered(t):
        return t in covered or t.rstrip("s") in covered or (t + "s") in covered
    return [t for t in query_terms(query) if not is_covered(t)]


# ---------------------------------------------------------------- search (BM25 over FTS4)
def parse_matchinfo(blob, n_terms):
    """matchinfo('pcnalx') for a one-column table -> (n_docs, avg_len, doc_len, [(tf, df), ...])."""
    v = struct.unpack(f"{len(blob) // 4}I", blob)
    return v[2], v[3] or 1, v[4], [(v[5 + 3 * i], v[7 + 3 * i]) for i in range(n_terms)]


def idf(n_docs, df):
    return math.log((n_docs - df + 0.5) / (df + 0.5) + 1.0)


def term_idfs(db, terms, table="chunks_fts"):
    """Corpus idf for each term (0 for terms that match nothing)."""
    out = {}
    for t in terms:
        row = db.execute(f"SELECT matchinfo({table}, 'pcnalx') FROM {table} "
                         f"WHERE {table} MATCH ? LIMIT 1", (t,)).fetchone()
        if row:
            n_docs, _, _, [(_, df)] = parse_matchinfo(row[0], 1)
            out[t] = idf(n_docs, df)
        else:
            out[t] = 0.0
    return out


def search(db, terms, top_k, focus=None, table="chunks_fts"):
    """BM25 over an FTS4 table. Returns (hits, idfs, focus); each hit is a dict with
    docid, score, norm (score / best possible), coverage (idf-weighted share of the
    question's words present) and focus_tf (count of the focus word)."""
    if not terms:
        return [], {}, None
    rows = db.execute(f"SELECT docid, matchinfo({table}, 'pcnalx') FROM {table} WHERE {table} MATCH ?",
                      (" OR ".join(terms),)).fetchall()
    if not rows:
        return [], {t: 0.0 for t in terms}, focus
    n_docs, _, _, first = parse_matchinfo(rows[0][1], len(terms))
    # A word the pack has never seen (df = 0) gets the HIGHEST weight, not zero: it is the
    # most specific word in the question ("Mweya"), and a chunk without it must not look
    # like it covers the whole question.
    idfs = [idf(n_docs, df) for _, df in first]
    total_idf = sum(idfs) or 1.0
    best_possible = sum(w * (K1 + 1) for w in idfs) or 1.0
    if focus is None or focus not in terms:
        focus = terms[max(range(len(terms)), key=lambda i: idfs[i])]
    fi = terms.index(focus)

    hits = []
    for docid, blob in rows:
        _, avg_len, doc_len, per_term = parse_matchinfo(blob, len(terms))
        score = covered = 0.0
        for i, (tf, _) in enumerate(per_term):
            if tf:
                score += idfs[i] * tf * (K1 + 1) / (tf + K1 * (1 - B + B * doc_len / avg_len))
                covered += idfs[i]
        hits.append(dict(docid=docid, score=score, norm=score / best_possible,
                         coverage=covered / total_idf, focus_tf=per_term[fi][0]))
    hits.sort(key=lambda h: -h["score"])
    return hits[:top_k], dict(zip(terms, idfs)), focus


def retrieve(db, terms, top_k, focus=None):
    hits, idfs, focus = search(db, terms, top_k, focus)
    for h in hits:
        h["kb"], h["source"], h["body"] = db.execute(
            "SELECT kb, source, body FROM chunks WHERE id = ?", (h["docid"],)).fetchone()
    return hits, idfs, focus


def confidence(hits):
    if not hits:
        return "WEAK"
    h = hits[0]
    if h["focus_tf"] >= STRONG_FOCUS_TF and h["norm"] >= STRONG_NORM and h["coverage"] >= STRONG_COVERAGE:
        return "STRONG"
    if h["focus_tf"] >= 1 and h["norm"] >= PARTIAL_NORM and h["coverage"] >= PARTIAL_COVERAGE:
        return "PARTIAL"
    return "WEAK"


def known_anywhere(db, terms):
    """True if at least one term occurs in the corpus or in the verified answers."""
    for t in terms:
        for table in ("chunks_fts", "canned_fts"):
            if db.execute(f"SELECT 1 FROM {table} WHERE {table} MATCH ? LIMIT 1", (t,)).fetchone():
                return True
    return False


# ---------------------------------------------------------------- the router
ACTION = {
    "CHAT": "friendly reply, invite a business question; no search, no model",
    "APP_INFO": "the app answers from the phone's own clock/settings; no model",
    "NOT_UNDERSTOOD": "'Sorry, I understand English and Kiswahili -- please ask again'",
    "FOLLOW_UP": "continue the previous answer (re-show its sources / expand it)",
    "VERIFIED": "show the verified answer (no model)",
    "SUGGEST": "ask 'Is your question about <topic>?' -- tap shows the verified answer; "
               "otherwise continue with the passages below",
    "FACTUAL STRONG": "model answers ONLY from these passages, sources shown",
    "FACTUAL PARTIAL": "show passages with caution: 'these may only partly answer your question'",
    "FACTUAL WEAK": "no model: 'I don't have verified information on this' + point to the right office",
    "DIGEST": "model + fact digest, no retrieval",
    "ADVISORY": "model answers, labelled 'general advice, not verified'; attach passages if any",
}


def route(db, query, lang="en", prev_topic=None, prev_query=None, k=3):
    """Decide how the app answers one question. Returns a dict; 'kind' is a key of ACTION."""
    load_config(db)
    r = dict(kind="", topic="", also_matched=[], confidence="", focus="", hits=[], answer="",
             followup=None, suggest="")
    terms = query_terms(query)

    if is_small_talk(query):
        r["kind"] = "CHAT"
        return r
    if prev_query and CLARIFICATION.match(query.lower()):
        # route the previous question and the clarification together, as one question
        combined = f"{prev_query} {CLARIFICATION.sub('', query.lower())}"
        r = route(db, combined, lang, prev_topic=None, prev_query=None, k=k)
        r["clarified"] = combined
        return r
    if APP_INFO.search(query.lower()):
        r["kind"] = "APP_INFO"
        return r
    if terms and not known_anywhere(db, terms):
        r["kind"] = "NOT_UNDERSTOOD"
        return r
    if (prev_topic or prev_query) and is_referential(query):
        r.update(kind="FOLLOW_UP", topic=prev_topic or "")
        return r

    matches = canned_matches(db, query)
    if matches:
        topic = matches[0]
        answer, en, sw = canned_answer(db, topic, lang)
        r.update(kind="VERIFIED", topic=topic, also_matched=matches[1:], answer=answer)
        extra = uncovered_terms(query, topic, f"{en or ''} {sw or ''}", db)
        idfs = term_idfs(db, extra)
        specific = [t for t in extra if idfs[t] >= MIN_SPECIFIC_IDF]
        if specific:
            hits, _, focus = retrieve(db, terms, k, focus=max(specific, key=idfs.get))
            r["followup"] = dict(confidence=confidence(hits), focus=focus, hits=hits, words=specific)
        return r

    # Verified answers are all regulatory, so only factual questions are searched against
    # them -- and a search match is only ever a SUGGESTION the operator confirms, never
    # asserted as the verified answer (it was wrong about half the time on real questions).
    factual = is_factual(query)
    if factual:
        chits, _, _ = search(db, terms, 1, table="canned_fts")
        if chits and chits[0]["focus_tf"] >= 1 and chits[0]["norm"] >= CANNED_SEARCH_NORM \
                and chits[0]["coverage"] >= CANNED_SEARCH_COVERAGE:
            (r["suggest"],) = db.execute("SELECT topic FROM canned WHERE rowid = ?",
                                         (chits[0]["docid"],)).fetchone()

    hits, idfs, focus = retrieve(db, terms, k)
    level = confidence(hits)
    r.update(hits=hits, focus=focus or "", confidence=level)
    if r["suggest"]:
        r["kind"] = "SUGGEST"
    elif factual:
        in_digest = any(kw in query.lower() for (kw,) in
                        db.execute("SELECT keyword FROM digest_override_keywords"))
        r["kind"] = "DIGEST" if in_digest else f"FACTUAL {level}"
    else:
        r["kind"] = "ADVISORY"
    return r


# ---------------------------------------------------------------- CLI
def parity_line(query, r):
    """One comparable line per question. RouterSelfTest.kt logs exactly this format."""
    f = r.get("followup")
    top = r["hits"][0]["docid"] if r["hits"] else (f["hits"][0]["docid"] if f and f["hits"] else "")
    return "|".join(["P", query, r["kind"], r["topic"], r["suggest"], r["confidence"],
                     r["focus"], f["confidence"] if f else "", str(top)])


def show_hits(hits, focus):
    for i, h in enumerate(hits, 1):
        print(f"  #{i} score {h['score']:.1f} norm {h['norm']:.0%} cov {h['coverage']:.0%} "
              f"'{focus}' x{h['focus_tf']} [{h['kb'] or '?'}] {h['source'] or '(no source)'}")
        print("     " + re.sub(r"\s+", " ", h["body"])[:300] + ("..." if len(h["body"]) > 300 else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?")
    ap.add_argument("--db", default="rafiki_pack.db")
    ap.add_argument("--lang", choices=["en", "sw"], default="en")
    ap.add_argument("--prev", help="previous topic, to test follow-ups")
    ap.add_argument("--prev-query", help="previous question, to test follow-ups")
    ap.add_argument("-k", type=int, default=3)
    ap.add_argument("--info", action="store_true")
    ap.add_argument("--parity", metavar="FILE",
                    help="route each line of FILE and print one 'P|...' line per question -- "
                         "the same format the phone's self-test logs, so the two can be diffed")
    args = ap.parse_args()
    db = sqlite3.connect(args.db)

    if args.parity:
        with open(args.parity, encoding="utf-8") as f:
            for q in (line.strip() for line in f):
                if q and not q.startswith("#"):
                    print(parity_line(q, route(db, q, args.lang)))
        return

    if args.info or not args.query:
        for k, v in db.execute("SELECT key, value FROM meta ORDER BY key"):
            print(f"{k}: {v}")
        return

    t0 = time.perf_counter()
    r = route(db, args.query, args.lang, args.prev, args.prev_query, args.k)
    ms = (time.perf_counter() - t0) * 1000
    as_of = db.execute("SELECT value FROM meta WHERE key = 'as_of'").fetchone()[0]

    print("=" * 70)
    print(f"Q: {args.query}")
    print(f"ROUTE: {r['kind']}" + (f"  topic: {r['topic']}" if r["topic"] else "")
          + (f"  suggest: {r['suggest']} (passages: {r['confidence']})" if r["suggest"] else "")
          + f"  [{ms:.1f} ms]")
    print(f"  action: {ACTION[r['kind']]}")
    if r["also_matched"]:
        print(f"  also matched: {r['also_matched']}")
    if r["answer"]:
        print(f"-- verified answer (accurate as of {as_of}) " + "-" * 25)
        print(r["answer"])
    f = r["followup"]
    if f:
        print(f"-- follow-up: question is specifically about {f['words']} -> {f['confidence']}")
        show_hits(f["hits"], f["focus"])
    if r["hits"]:
        print(f"-- passages (focus word '{r['focus']}') " + "-" * 25)
        show_hits(r["hits"], r["focus"])


if __name__ == "__main__":
    main()
