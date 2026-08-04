import requests, time
from bs4 import BeautifulSoup
from pathlib import Path

DOCS_DIR = Path("documents/kb8_national_policy_strategy")
DOCS_DIR.mkdir(parents=True, exist_ok=True)
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0.0.0"}

WEB_PAGES = [
    # Kenya Vision 2030
    {"url": "https://vision2030.go.ke/about/", "filename": "kenya_vision2030_about.txt"},
    {"url": "https://vision2030.go.ke/pillars/", "filename": "kenya_vision2030_pillars.txt"},
    {"url": "https://vision2030.go.ke/enablers/", "filename": "kenya_vision2030_enablers.txt"},
    {"url": "https://vision2030.go.ke/big-four-agenda/", "filename": "kenya_vision2030_big4.txt"},
    # National Treasury - Budget
    {"url": "https://www.treasury.go.ke/budget-statements/", "filename": "national_treasury_budget_statements.txt"},
    {"url": "https://www.treasury.go.ke/budget-policy-statement/", "filename": "national_treasury_budget_policy.txt"},
    {"url": "https://www.treasury.go.ke/medium-term-debt-strategy/", "filename": "national_treasury_medium_term_debt.txt"},
    {"url": "https://www.treasury.go.ke/economic-surveys/", "filename": "national_treasury_economic_surveys.txt"},
    # KIPPRA - Policy research
    {"url": "https://kippra.or.ke/about/", "filename": "kippra_about.txt"},
    {"url": "https://kippra.or.ke/kenya-economic-report/", "filename": "kippra_kenya_economic_report.txt"},
    {"url": "https://kippra.or.ke/policy-briefs/", "filename": "kippra_policy_briefs.txt"},
    {"url": "https://kippra.or.ke/msme-policy/", "filename": "kippra_msme_policy.txt"},
    {"url": "https://kippra.or.ke/kenya-economic-report-2024/", "filename": "kippra_economic_report_2024.txt"},
    # ICT / Digital Economy Policy
    {"url": "https://ict.go.ke/about/", "filename": "ict_authority_about.txt"},
    {"url": "https://ict.go.ke/digital-economy/", "filename": "ict_digital_economy_policy.txt"},
    # State Department for MSMEs
    {"url": "https://msme.go.ke/policy-framework/", "filename": "msme_policy_framework.txt"},
    {"url": "https://msme.go.ke/msme-act/", "filename": "msme_act_kenya.txt"},
    {"url": "https://msme.go.ke/national-msme-policy/", "filename": "kenya_national_msme_policy.txt"},
    # NDMA
    {"url": "https://www.ndma.go.ke/about/", "filename": "ndma_about.txt"},
    {"url": "https://www.ndma.go.ke/strategic-plan/", "filename": "ndma_strategic_plan_overview.txt"},
    # World Bank Kenya
    {"url": "https://www.worldbank.org/en/country/kenya/overview", "filename": "worldbank_kenya_overview_2024.txt"},
    {"url": "https://www.worldbank.org/en/country/kenya/publication/kenya-economic-update", "filename": "worldbank_kenya_economic_update.txt"},
    # IMF Kenya
    {"url": "https://www.imf.org/en/countries/KEN", "filename": "imf_kenya_country_overview.txt"},
    # AfDB Kenya
    {"url": "https://www.afdb.org/en/countries/east-africa/kenya", "filename": "afdb_kenya_country_strategy.txt"},
    # UN Kenya
    {"url": "https://kenya.un.org/en/about/about-the-un-in-kenya", "filename": "un_kenya_about.txt"},
    {"url": "https://kenya.un.org/en/sdgs", "filename": "un_kenya_sdgs_2024.txt"},
    # UNCTAD
    {"url": "https://unctad.org/country/kenya", "filename": "unctad_kenya_country_profile.txt"},
    # Kenya Sessional Papers
    {"url": "https://www.parliament.go.ke/sessional-papers", "filename": "kenya_parliament_sessional_papers.txt"},
    # Big 4 Agenda
    {"url": "https://big4.delivery.go.ke/", "filename": "kenya_big4_agenda_delivery.txt"},
    # Kenya Climate Policy
    {"url": "https://www.environment.go.ke/climate-change/", "filename": "kenya_climate_change_policy.txt"},
    {"url": "https://www.environment.go.ke/nationally-determined-contribution/", "filename": "kenya_ndc_2030.txt"},
]

