import requests, time
from bs4 import BeautifulSoup
from pathlib import Path

DOCS_DIR = Path("documents/kb7_culture_context")
DOCS_DIR.mkdir(parents=True, exist_ok=True)
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0.0.0"}

WEB_PAGES = [
    {"url": "https://jkf.or.ke/about/associations/", "filename": "kenya_jua_kali_associations_msme.txt"},
    {"url": "https://jkf.or.ke/about/federation/", "filename": "kenya_jua_kali_federation_msme.txt"},
    {"url": "https://www.lmis.go.ke/", "filename": "kenya_labour_market_information_system.txt"},
    {"url": "https://www.lmis.go.ke/resources/", "filename": "kenya_labour_market_resources.txt"},
    {"url": "https://msme.go.ke/cultural-business-trust/", "filename": "kenya_cultural_business_trust_networks.txt"},
    {"url": "https://msme.go.ke/entrepreneurship-kiswahili/", "filename": "kenya_cultural_entrepreneurship_kiswahi.txt"},
    {"url": "https://msme.go.ke/cultural-norms-entrepreneurship/", "filename": "kenya_cultural_norms_entrepreneurship_re.txt"},
    {"url": "https://msme.go.ke/socio-cultural-business/", "filename": "kenya_socio_cultural_business_environmen.txt"},
    {"url": "https://msme.go.ke/local-languages-context/", "filename": "kenya_local_languages_cultural_context.txt"},
    {"url": "https://msme.go.ke/business-plan-guide-2025/", "filename": "kenya_sme_business_plan_guide_2025.txt"},
    {"url": "https://msme.go.ke/management-skills-guide/", "filename": "kenya_sme_management_skills_guide.txt"},
    {"url": "https://sbdc.strathmore.edu/msme-training/", "filename": "kenya_sbdc_strathmore_msme_training.txt"},
    {"url": "https://kenya.un.org/en/sdgs/msme-day", "filename": "un_msme_day_overview.txt"},
    {"url": "https://files.eric.ed.gov/fulltext/EJ1417302.pdf", "filename": "jua_kali_digital_skills_nairobi_2024.txt"},
    {"url": "https://www.researchsquare.com/article/rs-4330945/v1", "filename": "jua_kali_sustainability_challenges_nairobi.txt"},
    {"url": "https://www.journals.uchicago.edu/doi/10.1086/508716", "filename": "chama_rosca_kenya_commitment.txt"},
    {"url": "https://kippra.or.ke/nurturing-small-businesses-in-the-informal-sector-in-kenya/", "filename": "kenya_informal_sector_msme_culture.txt"},
    {"url": "https://kippra.or.ke/supporting-the-digital-needs-for-micro-and-small-enterprises-in-kenya/", "filename": "kenya_jua_kali_associations_msme.txt"},
    {"url": "https://eujournal.org/index.php/esj/article/download/15615/15554", "filename": "kenya_women_chama_entrepreneurship.txt"},
    {"url": "https://www.knbs.or.ke/wp-content/uploads/2023/09/2016-Micro-Small-and-Medium-Enterprises-Basic-Report.pdf", "filename": "kenya_informal_sector_skills_survey.txt"},
    {"url": "https://msea.go.ke/", "filename": "kenya_cultural_business_trust_networks.txt"},
    {"url": "https://sdgs.un.org/sites/default/files/2022-03/Policy%20guidelines%20for%20the%20formalization%20of%20MSMEs%20in%20Kenya.pdf", "filename": "kenya_informal_economy_formalization.txt"},
    {"url": "https://kippra.or.ke/unlock-the-potential-of-micro-small-and-medium-enterprises-in-kenya/", "filename": "kenya_jua_kali_federation_msme.txt"},
    {"url": "https://wef.go.ke/", "filename": "kenya_msme_gender_culture_2024.txt"},
    {"url": "https://www.fsdkenya.org/blogs-publications/blog/insights-from-the-2024-finaccess-sector-reports/", "filename": "kenya_community_financing_msme.txt"},
    {"url": "https://www.kra.go.ke/sw/mtu-binafsi/kufungua-kulipa/aina-za-ushuru/kodi-ya-mauzo", "filename": "kra_kiswahili_kodi_mauzo_tot.txt"},
    {"url": "https://www.kra.go.ke/sw/biashara/ushirika-wa-makampuni/Ubia-wa-makampuni-huweka-kodi/Ubia-wa-kampuni-aina-za-kodi", "filename": "kra_kiswahili_aina_ushuru_biashara.txt"},
    {"url": "https://www.kra.go.ke/sw/biashara/ushirika-wa-makampuni/Ubia-wa-makampuni-huweka-kodi/malipo-ya-faili-ya-ushirika-wa-kampuni", "filename": "kra_kiswahili_kufungua_kulipa_kodi.txt"},
    {"url": "https://kra.go.ke/sw/individual/filing-paying/types-of-taxes/individual-income-tax", "filename": "kra_kiswahili_kodi_mapato_mtu.txt"},
    {"url": "https://www.kra.go.ke/sw/individual/filing-paying/types-of-taxes/installment-tax", "filename": "kra_kiswahili_kodi_awamu.txt"},
    {"url": "https://www.kra.go.ke/sw/helping-tax-payers/faqs", "filename": "kra_kiswahili_msaada_walipakodi_faq.txt"},
    {"url": "https://kra.go.ke/sw/kituo-cha-habari/blog/Kodi-ya-mauzo-ya-1511-iliyoundwa-kufanya-biashara-ndogo-kutii-zaidi", "filename": "kra_kiswahili_tot_biashara_ndogo.txt"},
    {"url": "https://kra.go.ke/sw/kituo-cha-habari/vyombo-vya-habari-ya-kutolewa/939-shughuli-za-ushuru,-utiifu-umerahisishwa-kupitia-programu-ya-simu", "filename": "kra_kiswahili_app_huduma_biashara.txt"},
    {"url": "https://kra.go.ke/sw/kituo-cha-habari/blog/953-kodi-ya-huduma-ya-kidijitali-kiashirio-cha-kubadilisha-michakato-ya-biashara-nchini-kenya", "filename": "kra_kiswahili_dijitali_biashara.txt"},
    {"url": "https://www.kra.go.ke/sw/helping-tax-payers/faqs?start=40", "filename": "kra_kiswahili_ushuru_msaada.txt"},
    {"url": "https://www.hustlerfund.go.ke/sw/personal-loan", "filename": "hustlerfund_kiswahili_mkopo.txt"},
    {"url": "https://www.hustlerfund.go.ke/sw/", "filename": "hustlerfund_kiswahili_biashara.txt"},
    {"url": "https://joon.co.ke/sw/maoni-ya-biashara-ambayo-hayajafungwa/", "filename": "biashara_kenya_kiswahili_maoni.txt"},
    {"url": "https://www.kra.go.ke/sw/individual/filing-paying/types-of-taxes/individual-income-tax", "filename": "kra_sw_kodi_mapato.txt"},
    {"url": "https://www.kra.go.ke/sw/kituo-cha-habari/blog/Kodi-ya-mauzo-ya-1511-iliyoundwa-kufanya-biashara-ndogo-kutii-zaidi", "filename": "kra_sw_tot_biashara_ndogo.txt"},
    {"url": "https://www.kra.go.ke/sw/kituo-cha-habari/vyombo-vya-habari-ya-kutolewa/939-shughuli-za-ushuru,-utiifu-umerahisishwa-kupitia-programu-ya-simu", "filename": "kra_sw_app_huduma.txt"},
    {"url": "https://www.kra.go.ke/sw/kituo-cha-habari/blog/953-kodi-ya-huduma-ya-kidijitali-kiashirio-cha-kubadilisha-michakato-ya-biashara-nchini-kenya", "filename": "kra_sw_dijitali_biashara.txt"},
    {"url": "https://www.kra.go.ke/sw/individual/filing-paying/types-of-taxes/withholding-tax", "filename": "kra_sw_kodi_zuio.txt"},
    {"url": "https://www.kra.go.ke/sw/individual/filing-paying/types-of-taxes/value-added-tax", "filename": "kra_sw_vat_ushuru.txt"},
    {"url": "https://www.kra.go.ke/sw/individual/filing-paying/types-of-taxes/paye", "filename": "kra_sw_paye_mishahara.txt"},
    {"url": "https://www.kra.go.ke/sw/individual/individual-pin-registration/learn-about-pin/about-pin", "filename": "kra_sw_pin_usajili.txt"},
    {"url": "https://www.kra.go.ke/sw/biashara", "filename": "kra_sw_biashara_kukua.txt"},
]

