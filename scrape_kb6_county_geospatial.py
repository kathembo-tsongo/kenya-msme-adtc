import requests, time
from bs4 import BeautifulSoup
from pathlib import Path

DOCS_DIR = Path("documents/kb6_county_geospatial")
DOCS_DIR.mkdir(parents=True, exist_ok=True)
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0.0.0"}

WEB_PAGES = [
    {"url": "https://www.knbs.or.ke/msme-survey-2016/", "filename": "knbs_msme_survey_2016_overview.txt"},
    {"url": "https://opendata.go.ke/county-data/", "filename": "kenya_county_data_portal.txt"},
    {"url": "https://opendata.go.ke/county-economic-profiles/", "filename": "kenya_county_economic_profiles_geospati.txt"},
    {"url": "https://opendata.go.ke/county-market-data/", "filename": "kenya_county_market_data_portal.txt"},
    {"url": "https://www.devolution.go.ke/county-government-structure/", "filename": "kenya_county_government_structure.txt"},
    {"url": "https://www.knbs.or.ke/gross-county-product/", "filename": "kenya_gross_county_product_all47.txt"},
    {"url": "https://www.meru.go.ke/county-economy/", "filename": "kenya_meru_county_economy.txt"},
    {"url": "https://www.mombasa.go.ke/county-economy/", "filename": "kenya_mombasa_county_economy.txt"},
    {"url": "https://nairobi.go.ke/msme-profile/", "filename": "kenya_nairobi_county_msme_profile.txt"},
    {"url": "https://www.nakuru.go.ke/business-environment/", "filename": "kenya_nakuru_county_business.txt"},
    {"url": "https://msme.go.ke/peri-urban-markets/", "filename": "kenya_peri_urban_msme_markets.txt"},
    {"url": "https://www.ndma.go.ke/about/", "filename": "ndma_about_mandate.txt"},
    {"url": "https://www.ndma.go.ke/drought-resilience/", "filename": "ndma_drought_resilience.txt"},
    {"url": "https://www.environment.go.ke/nap-climate-adaptation/", "filename": "kenya_nap_climate_adaptation.txt"},
    {"url": "https://www.tandfonline.com/doi/full/10.1080/23322373.2024.2350861", "filename": "kenya_entrepreneurship_africa_culture_2024.txt"},
    {"url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7216653/", "filename": "kenya_chama_microfinance_health_women.txt"},
    {"url": "https://kippra.or.ke/nurturing-small-businesses-in-the-informal-sector-in-kenya/", "filename": "kenya_ubuntu_entrepreneurship_culture.txt"},
    {"url": "https://hrmars.com/papers_submitted/2013/The_Impact_of_Socio-cultural_Business_Environment_on_Entrepreneurial_Intention_A_Conceptual_Approach.pdf", "filename": "kenya_socio_cultural_business_environment.txt"},
    {"url": "https://statskenya.co.ke/at-stats-kenya/about/gross-county-product-county-gdp/45/", "filename": "kenya_gross_county_product_all47.txt"},
    {"url": "https://icma.org/articles/article/county-government-structure-kenya", "filename": "kenya_county_government_structure.txt"},
    {"url": "https://kenya.opendataforafrica.org/", "filename": "kenya_county_data_portal.txt"},
    {"url": "https://meru.go.ke/", "filename": "kenya_meru_county_economy.txt"},
    {"url": "https://nakuru.go.ke/", "filename": "kenya_nakuru_county_business.txt"},
    {"url": "https://uasingo.go.ke/", "filename": "kenya_eldoret_uasin_gishu_economy.txt"},
    {"url": "https://www.knbs.or.ke/county-statistical-abstracts/", "filename": "knbs_county_statistical_abstracts.txt"},
    {"url": "https://statistics.knbs.or.ke/nada/index.php/catalog/69", "filename": "knbs_msme_survey_2016_overview.txt"},
    {"url": "https://www.knbs.or.ke/publications/", "filename": "knbs_publications_all.txt"},
    {"url": "https://nairobi.go.ke/", "filename": "kenya_nairobi_county_msme_profile.txt"},
    {"url": "https://www.mombasa.go.ke/", "filename": "kenya_mombasa_county_economy.txt"},
    {"url": "http://eservices.kisumu.go.ke/index.php?id=2", "filename": "kenya_kisumu_county_economy.txt"},
    {"url": "https://www.knbs.or.ke/", "filename": "kenya_rural_urban_msme_distribution.txt"},
    {"url": "https://kenya.opendataforafrica.org/data", "filename": "kenya_county_market_data_portal.txt"},
    {"url": "https://msea.go.ke/wp-content/uploads/2023/06/MSME-Policy-2020.pdf", "filename": "kenya_msme_county_business_survey.txt"},
    {"url": "https://kippra.or.ke/characteristics-of-kenyan-msmes-relevant-to-the-proposed-kenya-credit-guarantee-scheme/", "filename": "kenya_peri_urban_msme_markets.txt"},
    {"url": "https://www.vision2030.go.ke/", "filename": "kenya_vision2030_county_development.txt"},
    {"url": "https://www.devolution.go.ke/", "filename": "kenya_devolution_county_economic_profiles.txt"},
]

