"""
router.py — Smart Topic Router for Multi-KB System
Routes questions to the most relevant knowledge base.
"""
import json, pickle
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity

KB_DIR = Path("/home/dieudonne/Programming Projects/kenya_msme_advisor/knowledge_base")

ROUTING_RULES = {
    "kb2_tax_kra": [
        "tax","kra","vat","paye","etims","turnover tax","income tax","pin",
        "itax","tax return","filing","withholding","tot","ushuru","kodi",
        "tax rate","tax compliance","tax obligation","presumptive",
    ],
    "kb3_financing_credit": [
        "loan","fund","financing","credit","sacco","borrow","lend","hustler",
        "yedf","wef","microfinance","interest","collateral","bank","invest",
        "capital","mkopo","faulu","kwft","smep","equity","kcb","coop",
        "credit guarantee","working capital","overdraft","fuliza",
    ],
    "kb4_social_security": [
        "nssf","sha","nhif","nita","insurance","pension","health cover",
        "contribution","employee","shif","social security","levy",
        "workmen","medical","accident","health insurance",
    ],
    "kb5_digital_trade": [
        "mpesa","m-pesa","paybill","till number","mobile money","pochi",
        "export","trade","afcfta","eac","comesa","ecommerce","online",
        "digital","electricity","kplc","internet","website","ajira",
        "airtel money","buy goods","lipa na mpesa","fuliza",
    ],
    "kb6_county_geospatial": [
        "county","nairobi","mombasa","kisumu","nakuru","eldoret","meru",
        "kakamega","kericho","region","statistics","knbs","population",
        "survey","world bank","gdp","economic","research","data","report",
    ],
    "kb7_culture_context": [
        "jua kali","chama","informal","culture","tvet","skills","training",
        "climate","youth","women","community","artisan","hawker","market",
        "cultural","indigenous","dholuo","kikuyu","kamba","kalenjin",
        "gender","disability","cooperative",
    ],
    "kb1_legal_regulatory": [
        "register","permit","license","certificate","brs","ecitizen",
        "county permit","business name","regulation","act","law",
        "compliance","legal","fine","penalty","ubp","unified business permit",
        "business registration","sole proprietorship","partnership","company",
    ],
}

_loaded = {}

def _load_kb(kb_id):
    if kb_id in _loaded:
        return _loaded[kb_id]
    p = KB_DIR / kb_id
    if not p.exists():
        return None, None, [], []
    try:
        with open(p/"vectorizer.pkl","rb") as f: vec = pickle.load(f)
        with open(p/"matrix.pkl","rb") as f:     mat = pickle.load(f)
        with open(p/"chunks.json",encoding="utf-8") as f: d = json.load(f)
        result = (vec, mat, d["chunks"], d["metadata"])
        _loaded[kb_id] = result
        return result
    except Exception as e:
        print(f"KB load error {kb_id}: {e}")
        return None, None, [], []

def route_question(question):
    q = question.lower()
    scores = {kb_id: 0 for kb_id in ROUTING_RULES}
    for kb_id, keywords in ROUTING_RULES.items():
        for kw in keywords:
            if kw in q:
                scores[kb_id] += len(kw.split())
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary   = ranked[0][0] if ranked[0][1] > 0 else "kb1_legal_regulatory"
    secondary = ranked[1][0] if len(ranked)>1 and ranked[1][1]>0 and ranked[1][0]!=primary else None
    return primary, secondary

def _retrieve_from(query, kb_id, k=4):
    vec, mat, chunks, meta = _load_kb(kb_id)
    if vec is None:
        return "", []
    qvec = vec.transform([query])
    sims = cosine_similarity(qvec, mat).flatten()
    top  = sims.argsort()[-k:][::-1]
    ctx, sources = [], []
    for i in top:
        if sims[i] > 0.01:
            ctx.append(chunks[i])
            src = meta[i].get("filename","")
            if src not in sources:
                sources.append(src)
    return "\n\n---\n\n".join(ctx), sources

def smart_retrieve(query, k=4):
    """Route to best KB and retrieve. Returns (context, sources, kb_name)."""
    primary, secondary = route_question(query)

    # Load manifest for KB name
    manifest_path = KB_DIR / "manifest.json"
    kb_name = primary
    if manifest_path.exists():
        m = json.loads(manifest_path.read_text())
        kb_name = m.get("knowledge_bases",{}).get(primary,{}).get("name", primary)

    context, sources = _retrieve_from(query, primary, k)

    # If weak results and secondary available, add top 2 from secondary
    if len(context) < 200 and secondary:
        ctx2, src2 = _retrieve_from(query, secondary, k=2)
        if ctx2:
            context = (context + "\n\n---\n\n" + ctx2).strip() if context else ctx2
            sources += [s for s in src2 if s not in sources]

    return context, sources, kb_name
