import requests, time
from bs4 import BeautifulSoup
from pathlib import Path

DOCS_DIR = Path("documents/kb2_tax_kra")
DOCS_DIR.mkdir(parents=True, exist_ok=True)
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0.0.0"}

WEB_PAGES = [
    {"url": "https://www.kra.go.ke/helping-tax-payers/faqs/taxes-for-businesses", "filename": "kra_business_types_of_taxes.txt"},
    {"url": "https://etims.kra.go.ke/", "filename": "kra_etims_what_is.txt"},
    {"url": "https://www.kra.go.ke/helping-tax-payers/faqs/etims-faqs", "filename": "kra_etims_noticefaq.txt"},
    {"url": "https://etims.kra.go.ke/how-to-onboard", "filename": "kra_etims_how_to_onboard.txt"},
    {"url": "https://etims.kra.go.ke/installation-guide", "filename": "kra_etims_install.txt"},
    {"url": "https://www.kra.go.ke/individual/filing-paying/types-of-taxes/income-tax-company", "filename": "kra_income_tax.txt"},
    {"url": "https://www.kra.go.ke/individual/filing-paying/types-of-taxes/paye", "filename": "kra_paye.txt"},
    {"url": "https://www.kra.go.ke/individual/filing-paying/types-of-taxes/rental-income", "filename": "kra_rental_income_tax.txt"},
    {"url": "https://www.kra.go.ke/individual/filing-paying/types-of-taxes/turnover-tax", "filename": "kra_turnover_tax.txt"},
    {"url": "https://www.kra.go.ke/individual/filing-paying/types-of-taxes/value-added-tax", "filename": "kra_vat.txt"},
    {"url": "https://www.kra.go.ke/helping-tax-payers/faqs/tax-compliance", "filename": "kra_tax_compliance.txt"},
    {"url": "https://www.kra.go.ke/individual/filing-paying/tax-obligations/offences-penalties", "filename": "kra_offences_penalties.txt"},
    {"url": "https://www.kra.go.ke/individual/filing-paying/registration-types/pin-registration", "filename": "kra_pin_registration.txt"},
    {"url": "https://www.kra.go.ke/sw/mwongozo-wa-ushuru-wa-biashara", "filename": "kra_sw_mwongozo_ushuru_biashara.txt"},
    {"url": "https://www.kra.go.ke/sw/usajili-biashara-pin", "filename": "kra_sw_usajili_biashara_pin.txt"},
]

PDF_FILES = [
    {"url": "https://kenyalaw.org/kl/fileadmin/pdfdownloads/Acts/IncomeTaxAct_Cap470.pdf", "filename": "income_tax_act_cap470.pdf"},
    {"url": "https://kenyalaw.org/kl/fileadmin/pdfdownloads/Acts/TaxProceduresAct_No29of2015.pdf", "filename": "tax_procedures_act_cap469b.pdf"},
    {"url": "https://www.kra.go.ke/images/publications/KRA-Annual-Revenue-Performance-2023-2024.pdf", "filename": "kra_annual_revenue_2023_2024.pdf"},
    {"url": "https://etims.kra.go.ke/downloads/eTIMS-Individual-Invoicing-Guide.pdf", "filename": "kra_etims_individual_invoicing_guide.pdf"},
    {"url": "https://etims.kra.go.ke/downloads/eTIMS-Online-Portal-Guide-2024.pdf", "filename": "kra_etims_online_portal_guide_2024.pdf"},
    {"url": "https://etims.kra.go.ke/downloads/eTIMS-Windows-User-Guide-2024.pdf", "filename": "kra_etims_windows_user_guide_2024.pdf"},
]

def scrape(url, fn):
    p = DOCS_DIR / fn
    if p.exists(): print(f"  [SKIP] {fn}"); return
    try:
        r = requests.get(url, headers=HEADERS, timeout=30); r.raise_for_status()
        s = BeautifulSoup(r.text, "html.parser")
        [t.decompose() for t in s(["script","style","nav","footer","header","aside"])]
        c = "\n".join([l for l in s.get_text("\n", strip=True).splitlines() if l.strip()])
        p.write_text(f"SOURCE: {url}\nKB: kb2_tax_kra\n\n{c}", encoding="utf-8")
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
    print("\nKB2 - Tax & KRA")
    [scrape(i["url"], i["filename"]) or time.sleep(1) for i in WEB_PAGES]
    [dl(i["url"], i["filename"]) or time.sleep(2) for i in PDF_FILES]
    print(f"Done. {len(list(DOCS_DIR.glob('*.txt')))} txt, {len(list(DOCS_DIR.glob('*.pdf')))} pdf")
