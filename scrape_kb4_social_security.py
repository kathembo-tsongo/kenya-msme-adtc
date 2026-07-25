import requests, time
from bs4 import BeautifulSoup
from pathlib import Path

DOCS_DIR = Path("documents/kb4_social_security")
DOCS_DIR.mkdir(parents=True, exist_ok=True)
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0.0.0"}

WEB_PAGES = [
    {"url": "https://www.nssf.or.ke/faqs/", "filename": "nssf_faq.txt"},
    {"url": "https://www.nssf.or.ke/employer/employer-notice-2024/", "filename": "nssf_employer_notice_2024.txt"},
    {"url": "https://www.nssf.or.ke/contribution-rates/", "filename": "nssf_new_contribution_rates.txt"},
    {"url": "https://www.nssf.or.ke/registration/", "filename": "nssf_registration_forms.txt"},
    {"url": "https://www.sha.go.ke/about/", "filename": "sha_about_shif.txt"},
    {"url": "https://www.sha.go.ke/employer-portal/", "filename": "sha_employer_portal_terms.txt"},
    {"url": "https://www.ira.go.ke/about/", "filename": "ira_about_insurance_regulation.txt"},
    {"url": "https://www.ira.go.ke/consumer-education/", "filename": "ira_consumer_education_insura.txt"},
    {"url": "https://www.ira.go.ke/downloads/", "filename": "ira_insurance_downloads.txt"},
    {"url": "https://www.ira.go.ke/msme-insurance-survey/", "filename": "ira_msme_insurance_survey_circular.txt"},
    {"url": "https://www.nita.go.ke/catalogue-curricula/", "filename": "nita_catalogue_curricula.txt"},
    {"url": "https://www.nita.go.ke/training-programs/", "filename": "nita_current_training_programs.txt"},
    {"url": "https://www.nita.go.ke/industrial-training-levy/", "filename": "nita_industrial_training_levy.txt"},
    {"url": "https://www.nita.go.ke/levy-inspectorate/", "filename": "nita_levy_inspectorate.txt"},
    {"url": "https://www.nita.go.ke/training-reimbursement/", "filename": "nita_training_reimbursement.txt"},
    {"url": "https://www.nita.go.ke/training-reimbursement-guidelines/", "filename": "nita_training_reimbursement_guidelines.txt"},
    {"url": "https://www.ira.go.ke/", "filename": "ira_about_insurance_regulation.txt"},
    {"url": "https://www.ira.go.ke/index.php/circular-2023", "filename": "ira_msme_insurance_survey_circular.txt"},
    {"url": "https://www.ira.go.ke/index.php/consumer-education", "filename": "ira_consumer_education_insurance.txt"},
    {"url": "https://ndma.go.ke/drought-resilience/", "filename": "ndma_drought_resilience.txt"},
    {"url": "https://ndma.go.ke/about-ndma/", "filename": "ndma_about_mandate.txt"},
    {"url": "https://napcentral.org/nap-summaries/kenya", "filename": "kenya_nap_climate_adaptation.txt"},
    {"url": "https://medium.com/mercy-corps-social-venture-fund/understanding-msme-resilience-to-climate-change-cd50355bd31b", "filename": "mercy_corps_msme_climate_resilience_kenya.txt"},
    {"url": "https://unfccc.int/sites/default/files/resource/Kenya_NAP.pdf", "filename": "kenya_national_climate_change_action_plan.txt"},
    {"url": "https://www.akinsurance.org/", "filename": "aki_insurance_kenya_msme.txt"},
    {"url": "https://www.nssf.or.ke/new-contribution-rates", "filename": "nssf_new_contribution_rates.txt"},
    {"url": "https://www.nssf.or.ke/notice-to-employers-on-the-updated-nssf-rates", "filename": "nssf_employer_notice_2024.txt"},
    {"url": "https://www.nssf.or.ke/download-category/application-and-registration-forms", "filename": "nssf_registration_forms.txt"},
    {"url": "https://www.nssf.or.ke/faq", "filename": "nssf_faq.txt"},
    {"url": "https://employers.sha.go.ke/terms-and-conditions", "filename": "sha_employer_portal_terms.txt"},
    {"url": "https://sha.go.ke/", "filename": "sha_about_shif.txt"},
    {"url": "https://www.nita.go.ke/our-services/levy-inspectorate.html", "filename": "nita_levy_inspectorate.txt"},
    {"url": "https://www.nita.go.ke/media-centre/downloads/16-industrial-training-levy-procedures.html", "filename": "nita_industrial_training_levy.txt"},
    {"url": "https://nita.go.ke/component/edocman/guidelines-for-training-and-reimbursement.html", "filename": "nita_training_reimbursement_guidelines.txt"},
]

PDF_FILES = [
    {"url": "https://kenyalaw.org/kl/fileadmin/pdfdownloads/Acts/NSSFAct_No45of2013.pdf", "filename": "nssf_act_2013.pdf"},
    {"url": "https://www.sha.go.ke/wp-content/uploads/2024/08/SHIF-General-Regulations-2024.pdf", "filename": "shif_general_regulations_2024.pdf"},
    {"url": "https://kenyalaw.org/kl/fileadmin/pdfdownloads/Acts/SocialHealthInsuranceAct_2023.pdf", "filename": "social_health_insurance_act_2023.pdf"},
    {"url": "https://www.ira.go.ke/images/docs/Claims-Report-Q1-2024.pdf", "filename": "ira_claims_report_q1_2024.pdf"},
    {"url": "https://www.ira.go.ke/images/docs/Insurance-Industry-Report-Q4-2023.pdf", "filename": "ira_insurance_industry_q4_2023.pdf"},
]

def scrape(url, fn):
    p = DOCS_DIR / fn
    if p.exists(): print(f"  [SKIP] {fn}"); return
    try:
        r = requests.get(url, headers=HEADERS, timeout=30); r.raise_for_status()
        s = BeautifulSoup(r.text, "html.parser")
        [t.decompose() for t in s(["script","style","nav","footer","header","aside"])]
        c = "\n".join([l for l in s.get_text("\n", strip=True).splitlines() if l.strip()])
        p.write_text(f"SOURCE: {url}\nKB: kb4_social_security\n\n{c}", encoding="utf-8")
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
    print("\nKB4 - Social Security")
    [scrape(i["url"], i["filename"]) or time.sleep(1) for i in WEB_PAGES]
    [dl(i["url"], i["filename"]) or time.sleep(2) for i in PDF_FILES]
    print(f"Done. {len(list(DOCS_DIR.glob('*.txt')))} txt, {len(list(DOCS_DIR.glob('*.pdf')))} pdf")
