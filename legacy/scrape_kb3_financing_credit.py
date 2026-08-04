import requests, time
from bs4 import BeautifulSoup
from pathlib import Path

DOCS_DIR = Path("documents/kb3_financing_credit")
DOCS_DIR.mkdir(parents=True, exist_ok=True)
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0.0.0"}

WEB_PAGES = [
    {"url": "https://www.ifc.org/en/topic/msme-finance", "filename": "ifc_msme_finance_overview.txt"},
    {"url": "https://www.youthfund.go.ke/about/", "filename": "yedf_about.txt"},
    {"url": "https://www.smep.co.ke/about/", "filename": "smep_about.txt"},
    {"url": "https://www.smep.co.ke/products/", "filename": "smep_business_products.txt"},
    {"url": "https://www.smep.co.ke/loans/sme-loans/", "filename": "smep_sme_loans.txt"},
    {"url": "https://www.smep.co.ke/loans/trade-finance/", "filename": "smep_trade_finance.txt"},
    {"url": "https://www.smep.co.ke/loans/", "filename": "smep_loan_products.txt"},
    {"url": "https://www.kwft.co.ke/personal/products/", "filename": "kwft_about_products.txt"},
    {"url": "https://www.kwft.co.ke/business/loans/", "filename": "kwft_business_loans.txt"},
    {"url": "https://www.safaricom.co.ke/personal/m-pesa/do-more-with-m-pesa/fuliza-m-pesa", "filename": "safaricom_fuliza_overdraft.txt"},
    {"url": "https://www.safaricom.co.ke/business/sme/m-pesa/pochi-la-biashara", "filename": "safaricom_pochi_la_biashara.txt"},
    {"url": "https://kippra.or.ke/msme-credit-guarantee/", "filename": "kippra_msme_credit_guarantee.txt"},
    {"url": "https://kippra.or.ke/nurturing-small-businesses/", "filename": "kippra_nurturing_small_businesses.txt"},
    {"url": "https://www.worldbank.org/en/country/kenya/overview", "filename": "worldbank_kenya_overview.txt"},
    {"url": "https://msme.go.ke/community-financing/", "filename": "kenya_community_financing_msme.txt"},
    {"url": "https://msme.go.ke/financial-planning-guide/", "filename": "kenya_sme_financial_planning_guide.txt"},
    {"url": "https://www.epra.go.ke/electricity", "filename": "epra_electricity_regulation.txt"},
    {"url": "https://kplc.co.ke/customer-support", "filename": "kplc_sme_connection_procedures.txt"},
    {"url": "https://www.stimatracker.com/", "filename": "kenya_energy_cost_msme_tracker.txt"},
    {"url": "https://serrarigroup.com/business-strategy-and-operating-plan-kenya-sme-guide-2026/", "filename": "kenya_sme_business_plan_guide_2025.txt"},
    {"url": "https://serrarigroup.com/business-financial-planning-kenya-sme-guide-2026/", "filename": "kenya_sme_financial_planning_guide.txt"},
    {"url": "https://nextconsulting.co.ke/how-to-develop-a-business-plan-kenya/", "filename": "kenya_business_plan_how_to_write.txt"},
    {"url": "https://sbs.strathmore.edu/kenya-small-business-development-centers-kenya-sbdc-and-kenya-bankers-association-partner-to-empower-msmes-and-foster-financial-inclusion/", "filename": "kenya_sbdc_strathmore_msme_training.txt"},
    {"url": "https://www.fke-kenya.org/media-center/news/unveiling-future-work-fke-launches-skills-needs-survey-report", "filename": "fke_skills_needs_survey_report.txt"},
    {"url": "https://www.fke-kenya.org/index.php/media-center/opinion-pieces/federation-kenya-employers-footprints-skilling-kenya", "filename": "fke_skilling_kenya_msme.txt"},
    {"url": "https://www.labourmarket.go.ke/", "filename": "kenya_labour_market_information_system.txt"},
    {"url": "https://labourmarket.go.ke/resources/", "filename": "kenya_labour_market_resources.txt"},
    {"url": "https://kwftbank.com/", "filename": "kwft_about_products.txt"},
    {"url": "https://kwftbank.com/personal/loans/", "filename": "kwft_loan_products.txt"},
    {"url": "https://kwftbank.com/business/", "filename": "kwft_business_loans.txt"},
    {"url": "https://www.faulukenya.com/about-us", "filename": "faulu_about.txt"},
    {"url": "https://www.faulukenya.com/", "filename": "faulu_msme_banking.txt"},
    {"url": "https://www.faulukenya.com/business-banking/biashara-SME-loan/", "filename": "faulu_biashara_sme_loan.txt"},
    {"url": "https://www.faulukenya.com/business-banking/faulu-micro-unsecured-loan/", "filename": "faulu_micro_unsecured_loan.txt"},
    {"url": "https://www.faulukenya.com/business-banking/faulu-micro-secured-loan/", "filename": "faulu_micro_secured_loan.txt"},
    {"url": "https://www.faulukenya.com/about-us/media/faulu-bank-expands-its-customized-financial-solutions-to-empower-women-in-kenya/", "filename": "faulu_women_products.txt"},
    {"url": "https://smep.co.ke/about-us", "filename": "smep_about.txt"},
    {"url": "https://www.smep.co.ke/loan", "filename": "smep_loan_products.txt"},
    {"url": "https://smep.co.ke/sme-loans", "filename": "smep_sme_loans.txt"},
    {"url": "https://smep.co.ke/for-your-business", "filename": "smep_business_products.txt"},
    {"url": "https://smep.co.ke/trade_finance/loan", "filename": "smep_trade_finance.txt"},
    {"url": "https://www.businessradar.co.ke/blog/2024/10/18/full-list-of-all-licensed-microfinance-banks-in-kenya/", "filename": "microfinance_banks_kenya_2024.txt"},
    {"url": "https://kepsa.or.ke/smeshub/msme-financing-gateway", "filename": "kepsa_msme_financing_gateway.txt"},
    {"url": "https://kepsa.or.ke/kepsanews/kepsa-hosts-the-inaugural-annual-sme-conference-awards-and-exhibition", "filename": "kepsa_sme_conference_2024.txt"},
    {"url": "https://kepsa.or.ke/growing-an-inclusive-economy-creating-linkages-for-msmes-within-the-big-four-agenda/", "filename": "kepsa_msme_big_four_agenda.txt"},
    {"url": "https://kepsa.or.ke/kepsanews/kepsa-conducts-investor-readiness-business-training-for-sme-trainers", "filename": "kepsa_investor_readiness_msme.txt"},
    {"url": "https://kippra.or.ke/14355-2/", "filename": "kippra_nurturing_small_businesses.txt"},
    {"url": "https://kippra.or.ke/unlock-the-potential-of-micro-small-and-medium-enterprises-in-kenya/", "filename": "kippra_unlock_msme_potential.txt"},
    {"url": "https://kippra.or.ke/characteristics-of-kenyan-msmes-relevant-to-the-proposed-kenya-credit-guarantee-scheme/", "filename": "kippra_msme_credit_guarantee.txt"},
    {"url": "https://kippra.or.ke/supporting-the-digital-needs-for-micro-and-small-enterprises-in-kenya/", "filename": "kippra_digital_needs_msme.txt"},
    {"url": "https://kippra.or.ke/leveraging-on-ict-to-promote-innovations-amongst-msmes-in-kenya/", "filename": "kippra_ict_msme_innovations.txt"},
    {"url": "https://sbs.strathmore.edu/centers/center-for-entrepreneurship/", "filename": "strathmore_enterprise_development_centre.txt"},
    {"url": "https://sbs.strathmore.edu/about-sbs/", "filename": "strathmore_sbs_about.txt"},
]

