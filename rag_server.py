"""
rag_server.py — RAG proxy server for the Kenya MSME Advisor.
"""
import pickle
from pathlib import Path

import re
import requests
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from sklearn.metrics.pairwise import cosine_similarity

INDEX_PATH = Path("rag_index.pkl")
LLAMA_SERVER_URL = "http://localhost:8090"
TOP_K = 4
MIN_SIMILARITY = 0.05
PORT = 8091

app = Flask(__name__)
CORS(app)

print("Loading RAG index...")
with open(INDEX_PATH, "rb") as f:
    index = pickle.load(f)
vectorizer = index["vectorizer"]
matrix = index["matrix"]
chunks = index["chunks"]
print(f"Loaded {len(chunks)} chunks from {INDEX_PATH}")

SCOPE_INSTRUCTION = (
    "You are Rafiki wa Biashara, an assistant specifically built to help Kenyan "
    "MSME (micro, small, and medium enterprise) owners with tax, registration, "
    "financing, and regulatory compliance in Kenya.\n\n"
    "SCOPE RULES:\n"
    "1. If the question is clearly about a country OTHER than Kenya (e.g. Ethiopia, "
    "DRC, Tanzania), do not apply Kenyan rules or figures to it — say plainly you're "
    "built specifically for Kenya and don't have reliable information for other "
    "countries.\n"
    "2. If the question is clearly unrelated to business/tax/regulatory topics "
    "entirely (general trivia, opinions, non-business topics), redirect to Kenyan "
    "MSME matters instead of answering from general knowledge.\n"
    "3. For questions ABOUT KENYA and Kenyan MSMEs: answer normally using both the "
    "retrieved source material below (if present and relevant) AND your own trained "
    "knowledge of Kenyan regulations. Do NOT refuse or claim you lack information "
    "just because no source material was retrieved for this specific turn — only "
    "say you lack information if you genuinely don't know the answer, not by default.\n"
    "4. Only use retrieved material when it actually pertains to the question; ignore "
    "it if it doesn't.\n"
    "4b. If retrieved source material contains numbers, rates, or tables that seem "
    "confusing, contradictory, or hard to parse cleanly (common with tables extracted "
    "from PDFs), do NOT guess or combine fragments into a made-up figure. Prefer a "
    "clearly-stated fact from the digest below over an ambiguous number from a messy "
    "retrieved table. If genuinely uncertain, say the exact figure should be confirmed "
    "directly with the relevant agency rather than stating a possibly-wrong number "
    "confidently.\n"
    "4c. Do NOT invent worked examples, sample calculations, or hypothetical figures "
    "(e.g. \'a business earning X would pay Y\') unless the user explicitly asks for "
    "a calculation with specific numbers. State the fact/rate itself clearly and stop "
    "-- do not add fabricated arithmetic to illustrate it.\n"
    "4d. Do NOT invent specific phone numbers, USSD menu sequences/sub-codes, email "
    "addresses, reference numbers, or step-by-step menu prompts beyond what is "
    "explicitly given to you in the verified facts or retrieved material. If you know "
    "a general contact method (e.g. \'dial *254#\' or \'visit itax.kra.go.ke\') but "
    "not the specific sub-menu steps or an exact phone number, state only the general "
    "method you actually know and stop there -- do not add plausible-sounding specific "
    "digits or menu options you are not certain of.\n"
    "4e. Do NOT invent specific website URLs beyond well-known official domains you are "
    "certain of (e.g. itax.kra.go.ke, ecitizen.go.ke, youthfund.go.ke, brs.go.ke). Never "
    "add extra path segments or subpages you are not certain exist (e.g. do not write "
    "\'brs.go.ke/some-specific-subpage\' unless that exact path was given to you).\n"
    "4f. STRICT RULE ON CLASSIFICATIONS AND THRESHOLDS: never state a specific numeric "
    "business-size classification, category name, floor-area figure, or employee-count "
    "band (e.g. \'Medium Retailer\', \'35 square meters\', \'5-20 employees\') unless "
    "that EXACT figure or category name is explicitly present, word-for-word, in the "
    "verified facts digest above or the retrieved source material for THIS turn. If no "
    "such exact figure is present, do not classify the business by size at all -- "
    "simply describe the general licensing/registration process without inventing a "
    "category. It is always better to omit a classification than to state one you "
    "cannot point to in the given material.\n"
    "5. IMPORTANT -- this assistant exists specifically to save MSME owners the time and "
    "cost of visiting government offices or paying for consultancy just to get basic "
    "procedural information. When the retrieved source material contains concrete, "
    "actionable details -- application forms, product names, phone numbers, USSD codes, "
    "website URLs, step-by-step processes, specific offices/departments -- state them "
    "DIRECTLY and CONFIDENTLY as the main answer. Do NOT bury real, available steps "
    "under hedging language, and do NOT tell the user to \'contact\' or \'visit\' an "
    "office for information that is already in the retrieved material -- give them that "
    "information now. Only recommend contacting an office/agency when the retrieved "
    "material genuinely does not contain the specific answer needed.\n"
    "6. If the user writes in Kiswahili, respond fluently and naturally in Kiswahili, "
    "using correct Kenyan business/regulatory terminology (e.g. Mamlaka ya Mapato "
    "Kenya (KRA), Usajili wa Biashara, Kodi ya Ongezeko la Thamani (VAT)). If the "
    "user mixes Kiswahili and English (Sheng-style), respond in the same natural "
    "mixed style rather than switching entirely to one language.\n\n"
    "VERIFIED PROCEDURAL FACTS (state these directly and confidently when relevant):\n"
    "- Startup loans in Kenya: (1) YEDF -- apply via youthfund.go.ke, products include "
    "Vuka, Talanta, Agribizz, Vijana Bahari, LPO financing; requires Form 1A with "
    "county/constituency details; (2) Hustler Fund -- apply via USSD *254# or the "
    "Hustler Fund app, no collateral required, builds toward higher loan tiers through "
    "savings; (3) SACCOs -- require membership and savings history first; "
    "(4) commercial banks -- require a registered business, financial records, and "
    "collateral for larger amounts.\n"
    "- Business name registration: apply via the eCitizen portal (ecitizen.go.ke) or "
    "the Business Registration Service (brs.go.ke); search for name availability "
    "first, then submit registration with your ID/KRA PIN.\n"
    "- KRA PIN registration: apply free via iTax (itax.kra.go.ke) using your national "
    "ID; required before registering for VAT, PAYE, or any other tax obligation.\n"
    "- VAT registration: mandatory once annual taxable turnover exceeds KES 5,000,000; "
    "register via iTax.\n"
    "- Terminating an employee in Kenya: governed by the Employment Act 2007. You must "
    "have a valid, fair reason (e.g. misconduct, poor performance, redundancy) and "
    "follow due process -- give the employee notice (per their contract, or the "
    "statutory minimum), explain the reason in writing, and give them a genuine chance "
    "to respond/be heard before the decision is finalized. Skipping notice or the "
    "hearing step, even with a valid reason, can make a dismissal unfair/unlawful. "
    "For redundancy specifically, additional rules apply (e.g. notifying the labour "
    "office, selection criteria, severance pay). Recommend consulting the exact notice "
    "period in their contract or the Employment Act itself for precise timelines.\n"
    "- Business/trade licenses in Kenya: administered at the COUNTY level (not "
    "nationally), so exact categories, fees, and thresholds vary by county -- do not "
    "state a specific size classification (e.g. square meters, employee-count bands) "
    "as if it is a fixed national standard, because it is not. The general process is: "
    "register your business name first (eCitizen/BRS), then apply for a single business "
    "permit through your specific county government's business licensing office (e.g. "
    "Nairobi City County has its own portal/office). Advise the user to confirm exact "
    "category and fee with their specific county, since it genuinely varies.\n\n"
    "FORMATTING RULES:\n"
    "- Use **bold** for key terms, amounts, deadlines, and agency names.\n"
    "- Use bullet points or numbered lists whenever an answer has 2 or more distinct "
    "items, steps, or requirements — never bury multiple items in a single paragraph.\n"
    "- Use short section headers (as plain bold text, not markdown #) to break up "
    "longer answers into logical groups (e.g. **Registration**, **Tax Obligations**, "
    "**Next Steps**).\n"
    "- Keep genuinely simple, single-point answers as plain sentences — do not force "
    "structure onto a one-line answer.\n"
    "- Never write a long unbroken paragraph when the content has a natural list or "
    "step-by-step shape."
)