PDF_FILES = [
    # Kenya Budget 2024/2025
    {
        "url": "https://www.treasury.go.ke/wp-content/uploads/2024/06/Budget-Statement-2024-2025.pdf",
        "filename": "kenya_budget_statement_2024_2025.pdf"
    },
    # Kenya Economic Survey 2024
    {
        "url": "https://www.knbs.or.ke/download/economic-survey-2024/",
        "filename": "kenya_economic_survey_2024.pdf"
    },
    # KIPPRA Kenya Economic Report 2024
    {
        "url": "https://kippra.or.ke/wp-content/uploads/2024/Kenya-Economic-Report-2024.pdf",
        "filename": "kippra_kenya_economic_report_2024.pdf"
    },
    # Kenya MSME Policy 2020
    {
        "url": "https://msme.go.ke/wp-content/uploads/2020/Kenya-MSME-Policy-2020.pdf",
        "filename": "kenya_msme_policy_2020.pdf"
    },
    # Kenya Medium Term Plan IV 2023-2027
    {
        "url": "https://vision2030.go.ke/wp-content/uploads/2023/MTP-IV-2023-2027.pdf",
        "filename": "kenya_mtp4_2023_2027.pdf"
    },
    # World Bank Kenya Economic Update 2024
    {
        "url": "https://documents1.worldbank.org/curated/en/099021424095538281/pdf/Kenya-Economic-Update.pdf",
        "filename": "worldbank_kenya_economic_update_2024.pdf"
    },
    # AfDB Kenya Country Strategy
    {
        "url": "https://www.afdb.org/fileadmin/uploads/afdb/Documents/Project-and-Operations/Kenya_Country_Strategy_Paper.pdf",
        "filename": "afdb_kenya_country_strategy_paper.pdf"
    },
    # IMF Kenya Article IV 2024
    {
        "url": "https://www.imf.org/en/Publications/CR/Issues/2024/Kenya-Article-IV.pdf",
        "filename": "imf_kenya_article_iv_2024.pdf"
    },
    # Kenya NDC 2030
    {
        "url": "https://www.environment.go.ke/wp-content/uploads/2020/11/Kenya-NDC-2030.pdf",
        "filename": "kenya_ndc_2030_full.pdf"
    },
    # UNCTAD Kenya MSME Report
    {
        "url": "https://unctad.org/system/files/official-document/ditcted2023d1_en.pdf",
        "filename": "unctad_kenya_msme_report_2023.pdf"
    },
]

def scrape(url, fn):
    p = DOCS_DIR / fn
    if p.exists(): print(f"  [SKIP] {fn}"); return
    try:
        r = requests.get(url, headers=HEADERS, timeout=30); r.raise_for_status()
        s = BeautifulSoup(r.text, "html.parser")
        [t.decompose() for t in s(["script","style","nav","footer","header","aside"])]
        c = "\n".join([l for l in s.get_text("\n", strip=True).splitlines() if l.strip()])
        p.write_text(f"SOURCE: {url}\nKB: kb8_national_policy_strategy\n\n{c}", encoding="utf-8")
        print(f"  [OK] {fn} ({len(c):,} chars)")
    except Exception as e: print(f"  [ERR] {fn} - {e}")

def dl(url, fn):
    p = DOCS_DIR / fn
    if p.exists(): print(f"  [SKIP] {fn}"); return
    try:
        r = requests.get(url, headers=HEADERS, timeout=60, stream=True); r.raise_for_status()
        with open(p, "wb") as f:
            for chunk in r.iter_content(8192): f.write(chunk)
        print(f"  [PDF] {fn} ({p.stat().st_size//1024} KB)")
    except Exception as e: print(f"  [ERR] {fn} - {e}")

if __name__ == "__main__":
    print("\nKB8 - National Policy & Strategy")
    [scrape(i["url"], i["filename"]) or time.sleep(1) for i in WEB_PAGES]
    [dl(i["url"], i["filename"]) or time.sleep(2) for i in PDF_FILES]
    print(f"Done. {len(list(DOCS_DIR.glob('*.txt')))} txt, {len(list(DOCS_DIR.glob('*.pdf')))} pdf")
