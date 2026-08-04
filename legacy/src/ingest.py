"""
ingest.py — Kenya MSME Advisor Knowledge Base Builder
Reads documents/ folder and builds 7 focused sub-knowledge bases.
Run: python3 src/ingest.py
"""

import os, json, pickle, re, sys
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer

try:
    import pdfplumber
    PDF_OK = True
except ImportError:
    PDF_OK = False
    print("⚠ pdfplumber not found — PDFs will be skipped")
    print("  Install: pip install pdfplumber")

BASE_DIR = Path(__file__).parent.parent
DOCS_DIR = BASE_DIR / "documents"
KB_DIR   = BASE_DIR / "knowledge_base"
KB_DIR.mkdir(exist_ok=True)

# ── Category definitions ───────────────────────────────────────────────────────
CATEGORIES = {
    "kb1_legal_regulatory": {
        "name": "Legal & Regulatory",
        "description": "Business registration, permits, licenses, county regulations",
        "keywords": ["register","permit","license","certificate","BRS","county","eCitizen"],
        "patterns": ["brs_","business_registration","ca_licens","ca_annual","ca_market",
                     "ca_telecom","nairobi_","mombasa_county","kisumu_business",
                     "kebs_","ppb_","ktb_","doing_business_kenya",
                     "kenya_single_business","msea_msme_policy","kenya_sacco_societies"],
    },
    "kb2_tax_kra": {
        "name": "Tax & KRA",
        "description": "KRA tax guides, eTIMS, VAT, PAYE, Turnover Tax",
        "keywords": ["tax","KRA","VAT","PAYE","eTIMS","turnover","income tax","pin"],
        "patterns": ["kra_","etims","income_tax_act","vat_act","tax_procedures"],
    },
    "kb3_financing_credit": {
        "name": "Financing & Credit",
        "description": "Hustler Fund, YEDF, WEF, CBK, MFIs, SACCOs, loans",
        "keywords": ["loan","fund","financing","credit","sacco","bank","hustler","YEDF","WEF"],
        "patterns": ["hustler","yedf_","wef_","cbk_","kwft_","faulu_","smep_",
                     "microfinance","fsd_kenya","finaccess","ifc_msme","credit_guarantee"],
    },
    "kb4_social_security": {
        "name": "Social Security",
        "description": "NSSF, SHA, NITA, IRA, insurance contributions",
        "keywords": ["NSSF","SHA","insurance","NHIF","NITA","levy","pension","SHIF"],
        "patterns": ["nssf_","sha_","shif_","nita_","ira_","aki_",
                     "social_health_insurance","insurance_industry","claims_report"],
    },
    "kb5_digital_trade": {
        "name": "Digital & Trade",
        "description": "M-Pesa, AfCFTA, EAC, ICT, e-commerce, electricity",
        "keywords": ["mpesa","paybill","mobile money","export","trade","digital","AfCFTA","EAC"],
        "patterns": ["safaricom_","pochi","fuliza","gsma_","keproba_","afcfta",
                     "eac_","comesa_","icta_","ecommerce","kenya_trade","ajira_",
                     "kplc_","epra_","krb_","digital_payments","kenya_national_digital",
                     "kenya_data_protection","kenya_ecommerce"],
    },
    "kb6_county_geospatial": {
        "name": "County & Geospatial",
        "description": "47 counties, KNBS statistics, research reports",
        "keywords": ["county","nairobi","mombasa","kisumu","nakuru","statistics","KNBS"],
        "patterns": ["knbs_","cra_kenya","county_abstract","county_economic",
                     "county_product","worldbank_kenya","un_kenya","unctad_","kippra_",
                     "kepsa_","strathmore_","kenya_economic_report","county_government",
                     "gross_county","census_2019","ifc_msme_day","ifc_msme_platform"],
    },
    "kb7_culture_context": {
        "name": "Culture & Context",
        "description": "Jua Kali, chama, cultural context, TVET, skills, climate",
        "keywords": ["jua kali","chama","informal","culture","TVET","skills","climate","youth"],
        "patterns": ["jua_kali","chama_","cultural","culture","tvet","tveta_",
                     "labour_market","skills_","acf_kenya","climate","ndma_","lse_climate",
                     "unfccc","youth_entrepreneurship","entrepreneurial_culture",
                     "community_financing","informal_economy","socio_cultural",
                     "kenya_sme_management","kenya_sme_business","kenya_sme_financial",
                     "kenya_business_plan","kenya_sbdc","fke_skills","kenya_labour",
                     "local_languages","cultural_norms","cultural_geo","cultural_business",
                     "kenya_cultural","insurance_climate","kenya_nap","kenya_unfccc"],
    },
    "kb9_bank_lending": {
        "name": "Bank Lending & Credit",
        "description": "Commercial bank SME lending criteria, loan products, credit assessment",
        "keywords": ["bank loan","lending criteria","credit assessment","collateral","KCB","Equity Bank"],
        "patterns": ["kenya_commercial_bank","bank_lending","lending_criteria",
                     "kcb_sme","equity_bank_sme","coop_bank","ncba_sme",
                     "loan_criteria","credit_assessment","bank_sme"],
    },
    "kb8_national_policy_strategy": {
        "name": "National Policy & Strategy",
        "description": "Vision 2030, national strategies, World Bank, WEF, KIPPRA policy",
        "keywords": ["vision 2030","policy","strategy","national plan","World Bank","WEF"],
        "patterns": ["kenya_vision2030","kenya_national_digital_masterplan",
                     "kenya_nap_climate","kenya_unfccc","kenya_national_climate",
                     "ndma_strategic_plan","national_treasury_budget",
                     "kippra_policy","kippra_economic_report","kippra_kenya_economic",
                     "kippra_county_business_environment","kippra_ict_msme",
                     "worldbank_kenya_economic_update","worldbank_kenya_skills_demand",
                     "worldbank_kenya_overview","worldbank_kenya_msme_safer_report",
                     "worldbank_kenya_urban_sector","icta_strategic","afdb_kenya",
                     "gsma_mobile_economy","gsma_state_mobile","ifc_msme_finance_factsheet",
                     "acf_kenya_climate","un_kenya_annual","un_kenya_msme_sdgs",
                     "un_kenya_sdgs","unctad_kenya_msme_report",
                     "wef_services_report","wef_strategic_plan",
                     "fsd_kenya_msme_outlook","ifc_g20_msme"],
    },
}

