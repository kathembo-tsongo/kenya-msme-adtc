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
import os
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
MIN_LEFTOVER_DF = 3      # in a glossary-translated question, a leftover word found in fewer chunks
                         # than this is untranslated Kiswahili, not content: it is not searched

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
""".split()) | set("""
company companies director directors shareholder shareholders partnership partnerships llp
incorporation incorporate proprietorship limited certificate trademark patent copyright returns filing nil reserve
reservation registrar
standards inspection fire safety food handler handlers data protection odpc supplier suppliers
procurement importing exporting
withholding rental corporate capital gains exempt exemption excise stamp deadline
overtime notice injury wiba sick pension retirement redundancy severance gratuity casual
disability disabilities ncpwd inua jamii cash transfer elderly hospital hospitals first aid
collateral guarantee credit crb grant grants chama foreigner foreigners foreign
""".split())  # the six study domains' core legal vocabulary (proposal, domain scope)


# Bilingual glossary (glossary_sw_en.tsv): Kiswahili term -> English search words. The documents
# are in English, so a Kiswahili question is searched with the English words added and the
# matched Kiswahili words removed. Longest entry first, so "kodi ya mapato" wins over "kodi".
def load_glossary(path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "glossary_sw_en.tsv")):
    entries = {}
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip() or line.startswith("#") or line.startswith("kiswahili\t"):
                continue
            cols = line.rstrip("\n").split("\t")
            root = cols[0].strip().startswith("*")
            sw = ("*" if root else "") + " ".join(re.findall(r"[a-z0-9]+", cols[0].lower()))
            en = cols[1].strip() if len(cols) > 1 else ""
            en = "-" if en == "-" else " ".join(re.findall(r"[a-z0-9]+", en.lower()))
            if sw.strip("*") and en:
                entries[sw] = en  # a later duplicate wins
    # phrases first (most words, then longest), then roots (longest first)
    return sorted(entries.items(),
                  key=lambda e: (e[0].startswith("*"), -len(e[0].split()), -len(e[0]), e[0]))


GLOSSARY = load_glossary()


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
        # "kiswahili<TAB>english", already in matching order (longest first)
        "glossary": [f"{sw}\t{en}" for sw, en in GLOSSARY],
        "thresholds": dict(
            k1=K1, b=B, strong_norm=STRONG_NORM, strong_coverage=STRONG_COVERAGE,
            strong_focus_tf=STRONG_FOCUS_TF, partial_norm=PARTIAL_NORM,
            partial_coverage=PARTIAL_COVERAGE, canned_search_norm=CANNED_SEARCH_NORM,
            canned_search_coverage=CANNED_SEARCH_COVERAGE, min_specific_idf=MIN_SPECIFIC_IDF,
            min_leftover_df=MIN_LEFTOVER_DF),
    }


_loaded_from = None


def load_config(db):
    """Override the module defaults with the pack's config table (once per pack)."""
    global _loaded_from, STOPWORDS, SMALL_TALK, FACTUAL_WORDS, REFERENTIAL, APP_INFO, CLARIFICATION, GLOSSARY
    global K1, B, STRONG_NORM, STRONG_COVERAGE, STRONG_FOCUS_TF, PARTIAL_NORM, PARTIAL_COVERAGE
    global CANNED_SEARCH_NORM, CANNED_SEARCH_COVERAGE, MIN_SPECIFIC_IDF, MIN_LEFTOVER_DF
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
    # packs built before the glossary have none: cross-lingual expansion is then off
    GLOSSARY = [tuple(e.split("\t", 1)) for e in cfg.get("glossary", [])]
    t = cfg["thresholds"]
    K1, B = t["k1"], t["b"]
    STRONG_NORM, STRONG_COVERAGE, STRONG_FOCUS_TF = t["strong_norm"], t["strong_coverage"], t["strong_focus_tf"]
    PARTIAL_NORM, PARTIAL_COVERAGE = t["partial_norm"], t["partial_coverage"]
    CANNED_SEARCH_NORM, CANNED_SEARCH_COVERAGE = t["canned_search_norm"], t["canned_search_coverage"]
    MIN_SPECIFIC_IDF = t["min_specific_idf"]
    MIN_LEFTOVER_DF = t.get("min_leftover_df", MIN_LEFTOVER_DF)


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


