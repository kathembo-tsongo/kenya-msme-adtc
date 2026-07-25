"""
scrape_kb7_growth.py — Theme 1: Business Growth & Scalability
Adds to KB7 Culture & Context:
- Kenya SME growth strategies
- Business scaling frameworks
- Market expansion (EAC, AfCFTA)
- Strathmore SBDC resources
"""

import requests, time
from bs4 import BeautifulSoup
from pathlib import Path

DOCS_DIR = Path("documents/kb7_culture_context")
DOCS_DIR.mkdir(parents=True, exist_ok=True)
HEADERS  = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0.0.0"}

PAGES = [
    # Kenya SME Growth Strategies
    {"url": "https://www.kenyasbdc.or.ke/",
     "filename": "kenya_sbdc_homepage.txt"},
    {"url": "https://www.kenyasbdc.or.ke/services/",
     "filename": "kenya_sbdc_services.txt"},
    {"url": "https://www.kenyasbdc.or.ke/training/",
     "filename": "kenya_sbdc_training.txt"},

    # KIPPRA SME Growth
    {"url": "https://kippra.or.ke/sme-growth-kenya/",
     "filename": "kippra_sme_growth_kenya.txt"},
    {"url": "https://kippra.or.ke/msme-development/",
     "filename": "kippra_msme_development.txt"},

    # Kenya Private Sector Alliance
    {"url": "https://www.kepsa.or.ke/sme-support/",
     "filename": "kepsa_sme_support.txt"},
    {"url": "https://www.kepsa.or.ke/business-development/",
     "filename": "kepsa_business_development.txt"},

    # EAC Trade & Market Expansion
    {"url": "https://www.eac.int/trade",
     "filename": "eac_trade_market_expansion.txt"},
    {"url": "https://www.eac.int/sme",
     "filename": "eac_sme_opportunities.txt"},
    {"url": "https://www.eac.int/customs",
     "filename": "eac_customs_union_sme.txt"},

    # AfCFTA Kenya
    {"url": "https://au-afcfta.org/about/",
     "filename": "afcfta_about_kenya_sme.txt"},
    {"url": "https://kippra.or.ke/afcfta-kenya-opportunities/",
     "filename": "kippra_afcfta_sme_opportunities.txt"},

    # Kenya Export Promotion
    {"url": "https://www.keproba.go.ke/export-growth/",
     "filename": "keproba_export_growth_sme.txt"},
    {"url": "https://www.keproba.go.ke/market-access/",
     "filename": "keproba_market_access.txt"},
    {"url": "https://www.keproba.go.ke/trade-fairs/",
     "filename": "keproba_trade_fairs.txt"},

    # Kenya Investment Authority
    {"url": "https://invest.go.ke/sme-growth/",
     "filename": "keninvest_sme_growth.txt"},
    {"url": "https://invest.go.ke/sector-profiles/",
     "filename": "keninvest_sector_profiles.txt"},

    # IFC Kenya SME
    {"url": "https://www.ifc.org/en/where-we-work/africa/kenya",
     "filename": "ifc_kenya_sme_growth.txt"},

    # World Bank Kenya SME
    {"url": "https://www.worldbank.org/en/country/kenya/brief/private-sector",
     "filename": "worldbank_kenya_private_sector_growth.txt"},

    # FKE Skills & Growth
    {"url": "https://www.fke-kenya.org/sme-support/",
     "filename": "fke_sme_support_growth.txt"},

    # Kenya National Chamber of Commerce
    {"url": "https://www.kncci.or.ke/sme-development/",
     "filename": "kncci_sme_development.txt"},
    {"url": "https://www.kncci.or.ke/business-growth/",
     "filename": "kncci_business_growth.txt"},
    {"url": "https://www.kncci.or.ke/trade-opportunities/",
     "filename": "kncci_trade_opportunities.txt"},

    # Strathmore Business School SBDC
    {"url": "https://businessschool.strathmore.edu/sbdc/",
     "filename": "strathmore_sbdc_overview.txt"},
    {"url": "https://businessschool.strathmore.edu/sbdc/services/",
     "filename": "strathmore_sbdc_services.txt"},
    {"url": "https://businessschool.strathmore.edu/entrepreneurship/",
     "filename": "strathmore_entrepreneurship.txt"},

    # MSME State Department Growth
    {"url": "https://msme.go.ke/growth-programs/",
     "filename": "msme_growth_programs.txt"},
    {"url": "https://msme.go.ke/market-access/",
     "filename": "msme_market_access.txt"},

    # Kenya ICT Board Digital Growth
    {"url": "https://ict.go.ke/sme-digital-growth/",
     "filename": "ict_sme_digital_growth.txt"},

    # Safaricom Business Growth Tools
    {"url": "https://www.safaricom.co.ke/business/",
     "filename": "safaricom_business_growth_tools.txt"},

    # iBizAfrica Strathmore
    {"url": "https://ibizafrica.strathmore.edu/",
     "filename": "ibizafrica_sme_incubation.txt"},
    {"url": "https://ibizafrica.strathmore.edu/programs/",
     "filename": "ibizafrica_programs.txt"},

    # Kenya SME Scaling Framework
    {"url": "https://www.gsb.strathmore.edu/sme-scaling/",
     "filename": "strathmore_gsb_sme_scaling.txt"},

    # AfDB Kenya Private Sector
    {"url": "https://www.afdb.org/en/countries/east-africa/kenya/kenya-private-sector",
     "filename": "afdb_kenya_private_sector_growth.txt"},
]

def scrape(url, filename):
    path = DOCS_DIR / filename
    if path.exists():
        print(f"  [SKIP] {filename}")
        return
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script","style","nav","footer","header","aside"]):
            tag.decompose()
        text = "\n".join(
            line for line in soup.get_text("\n", strip=True).splitlines()
            if line.strip()
        )
        if len(text) < 200:
            print(f"  [THIN] {filename} ({len(text)} chars)")
            return
        content = f"SOURCE: {url}\nKB: kb7_culture_context\nTHEME: Business Growth & Scalability\n\n{text}"
        path.write_text(content, encoding="utf-8")
        print(f"  [OK] {filename} ({len(text):,} chars)")
    except Exception as e:
        print(f"  [ERR] {filename} — {e}")

if __name__ == "__main__":
    print("\nTheme 1 — Business Growth & Scalability → KB7")
    print("=" * 55)
    for page in PAGES:
        scrape(page["url"], page["filename"])
        time.sleep(1)

    txt = len(list(DOCS_DIR.glob("*.txt")))
    pdf = len(list(DOCS_DIR.glob("*.pdf")))
    print(f"\nKB7 total: {txt} txt + {pdf} pdf = {txt+pdf} docs")