SWAHILI_TO_ENGLISH = {
    "biashara": "business",
    "kodi": "tax",
    "usajili": "registration",
    "leseni": "license permit",
    "mfanyakazi": "employee",
    "wafanyakazi": "employees",
    "mshahara": "salary wage",
    "malipo": "payment",
    "faida": "profit",
    "mtaji": "capital",
    "mkopo": "loan credit",
    "fedha": "finance money",
    "kampuni": "company",
    "duka": "shop retail",
    "ushuru": "duty tax",
    "hifadhi ya jamii": "social security NSSF",
    "bima": "insurance",
    "kanuni": "regulation",
    "sheria": "law",
    "kaunti": "county",
    "ajira": "employment",
    "pensheni": "pension",
    "riba": "interest rate",
    "akaunti": "account",
    "mizani": "balance",
    "mauzo": "sales revenue",
    "gharama": "cost expense",
}

def expand_swahili_terms(query: str) -> str:
    """Append English equivalents of recognized Swahili business terms
    to improve retrieval against the English-only source corpus."""
    query_lower = query.lower()
    additions = []
    for sw_term, en_term in SWAHILI_TO_ENGLISH.items():
        if sw_term in query_lower:
            additions.append(en_term)
    if additions:
        return query + " " + " ".join(additions)
    return query


DIGEST_OVERRIDE_KEYWORDS = [
    "nssf", "national social security fund", "shif", "social health insurance", "nhif",
    "annual leave", "leave entitlement", "leave days", "maternity leave", "minimum wage",
    "minimum share capital", "share capital requirement",
    "yedf", "youth enterprise development fund", "rausha", "inua loan", "vuka loan",
    "apply for a loan", "apply for financing", "get a loan", "startup loan",
    "hustler fund", "how can i apply for a loan", "loan to start", "women enterprise fund",
    "register a business name", "business name registration", "kra pin", "vat registration",
    "vat threshold", "terminate an employee", "termination", "dismissal", "dismiss an employee",
    "redundancy", "fire an employee", "firing an employee",
    "license", "licence", "business permit", "trade license", "single business permit",
]