def glossary_expand(query):
    """(English words to add, Kiswahili words they replace) for the glossary entries in the query.
    Whole-word matches only, longest entry first; a matched phrase is consumed so a shorter
    entry inside it ("kodi" in "kodi ya mapato") cannot match again."""
    q = " " + " ".join(words(query)) + " "
    added, used = [], set()
    for sw, en in GLOSSARY:
        if sw.startswith("*"):
            continue
        if f" {sw} " in q:
            if en != "-":
                added.extend(en.split())
            used.update(sw.split())
            q = q.replace(f" {sw} ", " | ")
    roots = [(sw[1:], en) for sw, en in GLOSSARY if sw.startswith("*")]
    for w in q.split():
        if w == "|" or w in used:
            continue
        for root, en in roots:
            if root in w:
                if en != "-":
                    added.extend(en.split())
                used.add(w)
                break
    return added, used


def search_terms(query, limit=12):
    """Query terms for retrieval: glossary English words first, then the question's own words
    minus the Kiswahili words the glossary replaced. An English question with no glossary
    match gets exactly query_terms(query)."""
    added, used = glossary_expand(query)
    rest = [w for w in words(query) if w not in used]
    return query_terms(" ".join(added + rest), limit), added


def is_small_talk(query):
    w = words(query)
    return bool(w) and all(t in SMALL_TALK for t in w)


def is_referential(query):
    q = query.lower()
    return any(p in q for p in REFERENTIAL)


def is_factual(query, extra=()):
    return any(t in FACTUAL_WORDS or t.rstrip("s") in FACTUAL_WORDS for t in list(words(query)) + list(extra))


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


NEGATIONS = {"no", "not", "without", "bila"}


def light_stem(t):
    """Plural and -ing endings only: licenses/licences -> license/licence, filing -> fil.
    Negations (no / not / without / bila) all become "no"."""
    if t in NEGATIONS:
        return "no"
    if len(t) <= 4:
        return t
    if t.endswith("ies"):
        return t[:-3] + "y"
    if t.endswith("es") and t[:-2].endswith(("ss", "x", "ch", "sh")):
        return t[:-2]
    if t.endswith("s") and not t.endswith("ss"):
        return t[:-1]
    if t.endswith("ing") and len(t) >= 6:
        return t[:-3]
    return t


def canned_matches_glossary(db, tokens, added=()):
    """Second chance for a Kiswahili question that matched no keyword phrase: a topic matches
    when ALL content words of one of its multi-word keywords appear among the question's
    glossary English words and remaining words, in any order, plurals and -ing ignored.
    A one-word keyword ("termination") counts only if the glossary supplied that word. The keyword
    must contain at least one factual (regulatory) word -- verified answers are all regulatory,
    so "sell my products" alone never reaches one -- and negations ("no business permit") are
    kept as words the question must contain.
    Same ranking as canned_matches(). Only used when the glossary added words."""
    have = {light_stem(t) for t in tokens}
    from_glossary = {light_stem(t) for t in added}
    factual = {light_stem(t) for t in FACTUAL_WORDS}
    rows = db.execute(
        "SELECT topic, priority, keyword FROM topic_keywords ORDER BY priority, rowid").fetchall()
    general = {t for (t,) in db.execute("SELECT topic FROM general_topics")}
    best = {}
    for topic, priority, kw in rows:
        need = [light_stem(t) for t in words(kw) if t not in STOPWORDS or t in NEGATIONS]
        if not any(t in factual for t in need):
            continue
        ok = all(t in have for t in need) if len(need) >= 2 else \
            (len(need) == 1 and need[0] in from_glossary)
        if ok:
            if topic not in best or len(kw) > best[topic][0]:
                best[topic] = (len(kw), priority)
    return sorted(best, key=lambda t: (t in general, -best[t][0], best[t][1]))


def general_topic_set(db):
    return {t for (t,) in db.execute("SELECT topic FROM general_topics")}


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


def term_df(db, t, table="chunks_fts"):
    """Number of chunks containing the term (0 if none)."""
    row = db.execute(f"SELECT matchinfo({table}, 'pcnalx') FROM {table} "
                     f"WHERE {table} MATCH ? LIMIT 1", (t,)).fetchone()
    return parse_matchinfo(row[0], 1)[3][0][1] if row else 0


def drop_untranslated(db, terms, expanded):
    """For a glossary-translated question: keep the glossary's English words, and of the leftover
    words only those found in at least MIN_LEFTOVER_DF chunks. Unknown leftovers would otherwise
    get the highest weight and make every passage look like a partial match."""
    if not expanded:
        return terms
    english = set(query_terms(" ".join(expanded), 99))
    kept = [t for t in terms if t in english or term_df(db, t) >= MIN_LEFTOVER_DF]
    return kept or terms


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
        h["domain"] = chunk_domain_of(db, h["docid"])
    return hits, idfs, focus


def chunk_domain_of(db, docid):
    """A chunk's domain, or "" for packs built before domains."""
    try:
        return db.execute("SELECT domain FROM chunks WHERE id = ?", (docid,)).fetchone()[0] or ""
    except sqlite3.OperationalError:
        return ""


