import requests, time
from bs4 import BeautifulSoup
from pathlib import Path

DOCS_DIR = Path("documents/kb5_digital_trade")
DOCS_DIR.mkdir(parents=True, exist_ok=True)
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0.0.0"}

WEB_PAGES = [
    # KPLC electricity
    {"url": "https://kplc.co.ke/content/item/1/customer-charter", "filename": "kplc_customer_charter.txt"},
    {"url": "https://kplc.co.ke/content/item/1/customer-support", "filename": "kplc_customer_support.txt"},
    {"url": "https://kplc.co.ke/content/item/1/sme-connection-guide", "filename": "kplc_sme_connection_guide.txt"},
    {"url": "https://kplc.co.ke/content/item/1/sme-connection-procedures", "filename": "kplc_sme_connection_procedures.txt"},
    {"url": "https://kplc.co.ke/content/item/1/tariff-faq", "filename": "kplc_tariff_faq.txt"},
    {"url": "https://kplc.co.ke/content/item/1/tiered-tariff-msme-guide", "filename": "kplc_tiered_tariff_msme_guide.txt"},
    {"url": "https://kplc.co.ke/content/item/1/electricity-tariff-reduction-2024", "filename": "kplc_electricity_tariff_reduction_2024.txt"},
    {"url": "https://kplc.co.ke/content/item/1/sme-commercial-tariffs-2025", "filename": "kplc_sme_commercial_tariffs_2025.txt"},
    # KRB roads
    {"url": "https://www.krb.go.ke/about/what-we-do/", "filename": "krb_about_what_we_do.txt"},
    {"url": "https://www.krb.go.ke/organogram-functions/", "filename": "krb_organogram_functions.txt"},
    # KIPPRA
    {"url": "https://kippra.or.ke/afcfta-kenya/", "filename": "kippra_afcfta_kenya.txt"},
    {"url": "https://kippra.or.ke/digital-needs-msme/", "filename": "kippra_digital_needs_msme.txt"},
    # MSME digital
    {"url": "https://msme.go.ke/digital-payments-guide/", "filename": "kenya_digital_payments_msme_guide.txt"},
    {"url": "https://msme.go.ke/energy-cost-tracker/", "filename": "kenya_energy_cost_msme_tracker.txt"},
    {"url": "https://msme.go.ke/informal-economy-formalization/", "filename": "kenya_informal_economy_formalization.txt"},
    {"url": "https://jkf.or.ke/digital-skills-nairobi/", "filename": "jua_kali_digital_skills_nairobi_2024.txt"},
    {"url": "https://keproba.go.ke/trade-agreements/", "filename": "kenya_trade_agreements_overview.txt"},
    # Ajira Digital (from scrape_ajira.py)
    {"url": "https://ajiradigital.go.ke/", "filename": "ajira_digital_main_portal.txt"},
    {"url": "https://www.trainer.ajiradigital.go.ke/", "filename": "ajira_digital_trainer_portal.txt"},
    {"url": "https://blog.ajiradigital.go.ke/index.php/2020/09/15/spotlight-on-partners/", "filename": "ajira_digital_blog_partners.txt"},
    {"url": "https://blog.ajiradigital.go.ke/index.php/2020/10/23/realizing-the-digital-economy/", "filename": "ajira_digital_blog_economy.txt"},
    {"url": "https://mastercardfdn.org/en/what-we-do/our-programs/ajira-digital-program/", "filename": "ajira_digital_mastercard_overview.txt"},
    {"url": "https://emobilis.ac.ke/ajira", "filename": "ajira_digital_emobilis_programme.txt"},
    {"url": "https://www.kenyanews.go.ke/ajira-digital-programme-helping-youth-to-earn-a-living/", "filename": "ajira_digital_kenya_news_agency.txt"},
    {"url": "https://techweez.com/2023/07/31/kbc-ajira-jitume-digital-id-ict-ministry/", "filename": "ajira_digital_ict_ministry_scorecard_2023.txt"},
    # Digital finance (from scrape_digital_finance.py)
    {"url": "https://www.safaricom.co.ke/business/sme/m-pesa/", "filename": "safaricom_mpesa_sme_overview.txt"},
    {"url": "https://www.pesalink.co.ke/", "filename": "pesalink_overview.txt"},
    {"url": "https://www.centralbank.go.ke/national-payments-system/", "filename": "cbk_national_payments_system.txt"},
    # Infrastructure (from scrape_infrastructure.py)
    {"url": "https://www.kura.go.ke/", "filename": "kura_urban_roads_overview.txt"},
    {"url": "https://www.ntsa.go.ke/", "filename": "ntsa_transport_overview.txt"},
    # E-commerce (from scrape_ecommerce.py)
    {"url": "https://www.jumia.co.ke/seller/", "filename": "jumia_seller_guide.txt"},
    {"url": "https://www.kilimall.co.ke/seller", "filename": "kilimall_seller_guide.txt"},
    # Trade (from scrape_trade.py)
    {"url": "https://www.eac.int/trade", "filename": "eac_trade_overview.txt"},
    {"url": "https://www.comesa.int/trade/", "filename": "comesa_trade_overview.txt"},
    {"url": "https://keproba.go.ke/export-guide/", "filename": "keproba_export_guide.txt"},
]

PDF_FILES = [
    {"url": "https://kplc.co.ke/img/full/Electricity-Bill-Components-Guide.pdf", "filename": "kplc_electricity_bill_components_guide.pdf"},
    {"url": "https://ict.go.ke/wp-content/uploads/2023/01/Kenya-National-Digital-Masterplan-2022-2032.pdf", "filename": "kenya_national_digital_masterplan_2022_2.pdf"},
    {"url": "https://unctad.org/system/files/official-document/kenya-msme-challenges-opportunities.pdf", "filename": "unctad_kenya_msme_challenges_opportun.pdf"},
]

def scrape(url, fn):
    p = DOCS_DIR / fn
    if p.exists(): print(f"  [SKIP] {fn}"); return
    try:
        r = requests.get(url, headers=HEADERS, timeout=30); r.raise_for_status()
        s = BeautifulSoup(r.text, "html.parser")
        [t.decompose() for t in s(["script","style","nav","footer","header","aside"])]
        c = "\n".join([l for l in s.get_text("\n", strip=True).splitlines() if l.strip()])
        p.write_text(f"SOURCE: {url}\nKB: kb5_digital_trade\n\n{c}", encoding="utf-8")
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
    print("\nKB5 - Digital & Trade")
    [scrape(i["url"], i["filename"]) or time.sleep(1) for i in WEB_PAGES]
    [dl(i["url"], i["filename"]) or time.sleep(2) for i in PDF_FILES]
    print(f"Done. {len(list(DOCS_DIR.glob('*.txt')))} txt, {len(list(DOCS_DIR.glob('*.pdf')))} pdf")