CANNED_ANSWERS = {
    "nssf": (
        "**NSSF contributions** are split evenly:\n\n"
        "- **Employee**: 6% of pensionable pay\n"
        "- **Employer**: 6% (matched)\n\n"
        "This applies to Tier I (up to KES 9,000 of pensionable pay) and Tier II "
        "(the portion up to KES 108,000). Contributions are remitted monthly."
    ),
    "leave": (
        "**Statutory annual leave in Kenya** (Employment Act 2007):\n\n"
        "- Minimum **21 working days** of paid leave per 12 months of continuous service\n"
        "- Accrues over the year; some employers allow limited carry-forward\n\n"
        "Check your specific employment contract for any additional leave beyond the statutory minimum."
    ),
    "capital": (
        "**Minimum share capital for a private limited company in Kenya**:\n\n"
        "- There is **no legally mandated minimum** share capital requirement\n"
        "- Most companies register with a nominal capital (commonly KES 100,000, though this is a convention, not a legal floor)\n"
        "- Stamp duty is charged at **1% of nominal share capital**"
    ),
    "yedf": (
        "**Youth Enterprise Development Fund (YEDF)**:\n\n"
        "- **Eligibility**: age 18-34\n"
        "- **Rausha loan**: KES 100,000 (group startup funding)\n"
        "- **Inua loan**: KES 200,000-1,000,000 (business expansion)\n"
        "- **Vuka loan**: up to KES 5,000,000 at 8% p.a.\n\n"
        "Apply via youthfund.go.ke, Form 1A, with your county/constituency details."
    ),
    "loan": (
        "**Startup loan options in Kenya**:\n\n"
        "1. **YEDF** -- apply via youthfund.go.ke (Form 1A); products include Vuka, Talanta, Agribizz, Vijana Bahari, and LPO financing\n"
        "2. **Hustler Fund** -- apply via USSD *254# or the Hustler Fund app; no collateral required, builds toward higher loan tiers through savings\n"
        "3. **SACCOs** -- require membership and a savings history first\n"
        "4. **Commercial banks** -- require a registered business, financial records, and collateral for larger amounts"
    ),
    "registration": (
        "**Registering a business name in Kenya**:\n\n"
        "1. Search for name availability via the eCitizen portal (ecitizen.go.ke) or the Business Registration Service (brs.go.ke)\n"
        "2. Submit your registration with your national ID and KRA PIN\n"
        "3. Once approved, you'll receive a business registration certificate"
    ),
    "kra_pin": (
        "**Getting a KRA PIN**:\n\n"
        "1. Go to iTax at itax.kra.go.ke\n"
        "2. Log in / register using your national ID\n"
        "3. Click \"Register\" -- your PIN is issued once you complete registration\n\n"
        "You'll need this PIN before registering for VAT, PAYE, or any other tax obligation."
    ),
    "vat": (
        "**VAT registration threshold in Kenya**:\n\n"
        "- Mandatory once your annual taxable turnover exceeds **KES 5,000,000**\n"
        "- Register via iTax (itax.kra.go.ke)"
    ),
    "termination": (
        "**Terminating an employee legally in Kenya** (Employment Act 2007):\n\n"
        "1. Have a **valid, fair reason** (e.g. misconduct, poor performance, redundancy)\n"
        "2. Give proper **notice** (per contract, or the statutory minimum)\n"
        "3. Explain the reason in writing and give the employee a genuine chance to respond/be heard before the decision is final\n\n"
        "Skipping notice or the hearing step -- even with a valid reason -- can make a dismissal unfair. Redundancy has additional rules (labour office notification, selection criteria, severance pay)."
    ),
    "license": (
        "**Business/trade licenses in Kenya** are administered at the **county level**, not nationally -- exact categories and fees vary by county.\n\n"
        "General process:\n"
        "1. Register your business name first (eCitizen/BRS)\n"
        "2. Apply for a single business permit through your specific county government's business licensing office\n\n"
        "Confirm the exact category and fee with your specific county, since it genuinely varies."
    ),
    "turnover_tax": (
        "**Turnover Tax (TOT)** applies to resident persons and corporates in "
        "Kenya whose gross turnover is **more than KES 1,000,000** but **does "
        "not exceed KES 25,000,000** in a year of income. It is chargeable "
        "under Section 12(C) of the Income Tax Act (CAP 470).\n\n"
        "- **Rate:** 1.5% on gross sales, effective 1st July 2023 per the "
        "Finance Act 2023\n"
        "- **Final tax:** TOT is charged on gross sales with **no expense "
        "deductions allowed**\n"
        "- **Below KES 1,000,000:** exempt from TOT (but other tax "
        "obligations may still apply)\n"
        "- **Above KES 25,000,000:** must register for the regular Income "
        "Tax regime instead\n"
        "- **Not applicable to:** rental income, management/professional/"
        "training fees, income already subject to final withholding tax "
        "(e.g. qualifying dividends or interest), and non-resident "
        "taxpayers\n"
        "- If your turnover reaches **KES 5,000,000** and you deal in "
        "vatable supplies, you must also register for VAT\n"
        "- You may elect, by written notice to the Commissioner, to opt "
        "out of TOT and remain under the regular Income Tax regime "
        "instead\n\n"
        "Confirm your specific position via iTax (itax.kra.go.ke), since "
        "individual circumstances can affect eligibility."
    ),
    "paye_bands": (
        "**PAYE tax bands in Kenya** are progressive, applied monthly "
        "(Finance Act 2023):\n\n"
        "- **10%** on the first KES 24,000\n"
        "- **25%** on the next KES 8,333 (KES 24,001-32,333)\n"
        "- **30%** on KES 32,334-500,000\n"
        "- **32.5%** on KES 500,001-800,000\n"
        "- **35%** above KES 800,000\n\n"
        "Every resident employee is entitled to a **personal relief of "
        "KES 2,400 per month** (KES 28,800 per year), subtracted from the "
        "calculated tax. Non-residents do not qualify for this relief. "
        "PAYE is calculated on taxable income after NSSF, SHIF, and "
        "Affordable Housing Levy deductions.\n\n"
        "**Remittance deadline**: PAYE deducted from a given month's "
        "salaries must be remitted to KRA by the **9th day of the "
        "following month** (e.g. January's PAYE is due by 9th "
        "February), filed via the iTax P10 return. Late remittance "
        "carries a **25% penalty** on the tax due, plus **2% monthly "
        "interest** on the unpaid amount."
    ),
    "shif_rate": (
        "**SHIF (Social Health Insurance Fund)** contributions are charged "
        "at **2.75% of gross income**, with **no upper cap** -- higher "
        "earners pay proportionally more. SHIF replaced the old NHIF "
        "flat-rate system from October 2024. Unlike NSSF, SHIF is not "
        "split into tiers with a separate employer-matched portion in the "
        "same way -- confirm the exact current employer/employee split "
        "directly via the SHA (Social Health Authority) or your payroll "
        "provider, since specifics can be updated."
    ),
    "housing_levy": (
        "**Affordable Housing Levy (AHL)** in Kenya:\n\n"
        "- **1.5%** of gross salary from the employee\n"
        "- **1.5%** of gross salary matched by the employer\n"
        "- **Total: 3%** of gross salary per employee, per month\n\n"
        "There is **no minimum income threshold** -- it applies to all "
        "gross salaried employees. Informal-sector and self-employed "
        "contributors pay 1.5% of declared income with no employer match, "
        "registering via the AHL/Boma Yangu portal. Remittance is due by "
        "the 9th working day after month-end via KRA iTax. Resident "
        "individuals who pay AHL are entitled to affordable housing "
        "relief. Late remittance carries a 3% per month penalty on the "
        "unpaid amount."
    ),
    "minimum_wage": (
        "**Kenya does not have a single national minimum wage.** Rates "
        "are set by occupation, sector, and geographic zone under "
        "periodic Regulation of Wages Orders (Labour Institutions Act), "
        "typically revised around Labour Day (1st May).\n\n"
        "As a reference point: the general (unskilled) labourer minimum "
        "in Nairobi, Mombasa, Kisumu, Nakuru, and Eldoret was set at "
        "**KES 18,047.40 per month** under the May 2026 Wage Order "
        "(Legal Notices No. 95 and 96), with lower rates in other zones. "
        "Skilled occupations (e.g. drivers, artisans, cashiers) and "
        "sector-specific roles (agricultural, security, domestic work) "
        "have their own, generally higher, statutory minimums.\n\n"
        "Because rates vary by role and location and are revised "
        "periodically, confirm the exact current figure for your "
        "specific occupation and zone via the Ministry of Labour and "
        "Social Protection or the current Kenya Gazette Wage Order, "
        "rather than relying on a single number."
    ),
    "nssf_penalty": (
        "**NSSF late payment penalty in Kenya**: a penalty of **5% of the "
        "outstanding contribution** is charged for each month, or part of "
        "a month, that remittance remains late. Some sources also note "
        "additional monthly interest on top of this base penalty -- "
        "confirm the full current figure directly with NSSF, since this "
        "detail varies across sources. Persistent non-compliance can lead "
        "to legal action, and company directors can be held personally "
        "liable for unpaid contributions."
    ),
    "mpesa_paybill_till": (
        "**Getting an M-Pesa Paybill or Till number** -- apply through "
        "**Safaricom**, not a bank:\n\n"
        "- **Till Number**: for retail/point-of-sale (shops, restaurants, "
        "kiosks) -- one till per outlet, customer pays no fee, merchant "
        "pays a small settlement fee (roughly 0.5-1%)\n"
        "- **Paybill Number**: for recurring collections with an account/"
        "reference number (rent, school fees, utilities, subscriptions)\n\n"
        "**How to apply**: visit m-pesaforbusiness.co.ke and click "
        "'Apply Now', or visit any Safaricom shop. You'll need your "
        "national ID, KRA PIN, business registration documents (type "
        "depends on whether you're a sole proprietor, partnership, or "
        "company), and bank account details for settlement. Application "
        "is **free**. Once approved, you'll receive your number by SMS "
        "and activate it by dialing *234# on the registered line."
    ),
}