def topic_domain(db, topic):
    """A verified answer's domain, or "" for packs built before domains."""
    try:
        row = db.execute("SELECT domain FROM topic_domain WHERE topic = ?", (topic,)).fetchone()
        return row[0] if row else ""
    except sqlite3.OperationalError:
        return ""


def answer_domain(db, r):
    """The domain an answer belongs to, for the evaluation log: the verified topic's domain,
    else the top passage's domain (also for a SUGGEST, whose topic is still unconfirmed),
    else "general"."""
    t = r.get("topic")
    if t:
        return topic_domain(db, t) or "general"
    if r.get("hits"):
        return r["hits"][0].get("domain") or "general"
    return "general"


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


# Short follow-ups that lean on the previous question ("and for the father?", "what about Nairobi?", "na ...").
ELLIPTIC = re.compile(r"^(and|but|so|what about|what if|how about|how much|how long|how many|when|where|"
                      r"na|je|vipi|basi|halafu)\b|\b(it|this|that|them|those|hiyo|hii|hizo|hilo|hayo)\b")


def contextual_topic(db, query, prev_topic):
    """Topic for a short follow-up with no keyword of its own, given the previous topic -- or None (new question)."""
    q = query.lower()
    if len(words(q)) > 8:
        return None
    try:
        rows = db.execute("SELECT target, cue FROM followups WHERE topic = ? ORDER BY ord", (prev_topic,)).fetchall()
    except Exception:
        rows = []
    for target, cue in rows:
        if cue in q:
            return target
    return prev_topic if ELLIPTIC.search(q) else None


NO_DOMAIN_KINDS = {"CHAT", "APP_INFO", "NOT_UNDERSTOOD"}


def route(db, query, lang="en", prev_topic=None, prev_query=None, k=3):
    """Decide how the app answers one question. Returns a dict; 'kind' is a key of ACTION,
    'domain' is one of the six study domains, "general", or "" (chat, clock, not understood)."""
    r = _route(db, query, lang, prev_topic, prev_query, k)
    r["domain"] = "" if r["kind"] in NO_DOMAIN_KINDS else answer_domain(db, r)
    return r


def _route(db, query, lang="en", prev_topic=None, prev_query=None, k=3):
    load_config(db)
    r = dict(kind="", topic="", also_matched=[], confidence="", focus="", hits=[], answer="",
             followup=None, suggest="", expanded=[], domain="")
    terms, r["expanded"] = search_terms(query)
    terms = drop_untranslated(db, terms, r["expanded"])

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
    general_only = bool(matches) and all(t in general_topic_set(db) for t in matches)
    if r["expanded"] and (not matches or general_only):
        # no keyword phrase matched, or only an umbrella topic ("nssf"): give the glossary a
        # chance to find a more specific verified answer ("adhabu ... nssf" -> nssf_penalty)
        added, used = glossary_expand(query)
        gm = canned_matches_glossary(db, added + [w for w in words(query) if w not in used], added)
        if gm and (not matches or gm[0] not in general_topic_set(db)):
            matches = gm + [t for t in matches if t not in gm]
            r["via_glossary"] = True
    contextual = None
    if not matches and prev_topic:
        contextual = contextual_topic(db, query, prev_topic)
        if contextual:
            matches = [contextual]
            r["contextual"] = prev_topic
    if matches:
        topic = matches[0]
        answer, en, sw = canned_answer(db, topic, lang)
        r.update(kind="VERIFIED", topic=topic, also_matched=matches[1:], answer=answer)
        extra = [] if contextual else uncovered_terms(query, topic, f"{en or ''} {sw or ''}", db)
        idfs = term_idfs(db, extra)
        specific = [t for t in extra if idfs[t] >= MIN_SPECIFIC_IDF]
        if specific:
            hits, _, focus = retrieve(db, terms, k, focus=max(specific, key=idfs.get))
            r["followup"] = dict(confidence=confidence(hits), focus=focus, hits=hits, words=specific)
        return r

    # Verified answers are all regulatory, so only factual questions are searched against
    # them -- and a search match is only ever a SUGGESTION the operator confirms, never
    # asserted as the verified answer (it was wrong about half the time on real questions).
    factual = is_factual(query, r["expanded"])
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
              f"'{focus}' x{h['focus_tf']} [{h['kb'] or '?'}|{h.get('domain') or '?'}] {h['source'] or '(no source)'}")
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
    print(f"  action: {ACTION[r['kind']]}" + (f"  [domain: {r['domain']}]" if r["domain"] else ""))
    if r.get("expanded"):
        print(f"  glossary added: {' '.join(r['expanded'])}")
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