def categorise(filename: str) -> str:
    fn = filename.lower()
    for kb_id, kb_def in CATEGORIES.items():
        for pattern in kb_def["patterns"]:
            if pattern.lower() in fn:
                return kb_id
    return "kb1_legal_regulatory"

def extract_pdf(path: Path) -> str:
    if not PDF_OK:
        return ""
    try:
        text = ""
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages[:60]:
                t = page.extract_text()
                if t:
                    text += t + "\n"
        return text
    except Exception as e:
        print(f"  ⚠ PDF error {path.name}: {e}")
        return ""

def extract_txt(path: Path) -> str:
    for enc in ["utf-8", "latin-1", "cp1252"]:
        try:
            return path.read_text(encoding=enc)
        except Exception:
            continue
    return ""

def extract_text(path: Path) -> str:
    return extract_pdf(path) if path.suffix.lower() == ".pdf" else extract_txt(path)

def chunk_text(text: str, size=500, overlap=100) -> list:
    text   = re.sub(r'\s+', ' ', text).strip()
    chunks = []
    start  = 0
    while start < len(text):
        end   = min(start + size, len(text))
        chunk = text[start:end].strip()
        if len(chunk) > 80:
            chunks.append(chunk)
        start += size - overlap
    return chunks

def build_kb(kb_id: str, kb_def: dict, all_files: list) -> int:
    # Filter files for this KB
    kb_files = [f for f in all_files if categorise(f.name) == kb_id]

    if not kb_files:
        print(f"  ⚠ No files matched for {kb_id}")
        return 0

    chunks   = []
    metadata = []

    for f in sorted(kb_files):
        text = extract_text(f)
        if not text.strip():
            continue
        doc_chunks = chunk_text(text)
        for ch in doc_chunks:
            chunks.append(ch)
            metadata.append({
                "filename": f.name,
                "kb":       kb_id,
                "kb_name":  kb_def["name"],
            })

    if not chunks:
        return 0

    vectorizer = TfidfVectorizer(
        max_features=15000, ngram_range=(1,2),
        min_df=1, stop_words="english",
    )
    matrix = vectorizer.fit_transform(chunks)

    kb_path = KB_DIR / kb_id
    kb_path.mkdir(exist_ok=True)

    with open(kb_path / "chunks.json", "w", encoding="utf-8") as f:
        json.dump({
            "kb_id":       kb_id,
            "kb_name":     kb_def["name"],
            "description": kb_def["description"],
            "keywords":    kb_def["keywords"],
            "chunks":      chunks,
            "metadata":    metadata,
        }, f, ensure_ascii=False, indent=2)

    with open(kb_path / "vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)
    with open(kb_path / "matrix.pkl", "wb") as f:
        pickle.dump(matrix, f)

    return len(chunks)

if __name__ == "__main__":
    print("═"*60)
    print("KENYA MSME ADVISOR — KNOWLEDGE BASE BUILDER")
    print("═"*60)

    # Load all files from documents/
    all_files = (list(DOCS_DIR.rglob("*.pdf")) +
                 list(DOCS_DIR.rglob("*.txt")) +
                 list(DOCS_DIR.rglob("*.docx")))

    if not all_files:
        print(f"⚠ No documents found in {DOCS_DIR}")
        sys.exit(1)

    print(f"\n[1/3] Found {len(all_files)} documents in {DOCS_DIR}")

    # Show categorisation preview
    print("\n[2/3] Categorising documents...")
    preview = {}
    for f in all_files:
        kb_id = categorise(f.name)
        preview[kb_id] = preview.get(kb_id, 0) + 1
    for kb_id, count in preview.items():
        print(f"  {CATEGORIES[kb_id]['name']:<30} {count:>3} documents")

    # Build each KB
    print("\n[3/3] Building TF-IDF indexes...")
    manifest = {"total_chunks": 0, "total_kbs": 0, "knowledge_bases": {}}
    results  = {}

    for kb_id, kb_def in CATEGORIES.items():
        print(f"\n  ▶ {kb_def['name']}...", end=" ", flush=True)
        count = build_kb(kb_id, kb_def, all_files)
        results[kb_id] = count

        if count > 0:
            manifest["total_chunks"] += count
            manifest["total_kbs"]    += 1
            srcs = preview.get(kb_id, 0)
            manifest["knowledge_bases"][kb_id] = {
                "name":        kb_def["name"],
                "description": kb_def["description"],
                "keywords":    kb_def["keywords"],
                "chunks":      count,
                "sources":     srcs,
            }
            print(f"{count} chunks ✅")
        else:
            print("⚠ No chunks")

    # Save manifest
    with open(KB_DIR / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    # Final report
    print("\n" + "═"*60)
    print("BUILD COMPLETE")
    print("═"*60)
    for kb_id, count in results.items():
        name   = CATEGORIES[kb_id]["name"]
        status = "✅" if count > 0 else "❌"
        print(f"  {status} {name:<30} {count:>6} chunks")
    print(f"{'─'*60}")
    print(f"  {'TOTAL':<30} {sum(results.values()):>6} chunks")
    print("═"*60)
    print(f"\nKnowledge base saved to: {KB_DIR}")
    print("Launch the app: streamlit run src/app.py")