CANNED_ANSWERS_SW = {
    "nssf": (
        "**Michango ya NSSF** imegawanywa sawa kati ya pande mbili:\n\n"
        "- **Mfanyakazi**: 6% ya mshahara unaostahili\n"
        "- **Mwajiri**: 6% (kiasi sawa)\n\n"
        "Hii inatumika kwa Tier I (hadi KES 9,000 ya mshahara unaostahili) na Tier II "
        "(sehemu hadi KES 108,000). Michango hulipwa kila mwezi."
    ),
    "leave": (
        "**Likizo ya kila mwaka kisheria nchini Kenya** (Sheria ya Ajira 2007):\n\n"
        "- Angalau **siku 21 za kazi** za likizo yenye malipo kwa kila miezi 12 ya "
        "utumishi endelevu\n"
        "- Hukusanywa mwaka mzima; baadhi ya waajiri huruhusu kuhamisha siku chache "
        "zilizobaki kwenda mwaka unaofuata\n\n"
        "Angalia mkataba wako wa ajira kwa likizo yoyote ya ziada zaidi ya kiwango "
        "cha chini kisheria."
    ),
    "capital": (
        "**Mtaji wa chini wa hisa kwa kampuni binafsi ya dhima ndogo nchini Kenya**:\n\n"
        "- **Hakuna** mtaji wa chini wa hisa unaotakiwa kisheria\n"
        "- Kampuni nyingi husajiliwa na mtaji wa kawaida (mara nyingi KES 100,000, "
        "ingawa hii ni desturi tu, si kiwango cha kisheria)\n"
        "- Ushuru wa stempu hutozwa kwa **1% ya mtaji wa hisa wa kawaida**"
    ),
    "yedf": (
        "**Mfuko wa Maendeleo ya Wafanyabiashara Vijana (YEDF)**:\n\n"
        "- **Sifa**: umri wa miaka 18-34\n"
        "- **Mkopo wa Rausha**: KES 100,000 (ufadhili wa kuanzisha kikundi)\n"
        "- **Mkopo wa Inua**: KES 200,000-1,000,000 (upanuzi wa biashara)\n"
        "- **Mkopo wa Vuka**: hadi KES 5,000,000 kwa asilimia 8 kwa mwaka\n\n"
        "Omba kupitia youthfund.go.ke, Fomu 1A, ukiwa na maelezo ya kaunti/jimbo lako."
    ),
    "loan": (
        "**Chaguo za mikopo ya kuanzisha biashara nchini Kenya**:\n\n"
        "1. **YEDF** -- omba kupitia youthfund.go.ke (Fomu 1A); bidhaa ni pamoja na "
        "Vuka, Talanta, Agribizz, Vijana Bahari, na ufadhili wa LPO\n"
        "2. **Hustler Fund** -- omba kupitia USSD *254# au programu ya Hustler Fund; "
        "hakuna dhamana inayohitajika, hujenga kiwango cha juu cha mikopo kupitia akiba\n"
        "3. **SACCOs** -- zinahitaji uanachama na historia ya akiba kwanza\n"
        "4. **Benki za kibiashara** -- zinahitaji biashara iliyosajiliwa, kumbukumbu "
        "za kifedha, na dhamana kwa kiasi kikubwa zaidi"
    ),
    "registration": (
        "**Kusajili jina la biashara nchini Kenya**:\n\n"
        "1. Tafuta upatikanaji wa jina kupitia tovuti ya eCitizen (ecitizen.go.ke) "
        "au Huduma ya Usajili wa Biashara (brs.go.ke)\n"
        "2. Wasilisha usajili wako ukiwa na kitambulisho chako cha taifa na namba "
        "ya PIN ya KRA\n"
        "3. Baada ya kuidhinishwa, utapokea cheti cha usajili wa biashara"
    ),
    "kra_pin": (
        "**Kupata namba ya PIN ya KRA**:\n\n"
        "1. Nenda iTax kwenye itax.kra.go.ke\n"
        "2. Ingia / jisajili kwa kutumia kitambulisho chako cha taifa\n"
        "3. Bofya \"Register\" -- PIN yako hutolewa mara tu unapomaliza usajili\n\n"
        "Utahitaji PIN hii kabla ya kusajili kwa VAT, PAYE, au wajibu mwingine "
        "wowote wa kodi."
    ),
    "vat": (
        "**Kiwango cha lazima cha kusajili VAT nchini Kenya**:\n\n"
        "- Ni lazima pindi mauzo yako ya mwaka yanayotozwa kodi yanapozidi "
        "**KES 5,000,000**\n"
        "- Jisajili kupitia iTax (itax.kra.go.ke)"
    ),
    "termination": (
        "**Kumfukuza mfanyakazi kihalali nchini Kenya** (Sheria ya Ajira 2007):\n\n"
        "1. Kuwa na **sababu halali na ya haki** (mfano, utovu wa nidhamu, "
        "utendaji duni, kupunguzwa kwa wafanyakazi)\n"
        "2. Toa **taarifa** ifaayo (kulingana na mkataba, au kiwango cha chini "
        "kisheria)\n"
        "3. Eleza sababu kwa maandishi na mpe mfanyakazi nafasi halisi ya "
        "kujibu/kusikilizwa kabla uamuzi haujawa wa mwisho\n\n"
        "Kuruka hatua ya taarifa au usikilizaji -- hata kwa sababu halali -- "
        "kunaweza kufanya ufukuzaji kuwa si wa haki. Kupunguzwa kwa wafanyakazi "
        "kuna sheria za ziada (taarifa kwa ofisi ya kazi, vigezo vya uchaguzi, "
        "malipo ya kiinua mgongo)."
    ),
    "license": (
        "**Leseni za biashara/kibiashara nchini Kenya** zinasimamiwa katika "
        "**ngazi ya kaunti**, si kitaifa -- aina na ada halisi hutofautiana kwa "
        "kaunti.\n\n"
        "Mchakato wa jumla:\n"
        "1. Sajili jina la biashara yako kwanza (eCitizen/BRS)\n"
        "2. Omba kibali kimoja cha biashara kupitia ofisi ya leseni za biashara "
        "ya kaunti yako mahususi\n\n"
        "Thibitisha aina na ada halisi na kaunti yako mahususi, kwa kuwa "
        "hutofautiana kikweli."
    ),
    "turnover_tax": (
        "**Kodi ya Mauzo (Turnover Tax - TOT)** inahusu watu na makampuni "
        "yanayoishi nchini Kenya ambao mauzo yao ya jumla ni **zaidi ya "
        "KES 1,000,000** lakini **hayazidi KES 25,000,000** katika mwaka wa "
        "mapato. Inatozwa chini ya Kifungu cha 12(C) cha Sheria ya Kodi ya "
        "Mapato (CAP 470).\n\n"
        "- **Kiwango**: 1.5% ya mauzo ya jumla, kuanzia tarehe 1 Julai 2023 "
        "kulingana na Sheria ya Fedha 2023\n"
        "- **Kodi ya mwisho**: TOT hutozwa kwa mauzo ya jumla bila **makato "
        "yoyote ya gharama kuruhusiwa**\n"
        "- **Chini ya KES 1,000,000**: hakuna TOT (lakini wajibu mwingine wa "
        "kodi unaweza kuendelea kutumika)\n"
        "- **Zaidi ya KES 25,000,000**: lazima ujisajili kwa mfumo wa kawaida "
        "wa Kodi ya Mapato badala yake\n"
        "- **Haitumiki kwa**: mapato ya kupanga nyumba, ada za "
        "usimamizi/kitaalamu/mafunzo, mapato yanayotozwa tayari kodi ya mwisho "
        "ya makato (mfano, gawio linalostahili au riba), na walipa kodi wasio "
        "wakazi\n"
        "- Ikiwa mauzo yako yanafikia **KES 5,000,000** na unashughulika na "
        "bidhaa zinazotozwa VAT, lazima pia ujisajili kwa VAT\n"
        "- Unaweza kuchagua, kwa taarifa iliyoandikwa kwa Kamishna, "
        "kutojumuishwa katika TOT na kubaki chini ya mfumo wa kawaida wa Kodi "
        "ya Mapato badala yake\n\n"
        "Thibitisha msimamo wako mahususi kupitia iTax (itax.kra.go.ke), kwa "
        "kuwa hali za kibinafsi zinaweza kuathiri ustahiki."
    ),
    "paye_bands": (
        "**Viwango vya kodi ya PAYE nchini Kenya** hupanda kwa hatua, "
        "hutumika kila mwezi (Sheria ya Fedha 2023):\n\n"
        "- **10%** kwa KES 24,000 za kwanza\n"
        "- **25%** kwa KES 8,333 zinazofuata (KES 24,001-32,333)\n"
        "- **30%** kwa KES 32,334-500,000\n"
        "- **32.5%** kwa KES 500,001-800,000\n"
        "- **35%** zaidi ya KES 800,000\n\n"
        "Kila mfanyakazi mkazi anastahili **msamaha binafsi wa KES 2,400 "
        "kwa mwezi** (KES 28,800 kwa mwaka), unaotolewa kutoka kodi "
        "iliyokokotolewa. Wasio wakazi hawastahili msamaha huu. PAYE "
        "hukokotolewa kwa mapato yanayotozwa kodi baada ya makato ya "
        "NSSF, SHIF, na Ushuru wa Nyumba za Bei Nafuu.\n\n"
        "**Tarehe ya mwisho ya kuwasilisha**: PAYE iliyokatwa kwa "
        "mshahara wa mwezi fulani lazima iwasilishwe KRA ifikapo "
        "**tarehe 9 ya mwezi unaofuata** (mfano, PAYE ya Januari "
        "inatakiwa ifikapo tarehe 9 Februari), ikiwasilishwa kupitia "
        "fomu ya P10 kwenye iTax. Kuchelewesha malipo kunatoza **faini "
        "ya 25%** ya kodi inayodaiwa, pamoja na **riba ya 2% kwa "
        "mwezi** ya kiasi kisicholipwa."
    ),
    "shif_rate": (
        "**Mchango wa SHIF (Social Health Insurance Fund)** hutozwa kwa "
        "**2.75% ya mapato ya jumla**, **bila kiwango cha juu** -- "
        "wanaopata zaidi hulipa zaidi kwa uwiano. SHIF ilichukua nafasi "
        "ya mfumo wa zamani wa NHIF wenye kiwango cha kudumu tangu "
        "Oktoba 2024. Tofauti na NSSF, SHIF haigawanywi katika hatua "
        "zenye sehemu ya mwajiri inayolingana kwa njia hiyo hiyo -- "
        "thibitisha mgawanyo halisi wa sasa wa mwajiri/mfanyakazi moja "
        "kwa moja kupitia SHA (Social Health Authority) au mtoa huduma "
        "wako wa malipo, kwa kuwa maelezo yanaweza kubadilishwa."
    ),
    "housing_levy": (
        "**Ushuru wa Nyumba za Bei Nafuu (AHL)** nchini Kenya:\n\n"
        "- **1.5%** ya mshahara wa jumla kutoka kwa mfanyakazi\n"
        "- **1.5%** ya mshahara wa jumla inayolingana kutoka kwa mwajiri\n"
        "- **Jumla: 3%** ya mshahara wa jumla kwa kila mfanyakazi, kila "
        "mwezi\n\n"
        "**Hakuna kiwango cha chini cha mapato** kinachotakiwa -- "
        "hutumika kwa wafanyakazi wote wenye mshahara wa jumla. "
        "Wachangiaji wa sekta isiyo rasmi na wanaojiajiri hulipa 1.5% ya "
        "mapato yaliyotangazwa bila mchango wa mwajiri, wakijisajili "
        "kupitia tovuti ya AHL/Boma Yangu. Malipo yanatakiwa kufikishwa "
        "ndani ya siku 9 za kazi baada ya mwisho wa mwezi kupitia iTax "
        "ya KRA. Watu wakazi wanaolipa AHL wanastahili msamaha wa nyumba "
        "za bei nafuu. Kuchelewesha malipo kunatoza faini ya 3% kwa "
        "mwezi ya kiasi kisicholipwa."
    ),
    "minimum_wage": (
        "**Kenya haina mshahara mmoja wa chini wa kitaifa.** Viwango "
        "huwekwa kulingana na kazi, sekta, na eneo la kijiografia chini "
        "ya Amri za Kanuni za Mishahara zinazotolewa mara kwa mara "
        "(Sheria ya Taasisi za Kazi), kwa kawaida hurekebishwa karibu na "
        "Siku ya Wafanyakazi (Mei 1).\n\n"
        "Kama kumbukumbu: mshahara wa chini wa kibarua wa kawaida "
        "(asiye na ujuzi maalum) Nairobi, Mombasa, Kisumu, Nakuru, na "
        "Eldoret uliwekwa kuwa **KES 18,047.40 kwa mwezi** chini ya Amri "
        "ya Mishahara ya Mei 2026, ukiwa na viwango vya chini zaidi "
        "katika maeneo mengine. Kazi zenye ujuzi (mfano, madereva, "
        "mafundi, wafanyakazi wa fedha) na kazi za sekta mahususi "
        "(kilimo, ulinzi, kazi za nyumbani) zina viwango vyao vya "
        "kisheria, kwa kawaida vya juu zaidi.\n\n"
        "Kwa kuwa viwango hutofautiana kulingana na kazi na eneo na "
        "hurekebishwa mara kwa mara, thibitisha kiwango halisi cha sasa "
        "kwa kazi yako mahususi na eneo lako kupitia Wizara ya Kazi na "
        "Ulinzi wa Jamii au Amri ya Mishahara ya sasa ya Kenya Gazette, "
        "badala ya kutegemea nambari moja."
    ),
    "nssf_penalty": (
        "**Adhabu ya kuchelewesha malipo ya NSSF nchini Kenya**: faini ya "
        "**5% ya mchango usiolipwa** hutozwa kwa kila mwezi, au sehemu ya "
        "mwezi, ambao malipo yanabaki kuchelewa. Baadhi ya vyanzo pia "
        "hutaja riba ya ziada ya kila mwezi juu ya faini hii ya msingi -- "
        "thibitisha kiwango kamili cha sasa moja kwa moja na NSSF, kwa "
        "kuwa maelezo haya hutofautiana kati ya vyanzo. Kutozingatia kwa "
        "kudumu kunaweza kusababisha hatua za kisheria, na wakurugenzi wa "
        "kampuni wanaweza kuwajibika binafsi kwa michango isiyolipwa."
    ),
    "mpesa_paybill_till": (
        "**Kupata namba ya Paybill au Till ya M-Pesa** -- omba kupitia "
        "**Safaricom**, si benki:\n\n"
        "- **Namba ya Till**: kwa biashara za rejareja (maduka, "
        "mikahawa, vibanda) -- till moja kwa kila tawi, mteja halipi "
        "ada, mfanyabiashara hulipa ada ndogo ya malipo (karibu 0.5-1%)\n"
        "- **Namba ya Paybill**: kwa malipo yanayojirudia yenye namba ya "
        "akaunti/kumbukumbu (kodi, karo za shule, huduma, michango)\n\n"
        "**Jinsi ya kuomba**: tembelea m-pesaforbusiness.co.ke na bofya "
        "'Apply Now', au tembelea duka lolote la Safaricom. Utahitaji "
        "kitambulisho chako cha taifa, namba ya PIN ya KRA, hati za "
        "usajili wa biashara (aina inategemea kama wewe ni mmiliki "
        "binafsi, ubia, au kampuni), na maelezo ya akaunti ya benki kwa "
        "malipo. Kuomba ni **bure**. Baada ya kuidhinishwa, utapokea "
        "namba yako kwa SMS na kuiwezesha kwa kupiga *234# kwenye laini "
        "iliyosajiliwa."
    ),
}


