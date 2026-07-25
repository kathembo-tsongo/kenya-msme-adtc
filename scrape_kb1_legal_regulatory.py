import requests, time
from bs4 import BeautifulSoup
from pathlib import Path

DOCS_DIR = Path("documents/kb1_legal_regulatory")
DOCS_DIR.mkdir(parents=True, exist_ok=True)
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0.0.0"}

WEB_PAGES = [
    {"url": "https://brs.go.ke/about-brs/", "filename": "brs_about_business_registration.txt"},
    {"url": "https://brs.go.ke/business-name-registration/", "filename": "brs_business_name_registration_guide.txt"},
    {"url": "https://brs.go.ke/company-registration/", "filename": "brs_company_registration_guide.txt"},
    {"url": "https://brs.go.ke/company-types/", "filename": "brs_company_types_overview.txt"},
    {"url": "https://brs.go.ke/frequently-asked-questions/", "filename": "brs_faqs_complete_guide.txt"},
    {"url": "https://www.kebs.org/index.php/food-safety-standards/", "filename": "kebs_food_safety_management.txt"},
    {"url": "https://www.kebs.org/index.php/faqs/", "filename": "kebs_quality_assurance_faqs.txt"},
    {"url": "https://msme.go.ke/", "filename": "msme_state_dept.txt"},
    {"url": "https://msme.go.ke/business-guide/", "filename": "kenya_business_guide.txt"},
    {"url": "https://msme.go.ke/single-business-permit/", "filename": "kenya_single_business_permit_guide.txt"},
    {"url": "https://nairobi.go.ke/business-permits/", "filename": "nairobi_unified_business_permit.txt"},
    {"url": "https://nairobi.go.ke/faqs/", "filename": "nairobi_faqs_help_desks.txt"},
    {"url": "https://nairobi.go.ke/county-laws/", "filename": "nairobi_county_laws_business.txt"},
    {"url": "https://www.mombasa.go.ke/business-permits/", "filename": "mombasa_business_permit_procedure.txt"},
    {"url": "https://ipc.go.ke/msme-ip/", "filename": "ipc_intellectual_property_msme.txt"},
    {"url": "https://www.tveta.go.ke/about/", "filename": "tveta_about_tvet_system.txt"},
    {"url": "https://www.tveta.go.ke/accredited-institutions/", "filename": "tveta_accredited_institutions.txt"},
    {"url": "https://www.tveta.go.ke/tvet-courses/", "filename": "tveta_tvet_courses_list.txt"},
    {"url": "https://www.tveta.go.ke/standards/", "filename": "tveta_tvet_standards.txt"},
    {"url": "https://ca.go.ke/consumer-affairs/consumer-protection/", "filename": "ca_consumer_protection_framework.txt"},
    {"url": "https://pharmacyboardkenya.org/registration-enrollment/", "filename": "ppb_registration_enrollment.txt"},
    {"url": "https://pharmacyboardkenya.org/premises-licensing/", "filename": "ppb_premises_licensing_guide.txt"},
    {"url": "https://ktb.go.ke/tourism-licensing/", "filename": "ktb_tourism_licensing.txt"},
    {"url": "https://nairobi.go.ke/nairobi-city-county-government-unified-business-permit-ubp-permit-process", "filename": "nairobi_unified_business_permit.txt"},
    {"url": "https://nairobi.go.ke/unified-business-permit-ubp-usage", "filename": "nairobi_ubp_usage.txt"},
    {"url": "https://nairobi.go.ke/county-laws", "filename": "nairobi_county_laws_business.txt"},
    {"url": "https://nairobi.go.ke/faqs-and-help-desks", "filename": "nairobi_faqs_help_desks.txt"},
    {"url": "https://eprocedures.investkenya.go.ke/procedure/print/206/140/step/0?showRecourses=true&showCertification=false&l=en", "filename": "mombasa_business_permit_procedure.txt"},
    {"url": "https://www.mombasaassembly.go.ke/wp-content/uploads/2024/11/The_Mombasa_County_Finance_Bill-2024.pdf", "filename": "mombasa_county_finance_act_2024.txt"},
    {"url": "http://www.eservices.kisumu.go.ke/index.php/help/faq", "filename": "kisumu_business_permit_faq.txt"},
    {"url": "http://eservices.kisumu.go.ke/index.php?id=2", "filename": "kisumu_business_licensing.txt"},
    {"url": "https://eprocedures.investkenya.go.ke/media/Single_Business_Permit.2.pdf", "filename": "kenya_single_business_permit_guide.txt"},
    {"url": "https://www.doingbusinesskenya.go.ke/launch-your-business/", "filename": "doing_business_kenya_launch.txt"},
    {"url": "https://kebs.org/fsms/", "filename": "kebs_food_safety_management.txt"},
    {"url": "https://web.pharmacyboardkenya.org/download/guidelines-for-registration-and-licensing-of-premises/", "filename": "ppb_premises_licensing_guide.txt"},
    {"url": "https://web.pharmacyboardkenya.org/registration-and-enrollment/", "filename": "ppb_registration_enrollment.txt"},
    {"url": "https://www.ca.go.ke/licensing-procedures", "filename": "ca_licensing_procedures.txt"},
    {"url": "https://www.ca.go.ke/licensing-overview", "filename": "ca_licensing_overview.txt"},
    {"url": "https://www.ca.go.ke/license-application-forms-fees", "filename": "ca_license_fees.txt"},
    {"url": "https://www.ca.go.ke/market-structure", "filename": "ca_market_structure.txt"},
    {"url": "https://www.tourism.go.ke/", "filename": "ktb_tourism_licensing.txt"},
    {"url": "https://www.tveta.go.ke/", "filename": "tveta_about_tvet_system.txt"},
    {"url": "https://www.tveta.go.ke/accredited-tvet-institutions/", "filename": "tveta_accredited_institutions.txt"},
    {"url": "https://www.tveta.go.ke/tvet-standards/", "filename": "tveta_tvet_standards.txt"},
    {"url": "https://www.nita.go.ke/our-services/levy-inspectorate.html", "filename": "nita_levy_inspectorate.txt"},
    {"url": "https://www.nita.go.ke/careers/9-explore/325-catalogue-of-nita-curricula.html", "filename": "nita_catalogue_curricula.txt"},
    {"url": "https://www.nita.go.ke/media-centre/downloads/industrial-training-levy.html", "filename": "nita_industrial_training_levy.txt"},
    {"url": "https://nita.go.ke/component/edocman/guidelines-for-training-and-reimbursement.html", "filename": "nita_training_reimbursement.txt"},
    {"url": "https://www.nita.go.ke/index.php/84-national-industrial-vocational-training-centre-nivtc/241-current-training-programs", "filename": "nita_current_training_programs.txt"},
]