PDF_FILES = [
    {"url": "https://www.knbs.or.ke/download/2019-kenya-population-and-housing-census-volume-ii/", "filename": "knbs_census_2019_county_population.pdf"},
    {"url": "https://www.knbs.or.ke/download/economic-survey-2024/", "filename": "knbs_facts_figures_2024.pdf"},
    {"url": "https://www.knbs.or.ke/download/kakamega-county-statistical-abstract-2019/", "filename": "knbs_kakamega_county_abstract.pdf"},
    {"url": "https://www.knbs.or.ke/download/kericho-county-statistical-abstract/", "filename": "knbs_kericho_county_abstract.pdf"},
    {"url": "https://www.knbs.or.ke/download/kisumu-county-statistical-abstract/", "filename": "knbs_kisumu_county_abstract.pdf"},
    {"url": "https://www.knbs.or.ke/download/meru-county-statistical-abstract/", "filename": "knbs_meru_county_abstract.pdf"},
    {"url": "https://www.knbs.or.ke/download/2016-micro-small-medium-establishment-survey-report/", "filename": "knbs_msme_survey_2016_report.pdf"},
    {"url": "https://www.knbs.or.ke/download/nakuru-county-statistical-abstract/", "filename": "knbs_nakuru_county_abstract.pdf"},
    {"url": "https://www.knbs.or.ke/download/2023-statistical-abstract/", "filename": "knbs_statistical_abstract_2023.pdf"},
    {"url": "https://www.ndma.go.ke/wp-content/uploads/NDMA-Strategic-Plan-2023-2027.pdf", "filename": "ndma_strategic_plan_2023_2027.pdf"},
    {"url": "https://kenya.un.org/sites/default/files/2021-01/UN-Kenya-COVID19-Impact-MSMEs.pdf", "filename": "un_covid19_impact_msmes_kenya.pdf"},
]

def scrape(url, fn):
    p = DOCS_DIR / fn
    if p.exists(): print(f"  [SKIP] {fn}"); return
    try:
        r = requests.get(url, headers=HEADERS, timeout=30); r.raise_for_status()
        s = BeautifulSoup(r.text, "html.parser")
        [t.decompose() for t in s(["script","style","nav","footer","header","aside"])]
        c = "\n".join([l for l in s.get_text("\n", strip=True).splitlines() if l.strip()])
        p.write_text(f"SOURCE: {url}\nKB: kb6_county_geospatial\n\n{c}", encoding="utf-8")
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
    print("\nKB6 - County & Geospatial")
    [scrape(i["url"], i["filename"]) or time.sleep(1) for i in WEB_PAGES]
    [dl(i["url"], i["filename"]) or time.sleep(2) for i in PDF_FILES]
    print(f"Done. {len(list(DOCS_DIR.glob('*.txt')))} txt, {len(list(DOCS_DIR.glob('*.pdf')))} pdf")