TOPIC_KEYWORDS = {
    "nssf_penalty": ["nssf penalty", "late nssf", "nssf late payment", "penalty for late nssf", "nssf fine"],
    "mpesa_paybill_till": ["paybill", "till number", "buy goods till", "set up paybill", "mpesa business"],
    "nssf": ["nssf", "national social security fund"],
    "leave": ["annual leave", "leave entitlement", "leave days"],
    "capital": ["minimum share capital", "share capital requirement"],
    "yedf": ["yedf", "youth enterprise development fund", "rausha", "inua loan", "vuka loan"],
    "loan": ["apply for a loan", "apply for financing", "get a loan", "startup loan", "hustler fund", "loan to start"],
    "kra_pin": ["kra pin"],
    "vat": ["vat registration", "vat threshold"],
    "termination": ["terminate an employee", "termination", "dismissal", "dismiss an employee", "redundancy", "fire an employee", "firing an employee"],
    "license": ["single business permit", "what license do i need", "what licence do i need", "trade license requirements"],
    "turnover_tax": ["turnover tax", "tot rate", "tot threshold"],
    "paye_bands": ["paye rate", "paye band", "paye tax rate", "income tax band", "income tax rate"],
    "shif_rate": ["shif rate", "shif contribution", "shif percentage", "how much shif", "shif deduction", "contribute to shif", "employer shif", "shif employer", "pay to shif", "shif pay", "obligations to shif", "shif obligations", "obligations under shif"],
    "housing_levy": ["housing levy", "affordable housing levy", "ahl rate", "housing levy rate"],
    "minimum_wage": ["minimum wage", "minimum salary", "lowest wage", "minimum pay"],
    "registration": ["register a business name", "business name registration", "steps to register a business", "register a small business", "register a business in kenya", "how to register a business", "start a business in kenya", "steps to start a business"],
}