PDF_FILES = [
    {"url": "https://kenyalaw.org/kl/fileadmin/pdfdownloads/Acts/BusinessRegistrationServiceAct_No15of2015.pdf", "filename": "business_registration_act_cap499.pdf"},
    {"url": "https://kenyalaw.org/kl/fileadmin/pdfdownloads/Acts/ConsumerProtectionAct_No46of2012.pdf", "filename": "consumer_protection_act_cap504.pdf"},
    {"url": "https://kenyalaw.org/kl/fileadmin/pdfdownloads/Acts/EmploymentAct_Cap226.pdf", "filename": "employment_act_kenya_cap226.pdf"},
    {"url": "https://kenyalaw.org/kl/fileadmin/pdfdownloads/Acts/ValueAddedTaxAct_No35of2013.pdf", "filename": "vat_act_cap476.pdf"},
    {"url": "https://www.tveta.go.ke/wp-content/uploads/2023/08/TVETA-Accreditation-Handbook.pdf", "filename": "tveta_accreditation_handbook.pdf"},
    {"url": "https://www.mombasa.go.ke/wp-content/uploads/2024/07/Mombasa-County-Finance-Act-2024.pdf", "filename": "mombasa_county_finance_act_2024.pdf"},
    {"url": "https://www.kebs.org/index.php/download/standards-levy-act/?wpdmdl=4321", "filename": "kebs_standards_levy_msmes_2023.pdf"},
]

def scrape(url, fn):
    p = DOCS_DIR / fn
    if p.exists(): print(f"  [SKIP] {fn}"); return
    try:
        r = requests.get(url, headers=HEADERS, timeout=30); r.raise_for_status()
        s = BeautifulSoup(r.text, "html.parser")
        [t.decompose() for t in s(["script","style","nav","footer","header","aside"])]
        c = "\n".join([l for l in s.get_text("\n", strip=True).splitlines() if l.strip()])
        p.write_text(f"SOURCE: {url}\nKB: kb1_legal_regulatory\n\n{c}", encoding="utf-8")
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
    print("\nKB1 - Legal & Regulatory")
    [scrape(i["url"], i["filename"]) or time.sleep(1) for i in WEB_PAGES]
    [dl(i["url"], i["filename"]) or time.sleep(2) for i in PDF_FILES]
    print(f"Done. {len(list(DOCS_DIR.glob('*.txt')))} txt, {len(list(DOCS_DIR.glob('*.pdf')))} pdf")