PDF_FILES = [
    {"url": "https://www.lmis.go.ke/downloads/Kenya-Employability-Skills-Report-2023-2024.pdf", "filename": "kenya_employability_skills_2023_2024.pdf"},
    {"url": "https://kenya.un.org/sites/default/files/2024-07/UN-Kenya-Annual-Report-2024.pdf", "filename": "un_kenya_annual_report_2024.pdf"},
    {"url": "https://kenya.un.org/sites/default/files/2024-06/UN-Kenya-MSME-SDGs-2024.pdf", "filename": "un_kenya_msme_sdgs_2024.pdf"},
]

def scrape(url, fn):
    p = DOCS_DIR / fn
    if p.exists(): print(f"  [SKIP] {fn}"); return
    try:
        r = requests.get(url, headers=HEADERS, timeout=30); r.raise_for_status()
        s = BeautifulSoup(r.text, "html.parser")
        [t.decompose() for t in s(["script","style","nav","footer","header","aside"])]
        c = "\n".join([l for l in s.get_text("\n", strip=True).splitlines() if l.strip()])
        p.write_text(f"SOURCE: {url}\nKB: kb7_culture_context\n\n{c}", encoding="utf-8")
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
    print("\nKB7 - Culture & Context")
    [scrape(i["url"], i["filename"]) or time.sleep(1) for i in WEB_PAGES]
    [dl(i["url"], i["filename"]) or time.sleep(2) for i in PDF_FILES]
    print(f"Done. {len(list(DOCS_DIR.glob('*.txt')))} txt, {len(list(DOCS_DIR.glob('*.pdf')))} pdf")