def get_canned_topic(query: str):
    """Return the topic key if the query matches a hard-verified topic with
    a canned answer, else None. Bypasses LLM generation entirely for these
    topics to guarantee zero fabrication."""
    query_lower = query.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in query_lower for kw in keywords):
            return topic
    return None


def matches_digest_topic(query: str) -> bool:
    """Check if a query is about a topic we've already hard-verified in the
    fact digest -- for these, skip retrieval entirely rather than risk a
    messy PDF table confusing the model into inventing wrong numbers."""
    query_lower = query.lower()
    return any(kw in query_lower for kw in DIGEST_OVERRIDE_KEYWORDS)


def retrieve(query: str, top_k: int = TOP_K):
    query_vec = vectorizer.transform([query])
    sims = cosine_similarity(query_vec, matrix).flatten()
    top_indices = sims.argsort()[::-1][:top_k]

    results = []
    for idx in top_indices:
        score = float(sims[idx])
        if score < MIN_SIMILARITY:
            continue
        results.append({
            "text": chunks[idx]["text"],
            "kb": chunks[idx]["kb"],
            "source": chunks[idx]["source"],
            "score": score,
        })
    return results


def build_retrieval_query(messages, current_query):
    """Combine the current question with the prior user turn ONLY when the
    current question is short/vague (e.g. 'what about Kenya?') and would
    otherwise retrieve poorly on its own. A well-formed, specific question
    should be searched as-is -- blending in an unrelated prior topic dilutes
    the query and weakens retrieval precision."""
    VAGUE_WORD_THRESHOLD = 6
    if len(current_query.split()) > VAGUE_WORD_THRESHOLD:
        return current_query

    user_turns = [m["content"] for m in messages if m.get("role") == "user"]
    if len(user_turns) >= 2:
        return user_turns[-2] + " " + current_query
    return current_query


