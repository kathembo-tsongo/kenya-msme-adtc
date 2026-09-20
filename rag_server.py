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

# My Digest
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
    "maternity_paternity_leave": (
        "**Maternity leave** (Section 29, Employment Act 2007): female employees "
        "are entitled to **3 months (90 calendar days)** of maternity leave with "
        "**full pay** -- this can be taken before or after childbirth. Annual "
        "leave and sick leave continue accruing normally during maternity leave; "
        "she's entitled to return to the same or an equivalent position "
        "afterward.\n\n**Paternity leave** (Section 29(8)): male employees are "
        "entitled to **2 weeks (14 days)** of paternity leave, also with full "
        "pay, around the birth of their child.\n\nBoth are separate from, and "
        "don't reduce, the standard 21-working-day annual leave entitlement. "
        "Dismissing or disadvantaging an employee for taking either is illegal "
        "under the Employment Act."
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
        "- Mandatory once your annual taxable turnover exceeds **KES 5,000,000 (5 million)**\n"
        "- The standard VAT rate is **16%**, charged on your taxable sales\n"
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
    "class_r_permit": (
        "Go to the **Kenya eFNS portal** on eCitizen and apply for a **Class R "
        "Permit** -- the special permit for East African Community nationals "
        "(Burundi, DR Congo, Rwanda, South Sudan, Tanzania, Uganda), covering "
        "residing, working, trading, or running a business in Kenya. The "
        "permit itself is **free** (KES 0 processing, KES 0 issuance), "
        "gazetted under the Kenya Citizenship and Immigration Amendment "
        "Regulations 2024. You will separately need a **Foreigner Certificate "
        "(Alien Card)**, which costs **KES 5,000 per year**.\n\nTypical "
        "documents: valid passport, cover letter, KRA PIN if doing business, "
        "and a police clearance certificate (required specifically for "
        "small-scale traders). Apply online, then print the completed forms "
        "and submit them physically at the Immigration offices (Nyayo House, "
        "Nairobi)."
    ),
    "tcc_application": (
        "Log in to **itax.kra.go.ke** with your business KRA PIN (not a "
        "director's personal PIN), go to the **'Certificates'** menu, and "
        "select **'Apply for Tax Compliance Certificate (TCC)'**. Review your "
        "auto-filled details, select your reason for applying, and click "
        "Submit.\n\nIf your returns and payments are up to date, it's often "
        "approved within a day or two and emailed to you. If something is "
        "outstanding (an unfiled return, unpaid balance, or eTIMS "
        "non-compliance), the system flags it so you can resolve it before "
        "reapplying. It is **free**, and once issued it is valid for **12 "
        "months**."
    ),
    "probation_period": (
        "Under **Section 42 of the Employment Act 2007**, a probationary "
        "period cannot exceed **6 months initially**, but it may be extended "
        "for a further period of **not more than 6 months** with the "
        "employee's written consent -- making the maximum possible aggregate "
        "**12 months**, not a straight 1-year probation from the start.\n\n"
        "Most employers use a shorter period (commonly 3 months) as standard "
        "practice, reserving the full 6-month (or extended) period for more "
        "senior or technical roles. Probationary employees are excluded from "
        "Section 41's fair-hearing requirement before termination, but any "
        "dismissal must still be non-discriminatory and for a legitimate "
        "reason."
    ),
    "agpo": (
        "**AGPO** (Access to Government Procurement Opportunities) reserves "
        "**30% of all government procurement** for enterprises owned by "
        "youth (aged 18-35), women, and persons with disabilities, each "
        "requiring **at least 70% ownership** and **100% of leadership** "
        "from that group.\n\nTo register: have your business legally "
        "registered (sole proprietorship, partnership, or company), gather "
        "your registration certificate, KRA PIN/VAT certificate, Tax "
        "Compliance Certificate, and (for companies) your CR12 or (for "
        "partnerships) your partnership deed, then register directly at "
        "**agpo.go.ke**. Once certified, your status applies across all "
        "procuring entities -- national ministries, counties, and "
        "parastatals."
    ),
    "hustler_fund_business": (
        "The basic **Personal Loan** tier (KES 500 to KES 50,000, 8% per "
        "annum, repayable in 14 days) can be used for business or personal "
        "needs, accessible via *254# on your **M-PESA**-registered line -- you'll need ""a valid **Kenyan national ID** and an active SIM card, no collateral required. ""\n\nFor business specifically, Hustler "
        "Fund also offers group-based **Biashara/Enterprise loans** (for "
        "chamas, cooperatives, or registered groups) and higher-tier loans "
        "for **registered businesses with a KRA PIN**, both at the same 8% "
        "per annum rate but with larger amounts and longer repayment periods "
        "than the personal tier. Your loan limit and access to higher tiers "
        "grows with consistent on-time repayment history."
    ),
    "sole_prop_to_llc": (
        "Kenya doesn't have a single-step way to convert a business -- there's no direct 'conversion' process, practically, it's two "
        "separate actions: **(1) cease your existing business name** by filing "
        "**Form BN6** on eCitizen, and **(2) register a new private limited "
        "company** using **Forms CR1, CR2, CR8** plus Articles/Memorandum of "
        "Association (BRS provides standard templates, or you can customize "
        "them). You can typically reserve and reuse the same business name, "
        "now with 'Limited' or 'Ltd' added.\n\n"
        "**On KRA PIN specifically**: your sole proprietorship used your "
        "**personal KRA PIN**. The new company needs its **own separate "
        "company PIN**, applied for via iTax by selecting 'Non-Individual' as "
        "the taxpayer type -- and every director/shareholder must already "
        "have their own individual KRA PIN before the company PIN application "
        "can go through.\n\n"
        "**On fees**: expect two separate government charges -- business name "
        "cessation, and private limited company registration (roughly KES "
        "10,650-10,750 based on current BRS fee schedules, though I'd confirm "
        "the exact current figure on eCitizen directly). Note there is **no "
        "legal minimum share capital** requirement, though many people choose "
        "a nominal figure like KES 100,000 as practice. A clean conversion "
        "with all documents in order typically takes **5-10 working days**."
    ),
    "wef": (
        "The **Women Enterprise Fund (WEF)** is a real, distinct government agency "
        "(established 2007, under the Ministry of Public Service, Youth & Gender "
        "Affairs) -- not to be confused with YEDF (youth-focused) or the Hustler "
        "Fund. **Eligibility: any Kenyan woman aged 18 or older**, applying "
        "individually or as part of a registered group.\n\n"
        "**Key products**:\n"
        "- **Tuinuke Chama Loan** (via the Constituency Women Enterprise Scheme): "
        "for registered women's groups of 10-30 members (at least 70% women, "
        "100% women in leadership), registered with Social Services for at "
        "least 3 months, with a bank/SACCO account -- low-cost with a small "
        "administration charge\n"
        "- **LPO Financing**: for individual women-owned businesses needing to "
        "fulfill purchase orders or tenders\n\n"
        "Apply through WEF's regional offices, or online at wef.go.ke."
    ),
    "unified_business_permit": (
        "In Nairobi County specifically, this is the **Unified Business Permit "
        "(UBP)** -- a single annual license that bundles what used to be "
        "several separate approvals (trade license, fire inspection, food/"
        "health certificate, advertisement/signage permit) into one "
        "application. Apply via the **NairobiPay self-service portal "
        "(nairobiservices.go.ke)**, dial ***647#**, or visit City Hall Annex "
        "in person.\n\nThe fee depends on your business category and size "
        "(a small shop might pay around KES 4,000 plus a KES 200 application "
        "fee; larger operations pay significantly more) -- confirm your "
        "exact category's fee on the portal. It runs on a **January-"
        "December annual cycle**; renewal applications typically open in "
        "November, with payment expected by around March 31 to avoid "
        "escalating late penalties. Other counties (Mombasa, Meru, Kisumu, "
        "and several others) use eCitizen instead of a county-specific "
        "portal for their equivalent single business permit."
    ),
    "pharmacy_license": (
        "Operating a pharmacy or chemist shop requires licensing from the "
        "**Pharmacy and Poisons Board (PPB)**, the national medicines "
        "regulator under the Pharmacy and Poisons Act (Cap 244) -- this is "
        "in addition to, not instead of, your county Single Business Permit "
        "(roughly KES 5,000-30,000).\n\n**Key requirement**: everyone "
        "holding a financial interest in the pharmacy must be a registered "
        "pharmacist or enrolled pharmaceutical technologist -- you generally "
        "can't own a pharmacy purely as a non-pharmacist investor. The "
        "designated superintendent pharmacist also needs their own annual "
        "practicing license from PPB.\n\n**Process**: register your "
        "premises with PPB, then pass a premises inspection covering proper "
        "shelving, ventilation, a dispensing area separate from the sales "
        "counter, a lockable poisons cabinet, a refrigerator for cold-chain "
        "products, and Green Cross signage. Licenses are issued after a "
        "successful inspection and must be renewed annually (all PPB "
        "licenses expire December 31)."
    ),
    "ca_license": (
        "Not every tech startup needs this -- the **Communications "
        "Authority of Kenya (CA)** specifically licenses telecommunications, "
        "broadcasting, internet service provision, and postal/courier "
        "operators, not general software or app businesses. If your startup "
        "purely builds an app or website without operating telecom "
        "infrastructure or providing regulated content/network services, you "
        "likely don't need a CA license at all.\n\nIf you DO fall into a "
        "regulated category, CA's Unified Licensing Framework covers three "
        "main types: **Network Facilities Provider**, **Application Service "
        "Provider**, and **Content Service Provider** (plus separate "
        "licenses for broadcasting, equipment type-approval, and courier/"
        "postal services). Applications need a cover letter to the Director "
        "of Licensing, your certificate of registration, company documents "
        "(CR12 for companies), and a list of directors -- foreign-owned "
        "companies need at least 30% Kenyan shareholding. Processing runs on "
        "a first-come-first-served basis with a stated turnaround of around "
        "135 days."
    ),
    "nssf_registration": (
        "**As an employer**, register via the NSSF Employer Self-Service "
        "portal (selfservice.nssf.or.ke) -- select 'Employer Registration' "
        "if you've never registered before. It's worth getting your **KRA "
        "PIN first**, since you'll need it during registration. Once "
        "approved, you're issued an employer number, often on the spot.\n\n"
        "**Registration is mandatory** for every employer with even one "
        "employee earning KES 1,000 or more per month -- this includes "
        "casual, temporary, and part-time workers, not just permanent "
        "staff. Skipping registration is a legal offense under the NSSF Act "
        "2013.\n\n**For each employee**: they can register in person at any "
        "NSSF office with their national ID/passport/Alien Card and an "
        "introduction letter from you as their employer, after which they "
        "receive an NSSF membership number you'll need to remit their "
        "contributions."
    ),
    "keproba": (
        "**KEPROBA** (Kenya Export Promotion and Branding Agency) is a "
        "state corporation (formed 2019, merging the former Export "
        "Promotion Council and Brand Kenya Board) that supports Kenyan "
        "exporters and promotes 'Brand Kenya' internationally.\n\n"
        "**What it actually offers**: guidance on export procedures and "
        "documentation, market intelligence and market-entry requirements "
        "for target countries, capacity-building through export training "
        "and coaching, organized trade missions and trade fair "
        "participation, and support with **product development and "
        "branding** -- including packaging, labelling, and brand "
        "positioning to help your goods resonate with international "
        "buyers. It particularly prioritizes bringing youth- and "
        "women-led producer groups into the export process. Reach out "
        "through KEPROBA's offices or makeitkenya.go.ke to access these "
        "services."
    ),
    "no_permit_penalty": (
        "Operating without a valid county business permit is illegal in "
        "Kenya, under the **County Governments Act 2012** combined with "
        "each county's own Finance Act and Trade Licensing Act (Nairobi's "
        "trade licensing, for example, falls under its own County Trade "
        "Licensing Act).\n\n**Consequences can include**:\n"
        "- **Fines**: commonly cited in the range of KES 50,000-200,000, "
        "though this varies significantly by county -- confirm your "
        "specific county's penalty schedule\n"
        "- **Closure orders**: county inspectors can issue an immediate "
        "closure order, shutting your business until you comply\n"
        "- **Possible imprisonment**: in serious or repeated cases, "
        "directors/owners can face criminal prosecution personally, not "
        "just the business\n"
        "- **Back-payment of penalties**: on top of the permit fee itself "
        "once you do comply\n\n"
        "Most counties allow a grace period (commonly 30-60 days after "
        "expiry) before penalties kick in for a *lapsed* permit -- but "
        "operating with no permit at all from the start carries the fuller "
        "risk above from day one."
    ),
    "sole_prop_vs_limited": (
        "The core difference is **liability and separateness**. A **sole "
        "proprietorship** isn't a separate legal entity from you -- you and "
        "the business are the same in law, meaning you carry **unlimited "
        "personal liability** for business debts, and you use your own "
        "**personal KRA PIN**. It's fast and cheap to set up, with no "
        "minimum capital.\n\nA **limited company** is a separate legal "
        "person from its owners -- shareholders' liability is generally "
        "limited to what they've invested in shares, and the company gets "
        "its **own separate KRA PIN**, its own bank account, and can enter "
        "contracts, sue, or be sued in its own name. There's **no legal "
        "minimum share capital** required to register one, though it "
        "involves more paperwork (Memorandum/Articles of Association, "
        "CR1/CR2/CR8 forms) and ongoing compliance (annual returns to BRS) "
        "than a sole proprietorship. Many businesses start as sole "
        "proprietorships and convert to a limited company as they grow, "
        "specifically to gain that liability protection."
    ),
    "late_filing_penalty": (
        "Penalties depend on which return and whether it's late filing or "
        "late payment -- both apply to KRA obligations under the **Tax "
        "Procedures Act 2015**:\n\n"
        "- **Individual income tax**: KES 2,000 per return for late filing\n"
        "- **Company/partnership income tax**: KES 20,000 or 5% of the tax "
        "due, whichever is higher, for late filing; late payment adds "
        "another 5% plus 1% monthly interest on the unpaid amount\n"
        "- **PAYE**: late filing is 25% of the tax due or KES 10,000, "
        "whichever is higher; late payment is 5% plus 1% monthly interest\n"
        "- **VAT**: late filing is 5% of the tax due or KES 10,000, "
        "whichever is higher; late payment adds 5% plus 1% monthly "
        "interest\n\n"
        "**Even with zero income or sales, you must still file a nil "
        "return** -- skipping it triggers the same automatic penalty as "
        "any other missed return. Penalties apply automatically the day "
        "after the deadline, with no prior warning, so it's always better "
        "to file on time even if you can't pay yet (unpaid tax only draws "
        "interest, which is far less costly than filing-plus-payment "
        "penalties combined)."
    ),
    "compliance_software": "There isn't one package you are required to use, but these are the official systems most Kenyan MSMEs need for compliance:\n\n- **eTIMS** (KRA's electronic tax invoice system): required for VAT-registered businesses, and needed for your business expenses to be tax-deductible. The free **eTIMS Lite** option (web portal or USSD *222#) is the simplest way for a small business to comply without buying equipment.\n- **KRA iTax (itax.kra.go.ke)**: KRA's portal for filing returns, including the monthly PAYE return (P10) if you have employees.\n- **NSSF Employer Self-Service portal (selfservice.nssf.or.ke)**: register as an employer and manage your NSSF obligations if you employ staff.\n\nIf you also want accounting or payroll software on top of these, I can't recommend a specific product, but check that it calculates the current PAYE bands, NSSF tiers, SHIF (2.75% of gross pay) and Housing Levy (1.5% each for employee and employer) correctly, and that it can issue eTIMS-compliant invoices.",
    "regulations_not_exhaustive": 'No -- there isn\'t a single complete list, because what applies depends on your business type, your turnover and whether you employ people. These are the baseline items that apply to most Kenyan businesses:\n\n- **Registration**: register your business name (eCitizen/BRS) and get a KRA PIN\n- **County permit**: a single business permit from your county government -- the category and fee vary by county\n- **Income tax regime**: Turnover Tax (1.5% of gross sales) if your annual turnover is between KES 1,000,000 and KES 25,000,000; VAT registration once your annual taxable turnover exceeds KES 5,000,000\n- **eTIMS**: KRA\'s e-invoicing system, required for VAT-registered businesses and needed for your expenses to be tax-deductible (the free eTIMS Lite option is the simplest for small businesses)\n- **If you employ people**: NSSF (6% employee + 6% employer), PAYE, SHIF (2.75% of gross pay) and the Housing Levy (1.5% employee + 1.5% employer), plus written contracts and leave records -- ask about your "payroll obligations" for the full list\n\nSome sectors also need their own licences (for example food businesses or pharmacies). Tell me your specific business type and I\'ll give you the requirements I can verify for it.',
    "relocation_county": "Kenya has counties rather than states, and moving your business from one county to another mostly changes your **county licensing**, not your national taxes.\n\n- **National taxes stay the same**: Turnover Tax (1.5% of gross sales for turnover between KES 1,000,000 and KES 25,000,000), VAT (once taxable turnover reaches KES 5,000,000) and, if you employ staff, PAYE, NSSF, SHIF and the Housing Levy are set nationally and collected through KRA. They don't depend on which county you operate from.\n- **County licensing changes**: a single business permit is issued by each county government, and the category and fee vary by county. In your new county you will need a permit from that county's business licensing office.\n\nConfirm the exact category and fee with your new county.",
    "barber_salon_taxes": 'Tax obligations for a barber or salon business in Kenya depend on your annual turnover and on whether you employ staff -- not on the trade itself:\n\n- **Turnover Tax (TOT)**: 1.5% of gross sales if your annual turnover is more than KES 1,000,000 but does not exceed KES 25,000,000. It is charged on gross sales with **no expense deductions**. For example, KES 2,000,000 of annual sales means KES 30,000 of TOT (2,000,000 x 1.5%). Below KES 1,000,000 you are exempt from TOT.\n- **VAT**: if your turnover reaches KES 5,000,000 and you deal in vatable supplies, you must also register for VAT.\n- **If you employ staff**: PAYE (bands from 10% to 35%, less KES 2,400 monthly personal relief), NSSF (6% employee + 6% employer), SHIF (2.75% of gross pay) and the Housing Levy (1.5% employee + 1.5% employer) -- ask about your "payroll obligations" for the full list.\n- **County permit**: a single business permit from your county government; the category and fee vary by county.\n\nWhere you operate affects your county permit and fees, but the national tax rules above are the same in every county. Confirm your specific position via iTax (itax.kra.go.ke).',
    "sole_prop_llc_mistakes": "Common mistakes when moving from a sole proprietorship to a limited company:\n\n- **Expecting a direct conversion**: Kenya has no one-step conversion. It is two separate actions -- cease your business name (Form BN6 on eCitizen) and register a new private limited company (Forms CR1, CR2, CR8 plus the Articles/Memorandum of Association).\n- **Carrying over your personal KRA PIN**: the new company needs its own separate company PIN, applied for via iTax as a 'Non-Individual' taxpayer.\n- **Applying for the company PIN too early**: every director and shareholder must already have their own individual KRA PIN before the company PIN application can go through.\n- **Budgeting for only one charge**: expect two separate government charges -- business name cessation and company registration.\n- **Delaying because of share capital**: there is no legal minimum share capital requirement.\n\nConfirm the current forms and fees directly on eCitizen before you file.",
    "etims_general": (
        "**eTIMS** (electronic Tax Invoice Management System) is KRA's "
        "system for generating tax-compliant, verifiable electronic "
        "invoices/receipts -- it's required for VAT-registered businesses, "
        "and for anyone wanting business expenses to be tax-deductible, "
        "since KRA only accepts eTIMS-generated invoices as valid proof of "
        "purchase.\n\n**Why your business needs it**: without eTIMS "
        "invoices, your business expenses may not be deductible for tax "
        "purposes, and customers who need to claim their own input VAT or "
        "expense deductions can't do so from a non-eTIMS invoice -- making "
        "it harder to sell to other VAT-registered businesses.\n\nFor "
        "smaller businesses, the free **eTIMS Lite** option (via web "
        "portal or USSD *222#) is the simplest way to comply without "
        "buying equipment. Non-compliance penalties can reach up to **KES "
        "1,000,000 or 10% of the tax involved**, whichever is higher."
    ),
    "sacco_vs_bank": (
        "**SACCOs** typically offer meaningfully cheaper loans than "
        "commercial banks -- commonly **10-14% per annum** (reducing "
        "balance), often fixed by the SACCO's own annual general meeting "
        "rather than fluctuating with the Central Bank Rate. Commercial "
        "**bank** loans typically run **13-20%+ per annum** and move with "
        "CBK rate changes.\n\n**Key trade-off**: SACCOs require you to "
        "**join and build a savings history first** (commonly 3-6 months) "
        "before you can borrow, and loan amounts are often capped as a "
        "multiple of your savings (roughly 3-5x). Banks generally don't "
        "require prior membership/savings and can lend larger, more "
        "flexible amounts, especially against collateral -- but at a "
        "higher rate. SACCO members also earn dividends on their shares "
        "and savings, which partially offsets the cost of borrowing, a "
        "benefit a bank account doesn't offer."
    ),
    "food_business_license": (
        "A food business (restaurant, cafe, bakery, shop) needs several "
        "layers, on top of your standard county business permit "
        "(Single/Unified Business Permit):\n\n"
        "- **Health/Food Hygiene Certificate**: issued by your county "
        "health department, confirming your premises meet hygiene "
        "standards -- typically KES 2,000-5,000, required before opening\n"
        "- **Food Handler's Health Certificate**: required for **every "
        "individual employee** who handles food, obtained after a medical "
        "check-up (roughly KES 1,000 per person)\n"
        "- **Fire Safety Certificate**: mandatory for all businesses, "
        "requiring fire extinguishers and a county fire department "
        "inspection, renewed annually\n"
        "- **Restaurant-specific**: registration with the **Tourism "
        "Regulatory Authority (TRA)** under the Tourism Act 2011, if you "
        "operate as a restaurant\n\n"
        "If you manufacture or package food products for sale (not just "
        "serve food on-site), you'll also need **KEBS** certification "
        "(Standardization Mark) specific to packaged/processed goods."
    ),
    "employee_compliance_checklist": (
        "For a trading enterprise with permanent staff, here's what to maintain:\n\n"
        "**Employment contracts**: a written contract (or at minimum a written "
        "statement of particulars, required within 2 months of start date for "
        "any employment lasting more than 3 months) covering start date, job "
        "description, salary, working hours, and leave entitlement.\n\n"
        "**Statutory deductions, per employee, per month**:\n"
        "- **NSSF**: 6% employee + 6% employer (matched), Tier I up to KES "
        "9,000, Tier II up to KES 108,000\n"
        "- **PAYE**: progressive bands from 10% to 35%, less KES 2,400 "
        "personal relief\n"
        "- **SHIF** (Social Health Insurance Fund -- this replaced NHIF in "
        "October 2024): 2.75% of gross pay, employee-side only, no cap\n"
        "- **Housing Levy**: 1.5% employee + 1.5% employer, no minimum "
        "income threshold\n\n"
        "**Leave records**: minimum 21 working days of annual leave per 12 "
        "months of service (Employment Act Section 28).\n\n"
        "**Payroll records**: document each employee's monthly salary and "
        "all deductions above, and remit them on time -- NSSF, PAYE, SHIF, "
        "and Housing Levy all follow the same 9th-of-the-following-month "
        "deadline. Keep these records available for inspection, and confirm "
        "your county's specific retention-period requirement, since this "
        "isn't fully standardized nationally."
    ),
    "business_insurance": (
        "Kenya's insurance industry is regulated by the **Insurance "
        "Regulatory Authority (IRA)**, not KRA -- KRA is the tax "
        "authority and has no role in insurance.\n\n**Compulsory "
        "insurance, if you have employees**: cover under the **Work "
        "Injury Benefits Act (WIBA)**, protecting employees injured or "
        "disabled at work -- this is legally required, not optional. If "
        "your business uses any motor vehicle, **motor third-party "
        "liability insurance** is also compulsory.\n\n**Common optional "
        "cover worth considering**: public liability insurance (covers "
        "injury to customers/visitors on your premises), property/fire "
        "insurance (covers your stock, equipment, and premises), and "
        "business interruption cover (covers lost income if you have to "
        "close temporarily, e.g. after a fire).\n\nCoverage details, "
        "exclusions, and pricing vary significantly by insurer -- confirm "
        "specifics with a **licensed insurer or broker** (check the IRA's "
        "list of licensed providers at ira.go.ke), not KRA."
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
    "maternity_paternity_leave": (
        "**Likizo ya uzazi** (Kifungu cha 29, Sheria ya Ajira 2007): "
        "wafanyakazi wa kike wanastahili **miezi 3 (siku 90 za kalenda)** za "
        "likizo ya uzazi yenye **malipo kamili** -- inaweza kuchukuliwa kabla "
        "au baada ya kujifungua. Likizo ya kila mwaka na likizo ya ugonjwa "
        "huendelea kukusanywa kawaida wakati wa likizo ya uzazi; anastahili "
        "kurudi kwenye nafasi ile ile au sawa baada ya "
        "hapo.\n\n**Likizo ya baba** (Kifungu cha 29(8)): wafanyakazi wa "
        "kiume wanastahili **wiki 2 (siku 14)** za likizo ya baba, pia "
        "yenye malipo kamili, karibu na kuzaliwa kwa mtoto.\n\nZote mbili "
        "ni tofauti na, na hazipunguzi, haki ya kawaida ya likizo ya "
        "siku 21 za kazi kwa mwaka. Kumfukuza au kumnyima mfanyakazi haki "
        "kwa kuchukua yoyote kati ya hizi ni kinyume cha sheria chini ya "
        "Sheria ya Ajira."
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
        "- Kiwango cha kawaida cha VAT ni **16%**, kinachotozwa kwenye mauzo yako yanayotozwa kodi\n"
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
    "sole_prop_to_llc": (
        "Kenya haina mchakato wa hatua moja wa 'kubadilisha' -- kwa kweli, "
        "ni hatua mbili tofauti: **(1) sitisha jina lako la biashara "
        "lililopo** kwa kujaza **Fomu ya BN6** kwenye eCitizen, na **(2) "
        "sajili kampuni mpya ya kikomo** ukitumia **Fomu za CR1, CR2, CR8** "
        "pamoja na Memorandum/Articles of Association (BRS hutoa violezo "
        "vya kawaida, au unaweza kuvibinafsisha). Kwa kawaida unaweza "
        "kutumia jina lile lile la biashara, sasa likiwa na 'Limited' au "
        "'Ltd'.\n\n**Kuhusu PIN ya KRA hasa**: biashara yako ya umiliki "
        "binafsi ilitumia **PIN yako binafsi ya KRA**. Kampuni mpya "
        "inahitaji **PIN yake tofauti**, unaomba kupitia iTax kwa kuchagua "
        "'Non-Individual' kama aina ya mlipa kodi -- na kila mkurugenzi/"
        "mwanahisa lazima awe na PIN yake binafsi ya KRA kabla ya maombi "
        "ya PIN ya kampuni kuendelea.\n\n**Kuhusu ada**: tarajia malipo "
        "mawili tofauti ya serikali -- kusitisha jina la biashara, na "
        "usajili wa kampuni ya kikomo (takriban KES 10,650-10,750 kulingana "
        "na ratiba za sasa za BRS, ingawa ningependekeza uthibitishe kiasi "
        "halisi cha sasa moja kwa moja kwenye eCitizen). Kumbuka hakuna "
        "**mtaji wa chini wa hisa unaotakiwa kisheria**, ingawa watu wengi "
        "huchagua kiasi kama KES 100,000 kama mazoea. Mchakato safi wenye "
        "nyaraka zote sahihi kwa kawaida huchukua **siku 5-10 za kazi**."
    ),
    "wef": (
        "**Women Enterprise Fund (WEF)** ni shirika halisi na tofauti la "
        "serikali (lilianzishwa 2007, chini ya Wizara ya Utumishi wa Umma, "
        "Vijana na Mambo ya Jinsia) -- lisichanganywe na YEDF (inayolenga "
        "vijana) au Hustler Fund. **Sifa: mwanamke yeyote wa Kenya mwenye "
        "miaka 18 au zaidi**, akiomba peke yake au kama sehemu ya kikundi "
        "kilichosajiliwa.\n\n**Bidhaa kuu**:\n"
        "- **Mkopo wa Tuinuke Chama** (kupitia Constituency Women "
        "Enterprise Scheme): kwa vikundi vya wanawake vilivyosajiliwa vya "
        "wanachama 10-30 (angalau asilimia 70 wanawake, uongozi wa "
        "asilimia 100 wanawake), vilivyosajiliwa na Huduma za Jamii kwa "
        "angalau miezi 3, vyenye akaunti ya benki/SACCO -- gharama ndogo "
        "yenye ada ndogo ya utawala\n"
        "- **Ufadhili wa LPO**: kwa biashara za wanawake binafsi "
        "zinazohitaji kutimiza maagizo ya ununuzi au zabuni\n\n"
        "Omba kupitia ofisi za kanda za WEF, au mtandaoni kwenye wef.go.ke."
    ),
    "agpo": (
        "**AGPO** (Access to Government Procurement Opportunities) "
        "inatenga **asilimia 30 ya manunuzi yote ya serikali** kwa "
        "makampuni yanayomilikiwa na vijana (miaka 18-35), wanawake, na "
        "watu wenye ulemavu, kila kundi likihitajika kuwa na **umiliki wa "
        "asilimia 70 angalau** na **uongozi wa asilimia 100** kutoka kwa "
        "kundi hilo.\n\nKujiandikisha: hakikisha biashara yako imesajiliwa "
        "kisheria (umiliki binafsi, ubia, au kampuni), kusanya cheti cha "
        "usajili, PIN/cheti cha VAT cha KRA, Tax Compliance Certificate, na "
        "(kwa makampuni) CR12 au (kwa ubia) hati ya ubia, kisha jisajili "
        "moja kwa moja kwenye **agpo.go.ke**. Ukisha idhinishwa, hadhi yako "
        "inatumika katika taasisi zote za manunuzi -- wizara za kitaifa, "
        "kaunti, na mashirika ya umma."
    ),
    "tcc_application": (
        "Ingia kwenye **itax.kra.go.ke** ukitumia PIN ya KRA ya biashara "
        "(si PIN binafsi ya mkurugenzi), nenda kwenye menyu ya "
        "**'Certificates'**, kisha chagua **'Apply for Tax Compliance "
        "Certificate (TCC)'**. Kagua taarifa zilizojazwa kiotomatiki, chagua "
        "sababu ya kuomba, kisha bofya Submit.\n\nIkiwa marejesho na malipo "
        "yako yako sawa, mara nyingi huidhinishwa ndani ya siku moja au "
        "mbili na kutumwa kwa barua pepe. Ikiwa kuna jambo lililobaki "
        "(marejesho ambayo hayajawasilishwa, malipo yaliyobaki, au "
        "kutokamilisha eTIMS), mfumo utakuonyesha ili ulishughulikie kabla "
        "ya kuomba tena. Ni **bure**, na ikitolewa ni halali kwa **miezi "
        "12**."
    ),
    "class_r_permit": (
        "Nenda kwenye tovuti ya **Kenya eFNS** kupitia eCitizen na uombe "
        "**Class R Permit** -- kibali maalum kwa raia wa Jumuiya ya Afrika "
        "Mashariki (Burundi, DR Congo, Rwanda, Sudan Kusini, Tanzania, "
        "Uganda), kinachoruhusu kuishi, kufanya kazi, kufanya biashara, au "
        "kuendesha kampuni nchini Kenya. Kibali chenyewe ni **bure** (KES 0), "
        "kilichowekwa kisheria chini ya Kenya Citizenship and Immigration "
        "Amendment Regulations 2024. Utahitaji pia **Foreigner Certificate "
        "(Alien Card)**, ambayo inagharimu **KES 5,000 kwa mwaka**.\n\n"
        "Hati zinazohitajika kwa kawaida: pasipoti halali, barua ya maombi, "
        "PIN ya KRA endapo unafanya biashara, na cheti cha uthibitisho wa "
        "polisi (kwa wafanyabiashara wadogo). Omba mtandaoni, kisha "
        "chapisha fomu na uwasilishe kwa mkono katika ofisi za Uhamiaji "
        "(Nyayo House, Nairobi)."
    ),
    "tcc_application": (
        "Ingia kwenye **itax.kra.go.ke** ukitumia PIN ya KRA ya biashara "
        "(si PIN binafsi ya mkurugenzi), nenda kwenye menyu ya "
        "**'Certificates'**, kisha chagua **'Apply for Tax Compliance "
        "Certificate (TCC)'**. Kagua taarifa zilizojazwa kiotomatiki, chagua "
        "sababu ya kuomba, kisha bofya Submit.\n\nIkiwa marejesho na malipo "
        "yako yako sawa, mara nyingi huidhinishwa ndani ya siku moja au "
        "mbili na kutumwa kwa barua pepe. Ikiwa kuna jambo lililobaki "
        "(marejesho ambayo hayajawasilishwa, malipo yaliyobaki, au "
        "kutokamilisha eTIMS), mfumo utakuonyesha ili ulishughulikie kabla "
        "ya kuomba tena. Ni **bure**, na ikitolewa ni halali kwa **miezi "
        "12**."
    ),
    "probation_period": (
        "Kwa mujibu wa **Kifungu cha 42 cha Sheria ya Ajira ya 2007**, "
        "kipindi cha majaribio (probation) hakiwezi kuzidi **miezi 6** "
        "mwanzoni, lakini kinaweza kuongezwa kwa kipindi kingine cha **si "
        "zaidi ya miezi 6** kwa ridhaa ya maandishi ya mfanyakazi -- hivyo "
        "muda wa juu unaowezekana ni **miezi 12** kwa jumla, si mwaka "
        "mmoja moja kwa moja tangu mwanzo.\n\nWaajiri wengi hutumia "
        "kipindi kifupi zaidi (kawaida miezi 3), wakihifadhi kipindi kizima "
        "cha miezi 6 (au kilichoongezwa) kwa nafasi za juu zaidi au za "
        "kitaalamu. Wafanyakazi walio kwenye majaribio hawapo chini ya "
        "sharti la usikilizwaji wa haki la Kifungu cha 41 kabla ya "
        "kufukuzwa, lakini uamuzi wowote lazima usiwe wa ubaguzi na uwe na "
        "sababu halali."
    ),
    "unified_business_permit": (
        "Katika Kaunti ya Nairobi hasa, hii ni **Unified Business Permit "
        "(UBP)** -- leseni moja ya kila mwaka inayounganisha vibali "
        "kadhaa vilivyokuwa tofauti (leseni ya biashara, ukaguzi wa moto, "
        "cheti cha afya/chakula, kibali cha matangazo/alama) katika maombi "
        "moja. Omba kupitia **NairobiPay (nairobiservices.go.ke)**, piga "
        "***647#**, au tembelea City Hall Annex.\n\nAda inategemea aina na "
        "ukubwa wa biashara yako (duka dogo huenda likilipa karibu KES "
        "4,000 pamoja na KES 200 ya maombi; shughuli kubwa zaidi hulipa "
        "zaidi) -- thibitisha ada halisi ya aina yako kwenye tovuti. "
        "Inafuata mzunguko wa **Januari-Desemba**; maombi ya kuhuisha "
        "kwa kawaida hufunguliwa Novemba, na malipo yanatarajiwa kabla ya "
        "Machi 31 kuepuka adhabu zinazoongezeka."
    ),
    "pharmacy_license": (
        "Kuendesha duka la dawa au kemisti kunahitaji leseni kutoka "
        "**Pharmacy and Poisons Board (PPB)**, msimamizi wa kitaifa wa "
        "dawa chini ya Sheria ya Dawa na Sumu (Cap 244) -- hii ni pamoja "
        "na, si badala ya, Single Business Permit ya kaunti yako "
        "(takriban KES 5,000-30,000).\n\n**Sharti muhimu**: kila mtu "
        "mwenye maslahi ya kifedha katika duka la dawa lazima awe "
        "mfamasia aliyesajiliwa au fundi wa dawa aliyeandikishwa -- kwa "
        "kawaida huwezi kumiliki duka la dawa kama mwekezaji tu asiye "
        "mfamasia. Msimamizi mfamasia aliyeteuliwa pia anahitaji leseni "
        "yake ya kila mwaka ya kufanya kazi kutoka PPB.\n\n**Mchakato**: "
        "sajili majengo yako na PPB, kisha pitisha ukaguzi wa majengo "
        "unaoangalia rafu sahihi, mzunguko wa hewa, eneo la kutolea dawa "
        "tofauti na counter ya mauzo, kabati la sumu lenye kufuli, jokofu "
        "kwa bidhaa zinazohitaji baridi, na alama ya Msalaba wa Kijani. "
        "Leseni hutolewa baada ya ukaguzi wenye mafanikio na lazima "
        "zihuishwe kila mwaka (leseni zote za PPB huisha Desemba 31)."
    ),
    "ca_license": (
        "Si kila kampuni ya teknolojia inahitaji hii -- **Communications "
        "Authority of Kenya (CA)** inatoa leseni hasa kwa mawasiliano ya "
        "simu, utangazaji, huduma za intaneti, na waendeshaji wa posta/"
        "kurier, si biashara za kawaida za programu. Ikiwa kampuni yako "
        "inajenga tu programu au tovuti bila kuendesha miundombinu ya "
        "mawasiliano au kutoa huduma za maudhui/mtandao zinazodhibitiwa, "
        "huenda usihitaji leseni ya CA kabisa.\n\nIkiwa unaangukia katika "
        "kundi linalodhibitiwa, mfumo wa CA wa Unified Licensing "
        "Framework unahusisha aina tatu kuu: **Network Facilities "
        "Provider**, **Application Service Provider**, na **Content "
        "Service Provider** (pamoja na leseni tofauti za utangazaji, "
        "uidhinishaji wa vifaa, na huduma za posta/kurier). Maombi "
        "yanahitaji barua kwa Mkurugenzi wa Leseni, cheti chako cha "
        "usajili, hati za kampuni (CR12 kwa makampuni), na orodha ya "
        "wakurugenzi."
    ),
    "nssf_registration": (
        "**Kama mwajiri**, jisajili kupitia NSSF Employer Self-Service "
        "portal (selfservice.nssf.or.ke) -- chagua 'Employer "
        "Registration' ikiwa hujawahi kujisajili. Ni vyema kuwa na "
        "**PIN yako ya KRA kwanza**, kwani utaihitaji wakati wa usajili. "
        "Ukisha idhinishwa, unapewa namba ya mwajiri, mara nyingi papo "
        "hapo.\n\n**Usajili ni wa lazima** kwa kila mwajiri mwenye "
        "hata mfanyakazi mmoja anayepata KES 1,000 au zaidi kwa mwezi -- "
        "hii inajumuisha wafanyakazi wa muda, wa kandarasi, na wa muda "
        "mfupi, si wafanyakazi wa kudumu pekee. Kutojisajili ni kosa la "
        "kisheria chini ya Sheria ya NSSF ya 2013.\n\n**Kwa kila "
        "mfanyakazi**: wanaweza kujisajili wenyewe katika ofisi yoyote ya "
        "NSSF wakiwa na kitambulisho chao cha taifa/pasipoti/Alien Card na "
        "barua ya utambulisho kutoka kwako kama mwajiri wao, baada ya "
        "hapo watapokea namba ya uanachama wa NSSF utakayoihitaji kutuma "
        "michango yao."
    ),
    "keproba": (
        "**KEPROBA** (Kenya Export Promotion and Branding Agency) ni "
        "shirika la serikali (lililoundwa 2019, likiunganisha Export "
        "Promotion Council ya zamani na Brand Kenya Board) linalosaidia "
        "wafanyabiashara wa Kenya kuuza nje na kuendeleza 'Brand "
        "Kenya' kimataifa.\n\n**Kile kinachotolewa**: mwongozo wa "
        "taratibu na nyaraka za usafirishaji, taarifa za soko na sharti "
        "za kuingia katika nchi lengwa, ujenzi wa uwezo kupitia mafunzo "
        "ya usafirishaji, ujumbe wa kibiashara na ushiriki katika "
        "maonyesho ya biashara, na msaada wa **maendeleo ya bidhaa na "
        "branding** -- ikiwa ni pamoja na ufungashaji, uwekaji lebo, na "
        "uwekaji nafasi ya chapa kwa wanunuzi wa kimataifa. Wasiliana "
        "kupitia ofisi za KEPROBA au makeitkenya.go.ke."
    ),
    "no_permit_penalty": (
        "Kuendesha biashara bila kibali halali cha kaunti ni kinyume cha "
        "sheria nchini Kenya, chini ya **Sheria ya Serikali za Kaunti ya "
        "2012** pamoja na Sheria ya Fedha na Leseni za Biashara za kaunti "
        "yako.\n\n**Madhara yanaweza kujumuisha**:\n"
        "- **Faini**: mara nyingi kati ya KES 50,000-200,000, ingawa hii "
        "inatofautiana sana kwa kaunti\n"
        "- **Amri za kufunga**: wakaguzi wa kaunti wanaweza kutoa amri ya "
        "kufunga mara moja, wakifunga biashara yako mpaka utii\n"
        "- **Kifungo kinachowezekana**: katika hali mbaya au za "
        "kurudia, wakurugenzi/wamiliki wanaweza kukabiliwa na mashtaka ya "
        "jinai binafsi\n"
        "- **Malipo ya nyuma ya adhabu**: juu ya ada ya kibali chenyewe "
        "ukisha tii\n\n"
        "Kaunti nyingi huruhusu muda wa neema (kawaida siku 30-60 baada "
        "ya kuisha) kabla ya adhabu kuanza kwa kibali kilichoisha muda -- "
        "lakini kuendesha bila kibali kabisa tangu mwanzo kunabeba hatari "
        "kamili tangu siku ya kwanza."
    ),
    "sole_prop_vs_limited": (
        "Tofauti kuu ni **dhima na utengano**. **Umiliki binafsi** si "
        "chombo tofauti cha kisheria kutoka kwako -- wewe na biashara ni "
        "kitu kimoja kisheria, ikimaanisha unabeba **dhima kamili "
        "binafsi** kwa madeni ya biashara, na unatumia **PIN yako "
        "binafsi ya KRA**. Ni haraka na nafuu kuanzisha, bila mtaji wa "
        "chini.\n\n**Kampuni ya kikomo** ni mtu tofauti wa kisheria "
        "kutoka kwa wamiliki wake -- dhima ya wanahisa kwa kawaida "
        "inakomea kwa kiasi walichowekeza katika hisa, na kampuni "
        "inapata **PIN yake tofauti ya KRA**, akaunti yake ya benki, na "
        "inaweza kuingia mikataba au kushtakiwa kwa jina lake. **Hakuna "
        "mtaji wa chini wa hisa unaotakiwa kisheria**, ingawa inahusisha "
        "makaratasi zaidi (Memorandum/Articles of Association, fomu za "
        "CR1/CR2/CR8) na uzingatiaji unaoendelea (marejesho ya kila "
        "mwaka kwa BRS) kuliko umiliki binafsi."
    ),
    "late_filing_penalty": (
        "Adhabu zinategemea marejesho gani na kama ni kuchelewa "
        "kuwasilisha au kuchelewa kulipa -- zote zinatumika kwa wajibu wa "
        "KRA chini ya **Sheria ya Taratibu za Kodi ya 2015**:\n\n"
        "- **Kodi ya mapato binafsi**: KES 2,000 kwa marejesho kwa "
        "kuchelewa kuwasilisha\n"
        "- **Kodi ya mapato ya kampuni/ubia**: KES 20,000 au 5% ya kodi "
        "inayodaiwa, kikubwa kati ya hivyo, kwa kuchelewa kuwasilisha; "
        "kuchelewa kulipa kunaongeza 5% zaidi pamoja na riba ya 1% kwa "
        "mwezi\n"
        "- **PAYE**: kuchelewa kuwasilisha ni 25% ya kodi inayodaiwa au "
        "KES 10,000, kikubwa kati ya hivyo\n"
        "- **VAT**: kuchelewa kuwasilisha ni 5% ya kodi inayodaiwa au "
        "KES 10,000, kikubwa kati ya hivyo\n\n"
        "**Hata kama huna mapato au mauzo, lazima uwasilishe marejesho "
        "ya nil** -- kutofanya hivyo kunasababisha adhabu ile ile ya "
        "moja kwa moja."
    ),
    "etims_general": (
        "**eTIMS** (electronic Tax Invoice Management System) ni mfumo "
        "wa KRA wa kutengeneza risiti/ankara za kielektroniki "
        "zinazokubalika kikodi -- unahitajika kwa biashara "
        "zilizosajiliwa VAT, na kwa mtu yeyote anayetaka gharama za "
        "biashara zikubaliwe kikodi, kwani KRA hukubali tu ankara "
        "zilizotengenezwa na eTIMS kama uthibitisho halali wa "
        "ununuzi.\n\n**Kwa nini biashara yako inahitaji**: bila ankara "
        "za eTIMS, gharama zako za biashara huenda zisikubaliwe kikodi, "
        "na wateja wanaohitaji kudai VAT yao wenyewe hawawezi kufanya "
        "hivyo kutoka ankara isiyo ya eTIMS. Kwa biashara ndogo, chaguo "
        "la bure la **eTIMS Lite** (kupitia tovuti au USSD *222#) ni "
        "njia rahisi zaidi ya kutii bila kununua vifaa."
    ),
    "sacco_vs_bank": (
        "**SACCOs** kwa kawaida hutoa mikopo nafuu zaidi kuliko benki za "
        "kibiashara -- mara nyingi **10-14% kwa mwaka**, mara nyingi "
        "ikiwekwa na mkutano mkuu wa mwaka wa SACCO badala ya kubadilika "
        "na Kiwango cha Benki Kuu. Mikopo ya **benki** za kibiashara "
        "kwa kawaida ni **13-20%+ kwa mwaka** na hubadilika na mabadiliko "
        "ya CBK.\n\n**Ubadilishanaji muhimu**: SACCOs zinahitaji "
        "**kujiunga na kujenga historia ya akiba kwanza** (kawaida "
        "miezi 3-6) kabla ya kukopa, na kiasi cha mkopo mara nyingi "
        "hukomea kama mara 3-5 ya akiba yako. Benki kwa kawaida "
        "hazihitaji uanachama/akiba ya awali na zinaweza kutoa kiasi "
        "kikubwa zaidi, hasa dhidi ya dhamana -- lakini kwa kiwango cha "
        "juu zaidi."
    ),
    "food_business_license": (
        "Biashara ya chakula (mkahawa, cafe, mkate, duka) inahitaji "
        "tabaka kadhaa, juu ya kibali chako cha kawaida cha kaunti "
        "(Single/Unified Business Permit):\n\n"
        "- **Cheti cha Afya/Usafi wa Chakula**: kinatolewa na idara ya "
        "afya ya kaunti, kikithibitisha majengo yako yanafikia viwango "
        "vya usafi -- kawaida KES 2,000-5,000, kinahitajika kabla ya "
        "kufungua\n"
        "- **Cheti cha Afya cha Mshughulikiaji wa Chakula**: kinahitajika "
        "kwa **kila mfanyakazi binafsi** anayeshughulikia chakula, "
        "kinapatikana baada ya uchunguzi wa afya (karibu KES 1,000 kwa "
        "mtu)\n"
        "- **Cheti cha Usalama wa Moto**: cha lazima kwa biashara zote, "
        "kinahitaji vizima moto na ukaguzi wa idara ya moto ya kaunti\n"
        "- **Mahususi kwa mikahawa**: usajili na **Tourism Regulatory "
        "Authority (TRA)** chini ya Sheria ya Utalii ya 2011, ikiwa "
        "unaendesha kama mkahawa\n\n"
        "Ikiwa unatengeneza au kufunga bidhaa za chakula kwa mauzo, "
        "utahitaji pia uthibitisho wa **KEBS** (Standardization Mark)."
    ),
    "agpo": (
        "**AGPO** (Access to Government Procurement Opportunities) "
        "inatenga **asilimia 30 ya manunuzi yote ya serikali** kwa "
        "makampuni yanayomilikiwa na vijana (miaka 18-35), wanawake, na "
        "watu wenye ulemavu, kila kundi likihitajika kuwa na **umiliki wa "
        "asilimia 70 angalau** na **uongozi wa asilimia 100** kutoka kwa "
        "kundi hilo.\n\nKujiandikisha: hakikisha biashara yako imesajiliwa "
        "kisheria (umiliki binafsi, ubia, au kampuni), kusanya cheti cha "
        "usajili, PIN/cheti cha VAT cha KRA, Tax Compliance Certificate, na "
        "(kwa makampuni) CR12 au (kwa ubia) hati ya ubia, kisha jisajili "
        "moja kwa moja kwenye **agpo.go.ke**. Ukisha idhinishwa, hadhi yako "
        "inatumika katika taasisi zote za manunuzi -- wizara za kitaifa, "
        "kaunti, na mashirika ya umma."
    ),
    "hustler_fund_business": (
        "Kiwango cha msingi cha **Personal Loan** (KES 500 hadi KES "
        "50,000, riba ya asilimia 8 kwa mwaka, kurejeshwa ndani ya siku "
        "14) kinaweza kutumika kwa biashara au mahitaji binafsi, "
        "kinapatikana kupitia *254# kwenye laini yako iliyosajiliwa ya **M-PESA** -- utahitaji ""**kitambulisho cha taifa cha Kenya** na SIM kadi inayotumika, hakuna dhamana inayohitajika. ""\n\nKwa biashara hasa, Hustler Fund "
        "pia inatoa mikopo ya **Biashara/Enterprise** kwa vikundi (chama, "
        "ushirika, au vikundi vilivyosajiliwa) na mikopo ya kiwango cha "
        "juu zaidi kwa **biashara zilizosajiliwa zenye PIN ya KRA**, zote "
        "kwa riba ile ile ya asilimia 8 kwa mwaka lakini kwa kiasi kikubwa "
        "zaidi na muda mrefu zaidi wa kurejesha kuliko kiwango cha "
        "binafsi. Kiwango chako cha mkopo na uwezo wa kufikia viwango vya "
        "juu zaidi hukua kwa historia thabiti ya kurejesha kwa wakati."
    ),
    "business_insurance": (
        "Sekta ya bima nchini Kenya inasimamiwa na **Insurance Regulatory "
        "Authority (IRA)**, si KRA -- KRA ni mamlaka ya kodi na haihusiki "
        "na bima kabisa.\n\n**Bima ya lazima, ikiwa una wafanyakazi**: "
        "bima chini ya **Work Injury Benefits Act (WIBA)**, inayolinda "
        "wafanyakazi wanaoumia au kulemazwa kazini -- hii ni ya lazima "
        "kisheria, si hiari. Ikiwa biashara yako inatumia gari lolote, "
        "**bima ya dhima ya mtu wa tatu ya gari** pia ni ya "
        "lazima.\n\n**Bima za hiari zinazofaa kuzingatiwa**: bima ya "
        "dhima ya umma (inashughulikia jeraha kwa wateja/wageni katika "
        "majengo yako), bima ya mali/moto (inashughulikia bidhaa, vifaa, "
        "na majengo yako), na bima ya usumbufu wa biashara (inashughulikia "
        "mapato yaliyopotea ikiwa utalazimika kufunga kwa muda, kwa "
        "mfano baada ya moto).\n\nMaelezo ya bima, vizuizi, na bei "
        "hutofautiana sana kwa kampuni ya bima -- thibitisha maelezo na "
        "**kampuni ya bima au wakala aliyeidhinishwa** (angalia orodha ya "
        "IRA ya watoa huduma walioidhinishwa kwenye ira.go.ke), si KRA."
    ),
}


TOPIC_KEYWORDS = {
    "nssf_penalty": ["nssf penalty", "late nssf", "nssf late payment", "penalty for late nssf", "nssf fine", "adhabu ya nssf", "faini ya nssf kuchelewa"],
    "mpesa_paybill_till": ["paybill", "till number", "buy goods till", "set up paybill", "mpesa business", "namba ya paybill", "namba ya till", "kuweka paybill"],
    "nssf_registration": ["register my business and employees", "nssf registration", "register for nssf", "register my employees for nssf", "kusajili wafanyakazi nssf", "kujisajili nssf"],
    "nssf": ["nssf", "national social security fund"],
    "maternity_paternity_leave": ["maternity leave", "paternity leave", "maternity leave entitlement", "likizo ya uzazi", "likizo ya baba"],
    "leave": ["annual leave", "leave days", "likizo ya mwaka", "siku za likizo", "annual leave entitlement"],
    "capital": ["minimum share capital", "share capital requirement", "mtaji wa chini", "mtaji unaohitajika"],
    "yedf": ["yedf", "youth enterprise development fund", "rausha", "inua loan", "vuka loan", "mfuko wa vijana", "mkopo wa yedf"],
    "hustler_fund_business": ["hustler fund business", "hustler fund for my business", "hustler fund biashara loan", "business tier hustler fund", "hustler fund enterprise loan", "personal loan and business loan", "hustler fund personal loan and business", "difference between the hustler fund", "apply for the hustler fund", "hustler fund and what are the eligibility", "eligibility requirements for the hustler fund", "mkopo kutoka hustler fund", "kupata mkopo kutoka hustler fund", "hustler fund na ninahitaji", "ninahitaji nini kustahili"],
    "loan": ["apply for a loan", "apply for financing", "get a loan", "startup loan", "hustler fund", "loan to start", "mkopo wa biashara", "jinsi ya kupata mkopo", "kupata mkopo wa kuanzisha"],
    "sole_prop_to_llc": ["transition into a limited", "convert my sole proprietorship", "converting sole proprietorship", "convert a sole proprietorship", "sole proprietorship into a limited", "sole proprietorship to a limited", "convert business name to company", "business name to limited company", "sole prop to llc", "sole proprietorship to llc", "kubadilisha biashara kuwa kampuni", "kutoka umiliki binafsi kwenda kampuni"],
    "kra_pin": ["how do i get a kra pin", "kra pin registration", "apply for kra pin", "get a kra pin", "kra pin for my business", "namba ya pin ya kra", "kupata pin ya kra", "jinsi ya kupata pin"],
    "vat": ["vat registration", "vat threshold", "register for vat", "required to register for vat", "do i need to register for vat", "vat registration threshold", "kusajili vat", "ni lini nasajili vat", "kikomo cha vat", "vat rate", "rate of vat", "how much is vat", "kiwango cha vat", "asilimia ya vat"],
    "termination": ["terminate an employee", "termination", "dismissal", "dismiss an employee", "redundancy", "fire an employee", "firing an employee", "kumfukuza mfanyakazi", "kuachisha kazi", "kufukuza mfanyakazi"],
    "food_business_license": ["food business need to operate", "licenses does a food business", "restaurant license kenya", "food business licenses", "licenses for a restaurant", "leseni ya mkahawa", "leseni ya biashara ya chakula", "leseni gani kwa biashara ya chakula"],
    "license": ["single business permit", "what license do i need", "what licence do i need", "trade license requirements", "leseni ya biashara", "kibali cha biashara", "ninahitaji leseni gani"],
    "turnover_tax": ["turnover tax", "tot rate", "tot threshold", "kodi ya mauzo", "kodi ya turnover"],
    "paye_bands": ["paye rate", "paye band", "paye tax rate", "income tax band", "income tax rate", "kiwango cha paye", "ushuru wa paye", "kodi ya mshahara"],
    "shif_rate": ["shif rate", "shif contribution", "shif percentage", "how much shif", "shif deduction", "contribute to shif", "employer shif", "shif employer", "pay to shif", "shif pay", "obligations to shif", "shif obligations", "obligations under shif", "kiwango cha shif", "mchango wa shif"],
    "housing_levy": ["housing levy", "affordable housing levy", "ahl rate", "housing levy rate", "ushuru wa nyumba", "levy ya nyumba"],
    "minimum_wage": ["minimum wage", "minimum salary", "lowest wage", "minimum pay", "mshahara wa chini kabisa", "kima cha chini cha mshahara"],
    "class_r_permit": ["class r permit", "eac permit", "east african community permit", "foreigner certificate", "alien card", "ugandan need to trade", "ugandan trader", "tanzanian trader", "rwandan trader", "burundian trader", "eac national", "east african citizen business", "foreign trader permit kenya"],
    "tcc_application": ["tax compliance certificate", "apply for tcc", "tcc application", "how to get tcc", "tax compliance certificate application", "cheti cha ulipaji kodi", "kupata tcc"],
    "probation_period": ["probation period", "probation length", "how long can probation", "maximum probation", "probation extension", "kipindi cha majaribio", "muda wa majaribio kazini"],
    "agpo": ["agpo", "government procurement opportunities", "government tenders for youth", "30% government procurement", "access to government procurement", "zabuni za serikali", "manunuzi ya serikali"],
    "employee_compliance_checklist": ["employee compliance", "statutory deductions", "legal documentation and statutory", "compliance under the kenyan employment act", "documentation and statutory deductions", "three permanent staff", "permanent staff members", "statutory deductions a small trading enterprise", "payroll obligations", "payroll requirements", "payroll compliance", "employer obligations", "obligations as an employer", "obligations of an employer", "employer responsibilities", "responsibilities as an employer", "first employee", "hire my first", "hiring my first", "hired my first", "mfanyakazi wa kwanza", "nikimwajiri", "kumwajiri mfanyakazi", "majukumu ya mwajiri", "wajibu wa mwajiri", "wajibu wangu kama mwajiri"],
    "compliance_software": ["compliance software", "accounting software", "payroll software", "tax software", "software to help", "software that will help", "software that can help", "software for my business", "any software"],
    "regulations_not_exhaustive": ["are those all the", "are these all the", "is that all the regulations", "is that all the requirements", "is that all i need", "is that everything i need"],
    "relocation_county": ["to another county", "to a different county", "to a new county", "switch my city", "switch my county", "city or state", "relocate my business to"],
    "barber_salon_taxes": ["relevant to being a barber", "relevant to a barber", "subject to as a barber", "taxes as a barber", "tax as a barber", "taxes for a barber", "taxes does a barber", "tax obligations for a barber", "tax obligations of a barber", "taxes as a hairdresser"],
    "sole_prop_llc_mistakes": ["mistakes for this transition", "mistakes when converting", "mistakes when transitioning", "mistakes in converting", "mistakes converting"],
    "wef": ["women enterprise fund", "wef loan", "tuinuke chama loan", "woman-owned business access", "woman-owned business fund", "women group loan kenya", "constituency women enterprise scheme", "mfuko wa wanawake", "mkopo wa wanawake"],
    "unified_business_permit": ["unified business permit", "ubp nairobi", "nairobi business permit", "leseni ya nairobi", "kibali cha biashara nairobi"],
    "pharmacy_license": ["pharmacy license", "chemist shop license", "poisons board", "pharmacy and poisons board", "open a pharmacy", "chemist shop kenya", "pharmacy need to operate", "chemist shop need to operate", "licenses does a pharmacy", "licenses does a chemist", "leseni ya duka la dawa", "kufungua duka la dawa"],
    "ca_license": ["communications authority", "ca license kenya", "telecommunications license kenya", "mamlaka ya mawasiliano", "leseni ya mawasiliano"],
    "keproba": ["keproba", "kenya export promotion", "export promotion and branding agency", "brand kenya agency", "usafirishaji nje ya nchi", "kuuza bidhaa nje"],
    "no_permit_penalty": ["without a county permit", "operate a business without", "without a permit", "penalty for operating without", "no business permit", "bila kibali cha kaunti", "adhabu ya kutokuwa na kibali"],
    "sole_prop_vs_limited": ["difference between a sole proprietorship", "sole proprietorship and a limited company", "sole proprietorship vs limited company", "sole proprietorship or a limited company", "tofauti kati ya umiliki binafsi na kampuni"],
    "late_filing_penalty": ["penalties for late filing", "late filing of tax returns", "penalty for late filing", "what happens if i file late", "late tax return penalty", "adhabu ya kuchelewa kuwasilisha", "kuchelewa kuwasilisha marejesho"],
    "etims_general": ["what is etims", "why does my business need etims", "why do i need etims", "etims ni nini", "kwa nini nahitaji etims"],
    "sacco_vs_bank": ["saccos offer loans differently", "sacco vs bank", "sacco or bank loan", "difference between sacco and bank", "saccos differently from commercial banks", "tofauti kati ya sacco na benki"],
    "business_insurance": ["insurance does a", "business insurance", "insurance for my business", "what insurance", "bima ya biashara", "bima gani", "nahitaji bima"],
    "registration": ["register a business name", "business name registration", "steps to register a business", "register a small business", "register a business in kenya", "how to register a business", "start a business in kenya", "steps to start a business", "kusajili biashara", "naweza kusajili biashara", "jinsi ya kusajili biashara", "kuanzisha biashara", "nataka kusajili"],
}


def get_canned_topic(query: str):
    """Return the topic key if the query matches a hard-verified topic with
    a canned answer, else None. Bypasses LLM generation entirely for these
    topics to guarantee zero fabrication.

    Checks exact substrings first, then falls back to a space-normalized
    comparison (spaces stripped from both query and keyword) to tolerate
    common spacing variants -- e.g. someone typing "ku sajili" instead of
    "kusajili" for a Kiswahili compound verb form."""
    query_lower = query.lower()
    query_nospace = query_lower.replace(" ", "")
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in query_lower for kw in keywords):
            return topic
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw.replace(" ", "") in query_nospace for kw in keywords):
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
    import re as _re
    _followup = _re.search(r"\b(those|these|them|they|this category|this type of business|the same|the above)\b", current_query, _re.I)
    if len(current_query.split()) > VAGUE_WORD_THRESHOLD and not _followup:
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
        "je", "ninataka", "naomba", "ngapi", "nataka",
        "kodi", "usajili", "mfanyakazi", "mshahara", "kampuni", "sheria",
        "ushuru", "mwezi", "kiasi", "leseni", "ada", "pesa", "mkopo",
        "kibali", "ruhusa", "malipo", "faida", "huduma", "mwaka",
        "lini", "ninapaswa", "kusajili", "kiwango", "nifanyeje", "nikimwajiri",
        "mwajiri", "asilimia", "mchango", "michango", "jinsi", "ninaweza",
        "naweza", "nchini", "tafadhali",
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