PDF_FILES = [
    {"url": "https://www.ifc.org/content/dam/ifc/doc/mgrt/msme-fi-gap-report.pdf", "filename": "ifc_msme_finance_gap_report.pdf"},
    {"url": "https://www.kba.co.ke/downloads/KBA-MSME-Credit-Guarantees-Report.pdf", "filename": "kba_msme_credit_guarantees_report.pdf"},
    {"url": "https://www.youthfund.go.ke/downloads/YEDF-Loan-Products-Brochure.pdf", "filename": "yedf_loan_products_brochure.pdf"},
    {"url": "https://www.youthfund.go.ke/downloads/YEDF-Strategic-Plan-2020-2024.pdf", "filename": "yedf_strategic_plan_2020_2024.pdf"},
    {"url": "https://documents1.worldbank.org/curated/en/Kenya-Economic-Update-Dec2023.pdf", "filename": "worldbank_kenya_economic_update_dec20.pdf"},
    {"url": "https://documents1.worldbank.org/curated/en/kenya-msme-safer-report-2023.pdf", "filename": "worldbank_kenya_msme_safer_report_202.pdf"},
]

def scrape(url, fn):
    p = DOCS_DIR / fn
    if p.exists(): print(f"  [SKIP] {fn}"); return
    try:
        r = requests.get(url, headers=HEADERS, timeout=30); r.raise_for_status()
        s = BeautifulSoup(r.text, "html.parser")
        [t.decompose() for t in s(["script","style","nav","footer","header","aside"])]
        c = "\n".join([l for l in s.get_text("\n", strip=True).splitlines() if l.strip()])
        p.write_text(f"SOURCE: {url}\nKB: kb3_financing_credit\n\n{c}", encoding="utf-8")
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
    print("\nKB3 - Financing & Credit")
    [scrape(i["url"], i["filename"]) or time.sleep(1) for i in WEB_PAGES]
    [dl(i["url"], i["filename"]) or time.sleep(2) for i in PDF_FILES]
    print(f"Done. {len(list(DOCS_DIR.glob('*.txt')))} txt, {len(list(DOCS_DIR.glob('*.pdf')))} pdf")