MAX_CHUNK_CHARS = 700  # ~175-200 tokens per chunk; keeps 4 chunks well under the 2048 context window


def build_context_block(retrieved):
    parts = [SCOPE_INSTRUCTION]
    if retrieved:
        parts.append("\n\nRELEVANT SOURCE MATERIAL (use if it genuinely pertains to the question):\n")
        for i, r in enumerate(retrieved, 1):
            text = r["text"]
            if len(text) > MAX_CHUNK_CHARS:
                text = text[:MAX_CHUNK_CHARS].rsplit(" ", 1)[0] + "..."
            parts.append(f"[Source {i} — {r['kb']}]\n{text}\n")
    return "\n".join(parts)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "chunks_loaded": len(chunks)})


def is_swahili(text: str) -> bool:
    """Heuristic Swahili detection based on common Swahili word presence.

    Uses word-boundary matching, not substring matching -- a naive substring
    check previously misfired on English text containing 'Kenya' (which
    contains the substring 'ya'), among other false positives from short
    words like 'na'/'wa'/'kwa'. Short, collision-prone words are dropped
    entirely; the remainder require whole-word matches only."""
    text_lower = text.lower()
    common_swahili_words = [
        "ninahitaji", "kuhusu", "biashara", "nini", "vipi", "wapi", "gani",
        "je", "ninataka", "naomba",
        "kodi", "usajili", "mfanyakazi", "mshahara", "kampuni", "sheria",
    ]
    return any(
        re.search(r"\b" + re.escape(w) + r"\b", text_lower)
        for w in common_swahili_words
    )


def call_llama(messages, temperature=0.6, max_tokens=400):
    resp = requests.post(
        f"{LLAMA_SERVER_URL}/v1/chat/completions",
        json={
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "repeat_penalty": 1.3,
            "top_p": 0.9,
        },
    )
    data = resp.json()
    if "choices" not in data:
        print(f"[ERROR] llama-server returned unexpected response: {data}")
        return "I'm having trouble generating a response right now -- please try rephrasing your question or ask again in a moment."
    return data["choices"][0]["message"]["content"]


def translate_to_swahili(english_text: str) -> str:
    translation_messages = [
        {
            "role": "system",
            "content": (
                "You are a professional English-to-Kiswahili translator specializing "
                "in Kenyan business and regulatory terminology. Translate the following "
                "text into natural, fluent, grammatically correct Kiswahili. Keep "
                "acronyms, agency names, currency amounts, and percentages as-is "
                "(e.g. NSSF, KRA, KES, 6%). Preserve any markdown formatting "
                "(**bold**, bullet points, numbered lists) exactly as structured. "
                "Output ONLY the Kiswahili translation, nothing else -- no preamble, "
                "no explanation."
            ),
        },
        {"role": "user", "content": english_text},
    ]
    return call_llama(translation_messages, temperature=0.3, max_tokens=500)


@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    payload = request.get_json()
    messages = payload.get("messages", [])

    user_messages = [m for m in messages if m.get("role") == "user"]
    if not user_messages:
        return jsonify({"error": "no user message found"}), 400
    query = user_messages[-1]["content"]
    query_is_swahili = is_swahili(query)  # re-enabled: routes to CANNED_ANSWERS_SW for verified-answer topics only

    # Check for a hard-verified topic first -- bypass the LLM entirely for these,
    # guaranteeing zero fabrication since we return a pre-written, verified answer.
    canned_topic = get_canned_topic(query)
    if canned_topic:
        use_sw = query_is_swahili and canned_topic in CANNED_ANSWERS_SW
        answer_text = CANNED_ANSWERS_SW[canned_topic] if use_sw else CANNED_ANSWERS[canned_topic]
        lang_tag = "sw" if use_sw else "en"
        print(f"[CANNED] Query: {query[:80]!r} -- matched topic {canned_topic!r} ({lang_tag}), returning verified answer directly (no LLM call)")
        return jsonify({
            "choices": [{"message": {"role": "assistant", "content": answer_text}}]
        })

    if matches_digest_topic(query):
        retrieved = []
        context_block = SCOPE_INSTRUCTION + "\n\n(This question matches a topic already covered by verified facts above -- rely on those facts directly rather than any external material.)"
        print(f"[RAG] Query: {query[:80]!r} — matched digest-override topic, skipping retrieval")
    else:
        retrieval_query = build_retrieval_query(messages, query)
        retrieval_query = expand_swahili_terms(retrieval_query)
        retrieved = retrieve(retrieval_query)
        context_block = build_context_block(retrieved)

    augmented_messages = list(messages)
    insert_at = len(augmented_messages) - 1
    augmented_messages.insert(insert_at, {
        "role": "system",
        "content": context_block,
    })

    if query_is_swahili:
        # Force an English-language answer first, where the model is reliable
        augmented_messages.insert(insert_at + 1, {
            "role": "system",
            "content": "IMPORTANT: Answer the following question in English, even though it was asked in Kiswahili. A translation step will happen separately.",
        })

    if retrieved:
        print(f"[RAG] Query: {query[:80]!r} (retrieval query: {retrieval_query[:80]!r}) — "
              f"retrieved {len(retrieved)} chunks (top score {retrieved[0]['score']:.3f}) "
              f"from: {', '.join(sorted(set(r['kb'] for r in retrieved)))} "
              f"[swahili_detected={query_is_swahili}]")
    else:
        print(f"[RAG] Query: {query[:80]!r} — no relevant chunks found above threshold "
              f"[swahili_detected={query_is_swahili}]")

    english_answer = call_llama(augmented_messages, temperature=payload.get("temperature", 0.6),
                                  max_tokens=payload.get("max_tokens", 400))

    if query_is_swahili:
        final_answer = translate_to_swahili(english_answer)
        print(f"[Translation] Converted English answer to Kiswahili ({len(final_answer)} chars)")
    else:
        final_answer = english_answer

    return jsonify({
        "choices": [{"message": {"role": "assistant", "content": final_answer}}]
    })


if __name__ == "__main__":
    print(f"RAG proxy server starting on port {PORT}")
    print(f"Forwarding to llama-server at {LLAMA_SERVER_URL}")
    app.run(host="0.0.0.0", port=PORT, threaded=True)
