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
        '**Minimum share capital for a private limited company in Kenya**:\n'
        '\n'
        '- There is **no legally mandated minimum** share capital requirement\n'
        '- Most companies register with a nominal capital (commonly KES 100,000, though this is a convention, not a legal floor)\n'
        '- No stamp duty is charged on the initial nominal share capital at registration (exempt since Legal Notice 60 of 2016); stamp duty of **1%** applies if you later **increase** the share capital'
    ),
    "yedf": (
        '**Youth Enterprise Development Fund (YEDF)**:\n'
        '\n'
        "- **Eligibility**: age 18-34 (that is, under 35, the Constitution's definition of youth, Article 260)\n"
        '- **Vuka loan**: for youth who want to start or expand a business -- up to **KES 5,000,000** at **8%** interest, available to individuals, companies and partnerships\n'
        '- **Other loans**: YEDF also offers other products, such as the Agri-Biz loan for agribusiness. Products and amounts change, so check the current list at youthfund.go.ke\n'
        '\n'
        'Apply at a YEDF office at your county headquarters, or start at youthfund.go.ke.'
    ),
    "loan": (
        '**Startup loan options in Kenya**:\n'
        '\n'
        '1. **YEDF** (for youth aged 18-34) -- products include the **Vuka loan** (up to KES 5,000,000 at 8%) and the Agri-Biz loan; check the current list at youthfund.go.ke\n'
        '2. **Hustler Fund** -- dial ***254#**; the Personal Finance loan gives KES 500-50,000 at interest capped at 8% per annum, with no collateral\n'
        "3. **Women Enterprise Fund** -- Tuinuke loans for registered women's groups; see wef.go.ke\n"
        '4. **SACCOs** -- lend only to members, based on their savings\n'
        '5. **Commercial banks** -- usually require a registered business, financial records, and collateral for larger amounts'
    ),
    "registration": (
        '**Registering a business name in Kenya** (Business Registration Service, BRS):\n'
        '\n'
        '**You need**: a copy of your **national ID** (or passport if you are not Kenyan), your **KRA PIN**, and a recent passport-size photo.\n'
        '\n'
        '1. Log in to the BRS portal on eCitizen (brsv2.ecitizen.go.ke) and choose **Companies Registry Services**, then **Make Application** and **Registration of a Business Name**\n'
        '2. Enter **three to five** preferred business names, in order of priority, for review and approval\n'
        '3. Fill in the details asked for, then sign the auto-generated registration form, scan it and upload it\n'
        '4. Submit and pay **KES 950** -- the payment prompt comes to your phone\n'
        '\n'
        'For help, the BRS line is 011 112 7000.'
    ),
    "kra_pin": (
        '**Getting a KRA PIN** (free):\n'
        '\n'
        '1. Go to iTax at **itax.kra.go.ke** and choose **New PIN Registration**\n'
        '2. Choose **Individual**, then fill in your national ID number and date of birth (your name fills in automatically), plus your address, phone number and email address\n'
        '3. Verify your email with the one-time code (OTP) sent to it, submit, and download your **PIN certificate** -- the PIN is 11 characters, starting with A\n'
        '\n'
        "You'll need this PIN to register a business name and before registering for VAT, PAYE, or any other tax obligation."
    ),
    "vat": (
        '**VAT registration threshold in Kenya**:\n'
        '\n'
        '- Mandatory once your annual taxable turnover reaches **KES 5,000,000 (5 million)** or more\n'
        '- The standard VAT rate is **16%**, charged on your taxable sales\n'
        '- Register via iTax (itax.kra.go.ke)'
    ),
    "vat_penalty": (
        "**Penalties for late VAT filing and payment in Kenya**:\n\n"
        "- **Late filing of a VAT return**: 5% of the tax due or KES 10,000, whichever is higher\n"
        "- **Late payment of VAT**: 5% of the tax due, plus interest of 1% per month\n\n"
        "File and pay through iTax (itax.kra.go.ke)."
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
        '**PAYE tax bands in Kenya** are progressive, applied monthly (Finance Act 2023):\n'
        '\n'
        '- **10%** on the first KES 24,000\n'
        '- **25%** on the next KES 8,333 (KES 24,001-32,333)\n'
        '- **30%** on KES 32,334-500,000\n'
        '- **32.5%** on KES 500,001-800,000\n'
        '- **35%** above KES 800,000\n'
        '\n'
        'Every resident employee is entitled to a **personal relief of KES 2,400 per month** (KES 28,800 per year), subtracted from the calculated tax. Non-residents do not qualify for this relief. PAYE is calculated on taxable income after NSSF, SHIF, and Affordable Housing Levy deductions.\n'
        '\n'
        "**Remittance deadline**: PAYE deducted from a given month's salaries must be remitted to KRA by the **9th day of the following month** (e.g. January's PAYE is due by 9th February), filed via the iTax P10 return. **Late filing** of the PAYE return: the higher of **25%** of the tax due or **KES 10,000**. **Late payment**: **5%** of the tax due, plus interest of **1% per month** until paid in full."
    ),
    "paye_remit": (
        "**How an employer pays PAYE to KRA**:\n\n"
        "- Deduct PAYE from each employee's salary at the current individual income tax rates\n"
        "- File the PAYE return on iTax (itax.kra.go.ke): download the Excel return, fill and validate it, then upload the zipped file\n"
        "- Remit the tax deducted **on or before the 9th day of the following month**\n"
        "- **Late filing**: 25% of the tax due or KES 10,000, whichever is higher\n"
        "- **Late payment**: 5% of the tax due, plus interest of 1% per month until paid in full"
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
        '**Affordable Housing Levy (AHL)** in Kenya:\n'
        '\n'
        '- **1.5%** of gross salary from the employee\n'
        '- **1.5%** of gross salary matched by the employer\n'
        '- **Total: 3%** of gross salary per employee, per month\n'
        '\n'
        'There is **no minimum income threshold** -- it applies to all gross salaried employees. Informal-sector and self-employed contributors pay 1.5% of declared income with no employer match, registering via the AHL/Boma Yangu portal. Remittance is due by the 9th working day after month-end via KRA iTax. The levy deducted from salary is an allowable deduction when calculating PAYE. Late remittance carries a 3% per month penalty on the unpaid amount.'
    ),
    "minimum_wage": (
        '**Kenya does not have a single national minimum wage.** Rates are set by occupation, sector, and geographic zone under periodic Regulation of Wages Orders (Labour Institutions Act), typically revised around Labour Day (1st May).\n'
        '\n'
        'As a reference point: the general (unskilled) labourer minimum in Nairobi, Mombasa, Kisumu, Nakuru, and Eldoret was set at **KES 18,047.40 per month** (exclusive of housing allowance) under the May 2026 Wage Order (Legal Notices No. 95 and 96), with lower rates in other zones. Skilled occupations (e.g. drivers, artisans, cashiers) and sector-specific roles (agricultural, security, domestic work) have their own, generally higher, statutory minimums.\n'
        '\n'
        'Because rates vary by role and location and are revised periodically, confirm the exact current figure for your specific occupation and zone via the Ministry of Labour and Social Protection or the current Kenya Gazette Wage Order, rather than relying on a single number.'
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
        '**Getting an M-PESA Paybill or Till number** -- apply to **Safaricom**, not a bank:\n'
        '\n'
        "- **Till Number (Buy Goods)**: for retail and point-of-sale (shops, restaurants, kiosks); the merchant pays a transaction fee set in Safaricom's published tariff, which changes from time to time\n"
        '- **Paybill Number**: for collections that need an account or reference number (rent, school fees, utilities, subscriptions)\n'
        '\n'
        "**How to apply**: all applications go through Safaricom's online portal, **m-pesaforbusiness.co.ke/apply**, and only the business owner (or an aggregator) can apply. Each business type -- sole proprietor, partnership or company -- has its own list of required documents shown on the portal. For a Paybill you also give a bank account, and funds can only be withdrawn to that account. Safaricom says applications are processed within 24 hours of complete documents; track the status on the portal, and the number's details are sent to you once it is active. Check the current charges on Safaricom's website before you choose."
    ),
    "class_r_permit": (
        'Go to the **Kenya eFNS portal** on eCitizen and apply for a **Class R Permit** -- the permit for East African Community nationals (Burundi, DR Congo, Rwanda, South Sudan, Tanzania, Uganda) to live, work, trade or run a business in Kenya. **The permit is free**: the government has confirmed that no one should charge an EAC citizen for it. If you stay beyond 90 days you must also register as a foreign national, which is a separate process -- check its current fee on eFNS.\n'
        '\n'
        'Typical documents: valid passport, cover letter, KRA PIN if doing business, and a police clearance certificate (required for small-scale traders). Apply online, then submit the completed forms at an Immigration office (Nyayo House, Nairobi).'
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
        "youth (aged 18-34, that is, under 35), women, and persons with disabilities, each "
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
        'The Hustler Fund **Personal Finance loan** gives **KES 500 to KES 50,000**, depending on your credit score, at interest **capped at 8% per annum** (pro-rated), repayable in **14 days**. It can be used for business or personal needs, and no collateral is required.\n'
        '\n'
        '**To access it**: dial ***254#** on your registered line. You need to be a Kenyan citizen aged 18 or above, with a valid national ID, an active mobile money account (M-PESA, Airtel Money or T-Kash), and a SIM card that has been active for at least 90 days.\n'
        '\n'
        'The Fund has also announced Micro, SME and Start-up loan products; check *254# or the official Hustler Fund channels for what is currently available. Your loan limit depends on your scoring.'
    ),
    "sole_prop_to_llc": (
        'You can move a sole proprietorship (a registered business name) to a private limited company on the Business Registration Service portal (brsv2.ecitizen.go.ke) in **two linked steps**:\n'
        '\n'
        '1. **Cease the business name**: under your business, choose Maintain -> Cessation of Business Name, select "convert" as the reason, and upload the signed **Form BN 6**. The fee is **KES 250**.\n'
        "2. **Convert**: once the cessation is approved, an option to start the conversion appears. Choose private limited company, fill in the new company's details, submit and pay the registration fee.\n"
        '\n'
        "You can apply to keep the same name with 'Limited' or 'Ltd' added, subject to BRS approval.\n"
        '\n'
        '**KRA PIN**: your sole proprietorship used your **personal KRA PIN**. The company is a separate taxpayer with its **own KRA PIN**, issued with its incorporation documents -- and every director and shareholder must already have their own individual KRA PIN.\n'
        '\n'
        '**Fees**: expect two government charges -- KES 250 for the cessation and the company registration fee. Check the current fees on the BRS portal before you apply, since they change. There is **no legal minimum share capital**.'
    ),
    "wef": (
        'The **Women Enterprise Fund (WEF)** is a government fund that lends to Kenyan women -- separate from YEDF (for youth) and the Hustler Fund.\n'
        '\n'
        "**Tuinuke loan** (for women's groups):\n"
        '- The group must be a registered self-help group of **10-30 women**, all aged 18 or above\n'
        '- Registered with the Department of Social Services or the Micro and Small Enterprises Authority (MSEA) for **at least three months**\n'
        "- Has an active **commercial bank account**, and members complete WEF's financial literacy training\n"
        '- Each member may belong to only one WEF-funded group\n'
        '- Loans grow by cycle: **KES 100,000** (6 months), **200,000** (9 months), **350,000** (12 months), **500,000** (15 months), **750,000** (18 months)\n'
        '- A one-time **administrative fee of 6%** is charged upfront\n'
        '\n'
        'WEF also has products for individual women-owned businesses; check the current list and apply at a WEF office or at wef.go.ke.'
    ),
    "unified_business_permit": (
        'In Nairobi County specifically, this is the **Unified Business Permit (UBP)** -- a single annual license that bundles what used to be several separate approvals (trade license, fire inspection, food/health certificate, advertisement/signage permit) into one application. Apply via the **NairobiPay self-service portal (nairobiservices.go.ke)**, dial ***647#**, or visit City Hall Annex in person.\n'
        '\n'
        "The fee depends on your business category and size, and is set by the county's Finance Act -- confirm your exact category's fee on the portal before you pay. It runs on a **January-December annual cycle**; the permit is renewed every year; check the portal for the current deadline, since late payment attracts penalties. Other counties issue their own single business permit through their own systems -- check with your county."
    ),
    "pharmacy_license": (
        'Operating a pharmacy or chemist shop requires licensing from the **Pharmacy and Poisons Board (PPB)**, the national medicines regulator under the Pharmacy and Poisons Act (Cap 244) -- this is in addition to, not instead of, your county Single Business Permit (the fee varies by county).\n'
        '\n'
        "**Key requirement**: a pharmacy must be owned and run under a registered pharmacist or enrolled pharmaceutical technologist. If you register it as a company, the superintendent pharmacist must be the majority shareholder -- you can't own or control a pharmacy purely as a non-pharmacist investor. The designated superintendent pharmacist also needs their own annual practicing license from PPB.\n"
        '\n'
        '**Process**: register your premises with PPB, then pass a premises inspection covering proper shelving, ventilation, a dispensing area separate from the sales counter, a lockable poisons cabinet, a refrigerator for cold-chain products, and Green Cross signage. Licenses are issued after a successful inspection and must be renewed annually (all PPB licenses expire December 31). Confirm the current ownership and premises requirements with PPB before you invest.'
    ),
    "ca_license": (
        "Not every tech startup needs this -- the **Communications Authority of Kenya (CA)** licenses telecommunications, broadcasting, postal/courier services and related equipment, not general software or app businesses. If your startup only builds an app or website, without running telecom infrastructure or providing regulated network or content services, you likely don't need a CA licence.\n"
        '\n'
        "If you do fall into a regulated category, CA's Unified Licensing Framework includes **Network Facilities Provider** (infrastructure), **Applications Service Provider** and **Content Service Provider** licences, plus separate licences for broadcasting, postal/courier services and equipment type approval. A foreign-owned licensee must issue **at least 20% of its shares to Kenyans** within three years of getting the licence. Confirm the application requirements, fees and processing times with CA (ca.go.ke) before you apply."
    ),
    "nssf_registration": (
        "**As an employer**: every employer who engages **one or more employees** must register with NSSF as a contributing employer. On the NSSF Self Service portal (selfservice.nssf.or.ke), choose **'Employer Registration'** if you have no NSSF registration number yet and complete the form. Then print the application notification and take it to your nearest NSSF office for certification; the office gives you a PIN key to activate your online account.\n"
        '\n'
        '**For your employees**: you must also make sure every employee is promptly registered as an NSSF member.\n'
        '\n'
        '**After registering**: deduct and remit contributions, and submit monthly returns, by the **9th day of the following month**. An employer who fails to meet these obligations commits an offence.'
    ),
    "keproba": (
        "**KEPROBA** (Kenya Export Promotion and Branding Agency) is a state corporation (formed 2019, merging the former Export Promotion Council and Brand Kenya Board) that supports Kenyan exporters and promotes 'Brand Kenya' internationally.\n"
        '\n'
        "**What it actually offers**: guidance on export procedures and documentation, market intelligence and market-entry requirements for target countries, capacity-building through export training and coaching, organized trade missions and trade fair participation, and support with **product development and branding** -- including packaging, labelling, and brand positioning to help your goods resonate with international buyers. It particularly prioritizes bringing youth- and women-led producer groups into the export process. Reach out through KEPROBA's offices or makeitkenya.go.ke to access these services.\n"
        '\n'
        "Note: the Investment and Export Promotion Authority Bill, 2026 proposes merging KEPROBA with the Kenya Investment Authority, so check the agency's current name and contacts before you go."
    ),
    "no_permit_penalty": (
        'Operating without a valid county business permit is illegal in Kenya. Each county sets its own permit rules and penalties in its own laws.\n'
        '\n'
        '**What can happen**:\n'
        '- **Closure or seizure of goods**: county laws can let licensing officers close an unlicensed business -- in Kiambu, for example, a licensing officer can order closure of the business or seizure of goods, and the penalty is **20% of the licence fee for every month** of default\n'
        '- **A fine, imprisonment, or both** on conviction -- in Nairobi, a person who fails to renew a licence and continues to operate commits an offence, with a fine of up to **KES 50,000**, imprisonment of up to **3 months**, or both\n'
        "- Other counties set their own amounts -- confirm your county's penalty schedule\n"
        '\n'
        'Get your permit before you start operating, and renew it on time.'
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
    "compliance_software": (
        "There isn't one package you are required to use, but these are the official systems most Kenyan MSMEs need for compliance:\n"
        '\n'
        "- **eTIMS** (KRA's electronic tax invoice system): required for all persons carrying on business, unless exempted -- not only VAT-registered businesses -- and needed for your business expenses to be tax-deductible. The free **eTIMS Lite** option is the simplest way for a small business to comply without buying equipment.\n"
        "- **KRA iTax (itax.kra.go.ke)**: KRA's portal for filing returns, including the monthly PAYE return (P10) if you have employees.\n"
        '- **NSSF Employer Self-Service portal (selfservice.nssf.or.ke)**: register as an employer and manage your NSSF obligations if you employ staff.\n'
        '\n'
        "If you also want accounting or payroll software on top of these, I can't recommend a specific product, but check that it calculates the current PAYE bands, NSSF tiers, SHIF (2.75% of gross pay) and Housing Levy (1.5% each for employee and employer) correctly, and that it can issue eTIMS-compliant invoices."
    ),
    "regulations_not_exhaustive": (
        "No -- there isn't a single complete list, because what applies depends on your business type, your turnover and whether you employ people. These are the baseline items that apply to most Kenyan businesses:\n"
        '\n'
        '- **Registration**: register your business name (eCitizen/BRS) and get a KRA PIN\n'
        '- **County permit**: a single business permit from your county government -- the category and fee vary by county\n'
        '- **Income tax regime**: Turnover Tax (1.5% of gross sales) if your annual turnover is between KES 1,000,000 and KES 25,000,000; VAT registration once your annual taxable turnover reaches KES 5,000,000\n'
        "- **eTIMS**: KRA's e-invoicing system, required for all persons carrying on business unless exempted, and needed for your expenses to be tax-deductible (the free eTIMS Lite option is the simplest for small businesses)\n"
        '- **If you employ people**: NSSF (6% employee + 6% employer), PAYE, SHIF (2.75% of gross pay) and the Housing Levy (1.5% employee + 1.5% employer), plus written contracts and leave records -- ask about your "payroll obligations" for the full list\n'
        '\n'
        "Some sectors also need their own licences (for example food businesses or pharmacies). Tell me your specific business type and I'll give you the requirements I can verify for it."
    ),
    "relocation_county": (
        'Kenya has counties rather than states, and moving your business from one county to another mostly changes your **county licensing**, not your national taxes.\n'
        '\n'
        "- **National taxes stay the same**: Turnover Tax (1.5% of gross sales for turnover between KES 1,000,000 and KES 25,000,000), VAT (once taxable turnover reaches KES 5,000,000) and, if you employ staff, PAYE, NSSF, SHIF and the Housing Levy are set nationally and collected through KRA. They don't depend on which county you operate from.\n"
        "- **County licensing changes**: a single business permit is issued by each county government, and the category and fee vary by county. In your new county you will need a permit from that county's business licensing office.\n"
        '\n'
        'Confirm the exact category and fee with your new county.'
    ),
    "barber_salon_taxes": 'Tax obligations for a barber or salon business in Kenya depend on your annual turnover and on whether you employ staff -- not on the trade itself:\n\n- **Turnover Tax (TOT)**: 1.5% of gross sales if your annual turnover is more than KES 1,000,000 but does not exceed KES 25,000,000. It is charged on gross sales with **no expense deductions**. For example, KES 2,000,000 of annual sales means KES 30,000 of TOT (2,000,000 x 1.5%). Below KES 1,000,000 you are exempt from TOT.\n- **VAT**: if your turnover reaches KES 5,000,000 and you deal in vatable supplies, you must also register for VAT.\n- **If you employ staff**: PAYE (bands from 10% to 35%, less KES 2,400 monthly personal relief), NSSF (6% employee + 6% employer), SHIF (2.75% of gross pay) and the Housing Levy (1.5% employee + 1.5% employer) -- ask about your "payroll obligations" for the full list.\n- **County permit**: a single business permit from your county government; the category and fee vary by county.\n\nWhere you operate affects your county permit and fees, but the national tax rules above are the same in every county. Confirm your specific position via iTax (itax.kra.go.ke).',
    "sole_prop_llc_mistakes": (
        'Common mistakes when moving from a sole proprietorship to a limited company:\n'
        '\n'
        '- **Expecting a one-click conversion**: on the Business Registration Service portal (brsv2.ecitizen.go.ke) it is two linked steps. First cease your business name, choosing "convert" as the reason and uploading the signed **Form BN 6** (fee **KES 250**). Only after the cessation is approved does the option to convert to a company appear; you then fill in the new company\'s details and pay the registration fee.\n'
        "- **Carrying over your personal KRA PIN**: the company is a separate taxpayer with its own KRA PIN, issued with its incorporation documents. Don't file the company's taxes under your personal PIN.\n"
        '- **Starting before everyone has a PIN**: every director and shareholder must already have their own individual KRA PIN before the company can be registered.\n'
        '- **Budgeting for only one charge**: expect two separate government charges -- the business name cessation (KES 250) and the company registration.\n'
        '- **Delaying because of share capital**: there is no legal minimum share capital requirement.\n'
        '\n'
        'Confirm the current steps and fees on the BRS portal before you file.'
    ),
    "etims_general": (
        "**eTIMS** (electronic Tax Invoice Management System) is KRA's system for generating tax-compliant, verifiable electronic invoices/receipts -- it's required for all persons carrying on business unless exempted (Tax Procedures (Electronic Tax Invoice) Regulations, 2024), and KRA only accepts eTIMS-generated invoices as valid proof of purchase for deducting business expenses.\n"
        '\n'
        "**Why your business needs it**: without eTIMS invoices, your business expenses may not be deductible for tax purposes, and customers who need to claim their own input VAT or expense deductions can't do so from a non-eTIMS invoice -- making it harder to sell to other VAT-registered businesses.\n"
        '\n'
        'For smaller businesses, the free **eTIMS Lite** option on the KRA eTIMS portal is the simplest way to comply without buying equipment. Non-compliance carries a penalty of **two times the tax due** (Tax Procedures (Electronic Tax Invoice) Regulations, 2024).'
    ),
    "sacco_vs_bank": (
        '**SACCO loans vs bank loans in Kenya**:\n'
        '\n'
        '- **Who can borrow**: a SACCO lends only to its **members**; a bank lends to any customer who qualifies\n'
        '- **What secures the loan**: SACCO loans are based on your **savings with the SACCO**; banks rely more on collateral and credit checks\n'
        '- **Interest**: each SACCO and each bank sets its own loan rate. Ask for the **annual interest rate** and whether it is charged on a **reducing balance or a flat rate** -- at the same rate, a flat rate costs more\n'
        '- **Before borrowing from a SACCO**: you usually need to join and build savings first\n'
        '- **Dividends**: SACCO members can earn dividends on their shares and interest on deposits, which a bank loan does not offer\n'
        '- **Check the SACCO is licensed** on the SASRA website (sasra.go.ke)'
    ),
    "food_business_license": (
        'A food business (restaurant, cafe, bakery, shop) needs several layers, on top of your standard county business permit. **In Nairobi**, the Unified Business Permit combines the business, fire, food, health and advertising licences into one application, so the premises health and fire approvals below come with it; in other counties, check whether they are separate:\n'
        '\n'
        '- **Health/Food Hygiene Certificate**: issued by your county health department, confirming your premises meet hygiene standards, required before opening (the fee varies by county)\n'
        "- **Food Handler's Health Certificate**: required for **every individual employee** who handles food, obtained after a medical check-up\n"
        '- **Fire Safety Certificate**: mandatory for all businesses, requiring fire extinguishers and a county fire department inspection, renewed annually\n'
        '- **Restaurant-specific**: registration with the **Tourism Regulatory Authority (TRA)** under the Tourism Act 2011, if you operate as a restaurant\n'
        '\n'
        "If you manufacture or package food products for sale (not just serve food on-site), you'll also need **KEBS** certification (Standardization Mark) specific to packaged/processed goods."
    ),
    "employee_compliance_checklist": (
        "For a trading enterprise with permanent staff, here's what to maintain:\n"
        '\n'
        '**Employment contracts**: a written contract for any employment of three months or more (Employment Act, Section 9), covering start date, job description, salary, working hours, and leave entitlement.\n'
        '\n'
        '**Statutory deductions, per employee, per month**:\n'
        '- **NSSF**: 6% employee + 6% employer (matched), Tier I up to KES 9,000, Tier II up to KES 108,000\n'
        '- **PAYE**: progressive bands from 10% to 35%, less KES 2,400 personal relief\n'
        '- **SHIF** (Social Health Insurance Fund -- this replaced NHIF in October 2024): 2.75% of gross pay, employee-side only, no cap\n'
        '- **Housing Levy**: 1.5% employee + 1.5% employer, no minimum income threshold\n'
        '\n'
        '**Leave records**: minimum 21 working days of annual leave per 12 months of service (Employment Act Section 28).\n'
        '\n'
        "**Payroll records**: document each employee's monthly salary and all deductions above, and remit them on time -- NSSF and PAYE are due by the 9th of the following month, the Housing Levy by the 9th working day after month-end (declared on the PAYE return), and you should confirm the SHIF due date with the Social Health Authority. Keep these records available for inspection, and keep each employee's written contract and particulars for five years after their employment ends (Employment Act)."
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
    'start_business': (
        '**Starting a small business in Kenya** -- the basic steps:\n'
        '\n'
        '1. **Get a KRA PIN** (free, on iTax at itax.kra.go.ke).\n'
        '2. **Register your business name** on eCitizen through the Business Registration Service (BRS), with your national ID and KRA PIN, and pay the KES 950 fee. If you want a limited company instead, ask about "sole proprietorship vs limited company".\n'
        '3. **Get a single business permit from your county government** before you start operating -- the category and fee vary by county (in Nairobi it is the Unified Business Permit).\n'
        '4. **Sector licences**: some businesses also need their own licence, for example food businesses or pharmacies.\n'
        '5. **Tax**: if your annual turnover is above KES 1,000,000 and up to KES 25,000,000 you pay Turnover Tax (1.5% of gross sales); register for VAT once taxable turnover reaches KES 5,000,000. eTIMS invoicing applies to all persons carrying on business unless exempted.\n'
        '6. **If you employ people**: register as an employer with NSSF, and deduct PAYE, NSSF, SHIF (which replaced NHIF in October 2024) and the Housing Levy.\n'
        '\n'
        'So yes -- register and get your county permit before you start operating; operating without a county permit is illegal. Ask about any step for the details.'
    ),
    'afcfta': (
        '**Exporting to other African countries under the AfCFTA** (African Continental Free Trade Area):\n'
        '\n'
        "The AfCFTA was established in 2018 to create a single continental market of the 55 African Union member states. To export at the lower AfCFTA tariffs, your goods need an **AfCFTA certificate of origin**. In Kenya it is issued by **KRA's Customs & Border Control Department**.\n"
        '\n'
        '1. **Register as an exporter** with KRA Customs: fill in the registration form at a Rules of Origin office (Nairobi, Mombasa, Nakuru, Eldoret or Kisumu), with your business registration certificate, KRA PIN and relevant business licences\n'
        '2. KRA checks that your goods meet the AfCFTA **rules of origin** (Annex 2 to the Protocol on Trade in Goods) before approving you\n'
        '3. Once approved you get a reference number, and you can buy certificates of origin at **USD 3** each\n'
        '\n'
        'For export guidance, market information and trade fairs, ask about **KEPROBA**.'
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
        '**Mtaji wa chini wa hisa kwa kampuni binafsi ya dhima ndogo nchini Kenya**:\n'
        '\n'
        '- **Hakuna** mtaji wa chini wa hisa unaotakiwa kisheria\n'
        '- Kampuni nyingi husajiliwa na mtaji wa kawaida (mara nyingi KES 100,000, ingawa hii ni desturi tu, si kiwango cha kisheria)\n'
        '- Hakuna ushuru wa stempu kwa mtaji wa awali wa hisa wakati wa kusajili kampuni (msamaha tangu Tangazo la Kisheria Na. 60 la 2016); ushuru wa stempu wa **1%** hutozwa ukiongeza mtaji wa hisa baadaye'
    ),
    "yedf": (
        '**Mfuko wa Maendeleo ya Biashara za Vijana (YEDF)**:\n'
        '\n'
        '- **Sifa**: umri wa miaka 18-34 (yaani chini ya miaka 35, kwa mujibu wa Katiba, Kifungu cha 260)\n'
        '- **Mkopo wa Vuka**: kwa vijana wanaotaka kuanzisha au kupanua biashara -- hadi **KES 5,000,000** kwa riba ya **8%**, kwa watu binafsi, makampuni na ubia\n'
        '- **Mikopo mingine**: YEDF pia hutoa bidhaa nyingine, kama mkopo wa Agri-Biz kwa biashara za kilimo. Bidhaa na viwango hubadilika, hivyo angalia orodha ya sasa kwenye youthfund.go.ke\n'
        '\n'
        'Omba katika ofisi ya YEDF iliyo makao makuu ya kaunti yako, au anza kwenye youthfund.go.ke.'
    ),
    "loan": (
        '**Njia za mikopo ya kuanzisha biashara nchini Kenya**:\n'
        '\n'
        '1. **YEDF** (kwa vijana wa miaka 18-34) -- bidhaa ni pamoja na **mkopo wa Vuka** (hadi KES 5,000,000 kwa riba ya 8%) na mkopo wa Agri-Biz; angalia orodha ya sasa kwenye youthfund.go.ke\n'
        '2. **Hustler Fund** -- piga ***254#**; mkopo wa Personal Finance hutoa KES 500-50,000 kwa riba isiyozidi 8% kwa mwaka, bila dhamana\n'
        '3. **Women Enterprise Fund** -- mikopo ya Tuinuke kwa vikundi vya wanawake vilivyosajiliwa; tazama wef.go.ke\n'
        '4. **SACCO** -- hukopesha wanachama pekee, kulingana na akiba yao\n'
        '5. **Benki za biashara** -- kwa kawaida huhitaji biashara iliyosajiliwa, rekodi za fedha, na dhamana kwa kiasi kikubwa'
    ),
    "registration": (
        '**Kusajili jina la biashara nchini Kenya** (Huduma ya Usajili wa Biashara, BRS):\n'
        '\n'
        '**Unahitaji**: nakala ya **kitambulisho chako cha taifa** (au pasipoti kama si Mkenya), **PIN yako ya KRA**, na picha ya hivi karibuni ya ukubwa wa pasipoti.\n'
        '\n'
        '1. Ingia kwenye tovuti ya BRS kupitia eCitizen (brsv2.ecitizen.go.ke) na uchague **Companies Registry Services**, kisha **Make Application** na **Registration of a Business Name**\n'
        '2. Andika majina **matatu hadi matano** ya biashara unayopendelea, kwa mpangilio wa kipaumbele, ili yakaguliwe na kuidhinishwa\n'
        '3. Jaza taarifa zinazohitajika, kisha tia sahihi fomu ya usajili inayotolewa na mfumo, ichanganue (scan) na uipakie\n'
        '4. Wasilisha na ulipe **KES 950** -- ombi la malipo litakuja kwenye simu yako\n'
        '\n'
        'Kwa msaada, piga BRS: 011 112 7000.'
    ),
    "kra_pin": (
        '**Kupata PIN ya KRA** (bure):\n'
        '\n'
        '1. Nenda iTax kwenye **itax.kra.go.ke** na uchague **New PIN Registration**\n'
        '2. Chagua **Individual**, kisha jaza nambari ya kitambulisho chako cha taifa na tarehe ya kuzaliwa (jina lako hujazwa lenyewe), pamoja na anwani, nambari ya simu na barua pepe\n'
        '3. Thibitisha barua pepe yako kwa nambari ya siri ya mara moja (OTP) inayotumwa kwake, wasilisha, na upakue **cheti chako cha PIN** -- PIN ina herufi 11, ikianza na A\n'
        '\n'
        'Utahitaji PIN hii kusajili jina la biashara na kabla ya kujisajili kwa VAT, PAYE, au wajibu mwingine wowote wa kodi.'
    ),
    "vat": (
        '**Kiwango cha usajili wa VAT nchini Kenya**:\n'
        '\n'
        '- Ni lazima kujisajili mauzo yako ya mwaka yanayotozwa kodi yanapofikia **KES 5,000,000 (milioni 5)** au zaidi\n'
        '- Kiwango cha kawaida cha VAT ni **16%**, kinachotozwa kwenye mauzo yako yanayotozwa kodi\n'
        '- Jisajili kupitia iTax (itax.kra.go.ke)'
    ),
    "vat_penalty": (
        "**Adhabu za kuchelewa kuwasilisha na kulipa VAT nchini Kenya**:\n\n"
        "- **Kuchelewa kuwasilisha ritani ya VAT**: 5% ya kodi inayodaiwa au KES 10,000, kiasi kilicho kikubwa zaidi\n"
        "- **Kuchelewa kulipa VAT**: 5% ya kodi inayodaiwa, pamoja na riba ya 1% kwa mwezi\n\n"
        "Wasilisha na ulipe kupitia iTax (itax.kra.go.ke)."
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
        '**Viwango vya kodi ya PAYE nchini Kenya** hupanda kwa hatua, hutumika kila mwezi (Sheria ya Fedha 2023):\n'
        '\n'
        '- **10%** kwa KES 24,000 za kwanza\n'
        '- **25%** kwa KES 8,333 zinazofuata (KES 24,001-32,333)\n'
        '- **30%** kwa KES 32,334-500,000\n'
        '- **32.5%** kwa KES 500,001-800,000\n'
        '- **35%** zaidi ya KES 800,000\n'
        '\n'
        'Kila mfanyakazi mkazi anastahili **msamaha binafsi wa KES 2,400 kwa mwezi** (KES 28,800 kwa mwaka), unaotolewa kutoka kodi iliyokokotolewa. Wasio wakazi hawastahili msamaha huu. PAYE hukokotolewa kwa mapato yanayotozwa kodi baada ya makato ya NSSF, SHIF, na Ushuru wa Nyumba za Bei Nafuu.\n'
        '\n'
        '**Tarehe ya mwisho ya kuwasilisha**: PAYE iliyokatwa kwa mshahara wa mwezi fulani lazima iwasilishwe KRA ifikapo **tarehe 9 ya mwezi unaofuata** (mfano, PAYE ya Januari inatakiwa ifikapo tarehe 9 Februari), ikiwasilishwa kupitia fomu ya P10 kwenye iTax. **Kuchelewa kuwasilisha** ritani ya PAYE: **25%** ya kodi inayodaiwa au **KES 10,000**, kiasi kilicho kikubwa zaidi. **Kuchelewa kulipa**: **5%** ya kodi inayodaiwa, pamoja na riba ya **1% kwa mwezi** hadi ilipwe yote.'
    ),
    "paye_remit": (
        "**Jinsi mwajiri anavyolipa PAYE kwa KRA**:\n\n"
        "- Kata PAYE kutoka kwa mshahara wa kila mfanyakazi kwa viwango vya sasa vya Kodi ya Mapato\n"
        "- Wasilisha ritani ya PAYE kupitia iTax (itax.kra.go.ke): pakua fomu ya Excel, ijaze na uithibitishe, kisha upakie faili iliyobanwa (zip)\n"
        "- Lipa kodi iliyokatwa **kabla au tarehe 9 ya mwezi unaofuata**\n"
        "- **Kuchelewa kuwasilisha**: 25% ya kodi inayodaiwa au KES 10,000, kiasi kilicho kikubwa zaidi\n"
        "- **Kuchelewa kulipa**: 5% ya kodi inayodaiwa, pamoja na riba ya 1% kwa mwezi hadi ilipwe yote"
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
        '**Ushuru wa Nyumba za Bei Nafuu (AHL)** nchini Kenya:\n'
        '\n'
        '- **1.5%** ya mshahara wa jumla kutoka kwa mfanyakazi\n'
        '- **1.5%** ya mshahara wa jumla inayolingana kutoka kwa mwajiri\n'
        '- **Jumla: 3%** ya mshahara wa jumla kwa kila mfanyakazi, kila mwezi\n'
        '\n'
        '**Hakuna kiwango cha chini cha mapato** kinachotakiwa -- hutumika kwa wafanyakazi wote wenye mshahara wa jumla. Wachangiaji wa sekta isiyo rasmi na wanaojiajiri hulipa 1.5% ya mapato yaliyotangazwa bila mchango wa mwajiri, wakijisajili kupitia tovuti ya AHL/Boma Yangu. Malipo yanatakiwa kufikishwa ndani ya siku 9 za kazi baada ya mwisho wa mwezi kupitia iTax ya KRA. Ushuru unaokatwa kutoka kwa mshahara ni makato yanayoruhusiwa wakati wa kukokotoa PAYE. Kuchelewesha malipo kunatoza faini ya 3% kwa mwezi ya kiasi kisicholipwa.'
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
        '**Kupata nambari ya M-PESA Paybill au Till** -- omba kwa **Safaricom**, si benki:\n'
        '\n'
        '- **Nambari ya Till (Buy Goods)**: kwa biashara za rejareja na mauzo ya papo hapo (maduka, mikahawa, vibanda); mfanyabiashara hulipa ada ya muamala iliyowekwa kwenye viwango vilivyochapishwa na Safaricom, ambavyo hubadilika mara kwa mara\n'
        '- **Nambari ya Paybill**: kwa makusanyo yanayohitaji nambari ya akaunti au kumbukumbu (kodi ya nyumba, ada za shule, huduma, usajili)\n'
        '\n'
        '**Jinsi ya kuomba**: maombi yote hufanywa kupitia tovuti ya Safaricom, **m-pesaforbusiness.co.ke/apply**, na ni mmiliki wa biashara (au aggregator) pekee anayeweza kuomba. Kila aina ya biashara -- mtu binafsi, ubia au kampuni -- ina orodha yake ya nyaraka zinazohitajika inayoonyeshwa kwenye tovuti. Kwa Paybill pia unatoa akaunti ya benki, na pesa zinaweza kutolewa kwenda akaunti hiyo pekee. Safaricom inasema maombi hushughulikiwa ndani ya saa 24 baada ya nyaraka kamili; fuatilia hali ya ombi lako kwenye tovuti, na maelezo ya nambari hutumwa kwako ikishaanza kufanya kazi. Angalia ada za sasa kwenye tovuti ya Safaricom kabla ya kuchagua.'
    ),
    "sole_prop_to_llc": (
        'Unaweza kuhamisha biashara ya mtu binafsi (jina la biashara lililosajiliwa) kuwa kampuni ya kibinafsi (private limited company) kwenye tovuti ya Huduma ya Usajili wa Biashara (brsv2.ecitizen.go.ke) kwa **hatua mbili zinazofuatana**:\n'
        '\n'
        '1. **Sitisha jina la biashara**: chini ya biashara yako, chagua Maintain -> Cessation of Business Name, chagua "convert" kama sababu, na upakie **Fomu BN 6** iliyotiwa sahihi. Ada ni **KES 250**.\n'
        '2. **Badilisha**: usitishaji ukishaidhinishwa, chaguo la kuanza ubadilishaji hujitokeza. Chagua private limited company, jaza maelezo ya kampuni mpya, wasilisha na ulipe ada ya usajili.\n'
        '\n'
        "Unaweza kuomba kutumia jina lilelile likiongezewa 'Limited' au 'Ltd', kwa idhini ya BRS.\n"
        '\n'
        '**PIN ya KRA**: biashara yako ya mtu binafsi ilitumia **PIN yako binafsi ya KRA**. Kampuni ni mlipakodi tofauti mwenye **PIN yake ya KRA**, inayotolewa pamoja na hati zake za usajili -- na kila mkurugenzi na mwanahisa lazima awe tayari na PIN yake binafsi ya KRA.\n'
        '\n'
        '**Ada**: tarajia malipo mawili ya serikali -- KES 250 kwa usitishaji na ada ya usajili wa kampuni. Angalia ada za sasa kwenye tovuti ya BRS kabla ya kuomba, kwa kuwa hubadilika. **Hakuna kiwango cha chini cha mtaji wa hisa** kinachohitajika kisheria.'
    ),
    "wef": (
        '**Mfuko wa Biashara za Wanawake (WEF)** ni mfuko wa serikali unaokopesha wanawake wa Kenya -- tofauti na YEDF (kwa vijana) na Hustler Fund.\n'
        '\n'
        '**Mkopo wa Tuinuke** (kwa vikundi vya wanawake):\n'
        '- Kikundi lazima kiwe kikundi cha kujisaidia kilichosajiliwa chenye **wanawake 10-30**, wote wenye umri wa miaka 18 au zaidi\n'
        '- Kimesajiliwa na Idara ya Huduma za Jamii au Micro and Small Enterprises Authority (MSEA) kwa **angalau miezi mitatu**\n'
        '- Kina **akaunti hai ya benki ya biashara**, na wanachama hukamilisha mafunzo ya elimu ya fedha ya WEF\n'
        '- Kila mwanachama anaweza kuwa katika kikundi kimoja tu kinachofadhiliwa na WEF\n'
        '- Mikopo hukua kwa mzunguko: **KES 100,000** (miezi 6), **200,000** (miezi 9), **350,000** (miezi 12), **500,000** (miezi 15), **750,000** (miezi 18)\n'
        '- **Ada ya usimamizi ya 6%** hutozwa mara moja mwanzoni\n'
        '\n'
        'WEF pia ina bidhaa kwa biashara za wanawake binafsi; angalia orodha ya sasa na uombe katika ofisi ya WEF au kwenye wef.go.ke.'
    ),
    "agpo": (
        "**AGPO** (Access to Government Procurement Opportunities) "
        "inatenga **asilimia 30 ya manunuzi yote ya serikali** kwa "
        "makampuni yanayomilikiwa na vijana (miaka 18-34, yaani chini ya 35), wanawake, na "
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
        'Nenda kwenye **tovuti ya eFNS** ya eCitizen uombe **Kibali cha Daraja R (Class R Permit)** -- kibali kwa raia wa Jumuiya ya Afrika Mashariki (Burundi, DR Congo, Rwanda, Sudan Kusini, Tanzania, Uganda) kuishi, kufanya kazi, kufanya biashara au kuendesha biashara nchini Kenya. **Kibali ni bure**: serikali imethibitisha kwamba hakuna anayepaswa kumtoza raia wa EAC kwa kibali hiki. Ukikaa zaidi ya siku 90 lazima pia ujisajili kama raia wa kigeni, mchakato tofauti -- angalia ada yake ya sasa kwenye eFNS.\n'
        '\n'
        'Hati za kawaida: pasipoti halali, barua ya maombi, KRA PIN ukifanya biashara, na cheti cha tabia njema kutoka polisi (kinachohitajika kwa wafanyabiashara wadogo). Omba mtandaoni, kisha wasilisha fomu zilizojazwa katika ofisi ya Uhamiaji (Nyayo House, Nairobi).'
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
        'Katika Kaunti ya Nairobi hasa, hii ni **Unified Business Permit (UBP)** -- leseni moja ya kila mwaka inayounganisha vibali kadhaa vilivyokuwa tofauti (leseni ya biashara, ukaguzi wa moto, cheti cha afya/chakula, kibali cha matangazo/alama) katika maombi moja. Omba kupitia **NairobiPay (nairobiservices.go.ke)**, piga ***647#**, au tembelea City Hall Annex.\n'
        '\n'
        'Ada inategemea aina na ukubwa wa biashara yako, na huwekwa na Sheria ya Fedha ya kaunti -- thibitisha ada halisi ya aina yako kwenye tovuti kabla ya kulipa. Inafuata mzunguko wa **Januari-Desemba**; kibali huhuishwa kila mwaka; angalia tarehe ya mwisho ya sasa kwenye tovuti, kwa kuwa kuchelewa kulipa kunavutia adhabu. Kaunti nyingine hutoa kibali chao kimoja cha biashara kupitia mifumo yao -- wasiliana na kaunti yako.'
    ),
    "pharmacy_license": (
        'Kuendesha duka la dawa au kemisti kunahitaji leseni kutoka **Pharmacy and Poisons Board (PPB)**, msimamizi wa kitaifa wa dawa chini ya Sheria ya Dawa na Sumu (Cap 244) -- hii ni pamoja na, si badala ya, Single Business Permit ya kaunti yako (ada inatofautiana kwa kaunti).\n'
        '\n'
        '**Sharti muhimu**: duka la dawa lazima limilikiwe na kuendeshwa chini ya mfamasia aliyesajiliwa au fundi wa dawa aliyeandikishwa. Ukilisajili kama kampuni, msimamizi mfamasia lazima awe mwanahisa mwenye hisa nyingi -- huwezi kumiliki au kudhibiti duka la dawa kama mwekezaji tu asiye mfamasia. Msimamizi mfamasia aliyeteuliwa pia anahitaji leseni yake ya kila mwaka ya kufanya kazi kutoka PPB.\n'
        '\n'
        '**Mchakato**: sajili majengo yako na PPB, kisha pitisha ukaguzi wa majengo unaoangalia rafu sahihi, mzunguko wa hewa, eneo la kutolea dawa tofauti na counter ya mauzo, kabati la sumu lenye kufuli, jokofu kwa bidhaa zinazohitaji baridi, na alama ya Msalaba wa Kijani. Leseni hutolewa baada ya ukaguzi wenye mafanikio na lazima zihuishwe kila mwaka (leseni zote za PPB huisha Desemba 31). Thibitisha masharti ya sasa ya umiliki na majengo na PPB kabla ya kuwekeza.'
    ),
    "ca_license": (
        'Si kila kampuni changa ya teknolojia inahitaji hii -- **Mamlaka ya Mawasiliano ya Kenya (CA)** hutoa leseni kwa mawasiliano ya simu, utangazaji, huduma za posta/usafirishaji wa vifurushi na vifaa vinavyohusiana, si biashara za kawaida za programu au apps. Ikiwa kampuni yako inatengeneza app au tovuti tu, bila kuendesha miundombinu ya mawasiliano au kutoa huduma za mtandao au maudhui zinazodhibitiwa, huenda huhitaji leseni ya CA.\n'
        '\n'
        'Ikiwa uko katika kundi linalodhibitiwa, Mfumo wa Leseni Moja wa CA unajumuisha leseni za **Network Facilities Provider** (miundombinu), **Applications Service Provider** na **Content Service Provider**, pamoja na leseni tofauti za utangazaji, huduma za posta/vifurushi na uidhinishaji wa vifaa. Mwenye leseni anayemilikiwa na wageni lazima atoe **angalau 20% ya hisa zake kwa Wakenya** ndani ya miaka mitatu baada ya kupata leseni. Thibitisha mahitaji ya maombi, ada na muda wa kushughulikia na CA (ca.go.ke) kabla ya kuomba.'
    ),
    "nssf_registration": (
        "**Kama mwajiri**: kila mwajiri aliye na **mfanyakazi mmoja au zaidi** lazima ajisajili na NSSF kama mwajiri anayechangia. Kwenye tovuti ya NSSF Self Service (selfservice.nssf.or.ke), chagua **'Employer Registration'** kama bado huna nambari ya usajili ya NSSF, na ujaze fomu. Kisha chapisha taarifa ya maombi na uipeleke ofisi ya NSSF iliyo karibu nawe ili ithibitishwe; ofisi itakupa PIN key ya kuwezesha akaunti yako ya mtandaoni.\n"
        '\n'
        '**Kwa wafanyakazi wako**: lazima pia uhakikishe kila mfanyakazi anasajiliwa mara moja kama mwanachama wa NSSF.\n'
        '\n'
        '**Baada ya kujisajili**: kata na uwasilishe michango, na uwasilishe ripoti za kila mwezi, kufikia **tarehe 9 ya mwezi unaofuata**. Mwajiri asiyetimiza wajibu huu anatenda kosa.'
    ),
    "keproba": (
        "**KEPROBA** (Kenya Export Promotion and Branding Agency) ni shirika la serikali (lililoundwa 2019, likiunganisha Export Promotion Council ya zamani na Brand Kenya Board) linalosaidia wafanyabiashara wa Kenya kuuza nje na kuendeleza 'Brand Kenya' kimataifa.\n"
        '\n'
        '**Kile kinachotolewa**: mwongozo wa taratibu na nyaraka za usafirishaji, taarifa za soko na sharti za kuingia katika nchi lengwa, ujenzi wa uwezo kupitia mafunzo ya usafirishaji, ujumbe wa kibiashara na ushiriki katika maonyesho ya biashara, na msaada wa **maendeleo ya bidhaa na branding** -- ikiwa ni pamoja na ufungashaji, uwekaji lebo, na uwekaji nafasi ya chapa kwa wanunuzi wa kimataifa. Wasiliana kupitia ofisi za KEPROBA au makeitkenya.go.ke.\n'
        '\n'
        'Kumbuka: Mswada wa Investment and Export Promotion Authority, 2026 unapendekeza kuunganisha KEPROBA na Kenya Investment Authority, hivyo thibitisha jina la sasa la shirika na mawasiliano yake kabla ya kwenda.'
    ),
    "no_permit_penalty": (
        'Kufanya biashara bila kibali halali cha biashara cha kaunti ni kinyume cha sheria nchini Kenya. Kila kaunti huweka masharti na adhabu zake za vibali katika sheria zake.\n'
        '\n'
        '**Kinachoweza kutokea**:\n'
        "- **Kufungwa au kunyang'anywa bidhaa**: sheria za kaunti zinaweza kuwaruhusu maafisa wa leseni kufunga biashara isiyo na leseni -- Kiambu, kwa mfano, afisa wa leseni anaweza kuamuru biashara ifungwe au bidhaa zichukuliwe, na adhabu ni **20% ya ada ya leseni kwa kila mwezi** wa kuchelewa\n"
        '- **Faini, kifungo, au vyote viwili** ukipatikana na hatia -- Nairobi, mtu asiyehuisha leseni yake na kuendelea kufanya biashara anatenda kosa, na anaweza kutozwa faini ya hadi **KES 50,000**, kifungo cha hadi **miezi 3**, au vyote viwili\n'
        '- Kaunti nyingine huweka viwango vyao -- thibitisha adhabu za kaunti yako\n'
        '\n'
        'Pata kibali chako kabla ya kuanza biashara, na ukihuishe kwa wakati.'
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
        '**eTIMS** (electronic Tax Invoice Management System) ni mfumo wa KRA wa kutengeneza risiti/ankara za kielektroniki zinazokubalika kikodi -- unahitajika kwa watu wote wanaofanya biashara isipokuwa waliosamehewa (Kanuni za Taratibu za Kodi (Ankara za Kielektroniki), 2024), na KRA hukubali tu ankara zilizotengenezwa na eTIMS kama uthibitisho halali wa ununuzi wa kukata gharama za biashara.\n'
        '\n'
        '**Kwa nini biashara yako inahitaji**: bila ankara za eTIMS, gharama zako za biashara huenda zisikubaliwe kikodi, na wateja wanaohitaji kudai VAT yao wenyewe hawawezi kufanya hivyo kutoka ankara isiyo ya eTIMS. Kwa biashara ndogo, chaguo la bure la **eTIMS Lite** kwenye tovuti ya eTIMS ya KRA ni njia rahisi zaidi ya kutii bila kununua vifaa. Kutotii kunatozwa adhabu ya **mara mbili ya kodi inayodaiwa**.'
    ),
    "sacco_vs_bank": (
        '**Mikopo ya SACCO dhidi ya mikopo ya benki nchini Kenya**:\n'
        '\n'
        '- **Nani anaweza kukopa**: SACCO hukopesha **wanachama** wake pekee; benki hukopesha mteja yeyote anayestahili\n'
        '- **Kinachodhamini mkopo**: mikopo ya SACCO hutegemea **akiba yako katika SACCO**; benki hutegemea zaidi dhamana na ukaguzi wa historia ya mikopo\n'
        '- **Riba**: kila SACCO na kila benki huweka kiwango chake cha riba. Uliza **kiwango cha riba kwa mwaka** na kama kinatozwa kwa **salio linalopungua au kiwango cha kudumu (flat rate)** -- kwa kiwango kilekile, kiwango cha kudumu hugharimu zaidi\n'
        '- **Kabla ya kukopa kutoka SACCO**: kwa kawaida unahitaji kujiunga na kuweka akiba kwanza\n'
        '- **Gawio**: wanachama wa SACCO wanaweza kupata gawio kwa hisa zao na riba kwa akiba, jambo ambalo mkopo wa benki hautoi\n'
        '- **Hakikisha SACCO ina leseni** kwenye tovuti ya SASRA (sasra.go.ke)'
    ),
    "food_business_license": (
        'Biashara ya chakula (mkahawa, cafe, duka la mikate, duka) inahitaji tabaka kadhaa, juu ya kibali chako cha kawaida cha kaunti. **Nairobi**, Unified Business Permit inaunganisha leseni za biashara, moto, chakula, afya na matangazo katika maombi moja, hivyo idhini za afya na moto za majengo zilizo hapa chini huja nayo; katika kaunti nyingine, angalia kama ni tofauti:\n'
        '\n'
        '- **Cheti cha Afya/Usafi wa Chakula**: kinatolewa na idara ya afya ya kaunti, kikithibitisha majengo yako yanafikia viwango vya usafi, kinahitajika kabla ya kufungua (ada inatofautiana kwa kaunti)\n'
        '- **Cheti cha Afya cha Mshughulikiaji wa Chakula**: kinahitajika kwa **kila mfanyakazi binafsi** anayeshughulikia chakula, kinapatikana baada ya uchunguzi wa afya\n'
        '- **Cheti cha Usalama wa Moto**: cha lazima kwa biashara zote, kinahitaji vizima moto na ukaguzi wa idara ya moto ya kaunti\n'
        '- **Mahususi kwa mikahawa**: usajili na **Tourism Regulatory Authority (TRA)** chini ya Sheria ya Utalii ya 2011, ikiwa unaendesha kama mkahawa\n'
        '\n'
        'Ikiwa unatengeneza au kufunga bidhaa za chakula kwa mauzo, utahitaji pia uthibitisho wa **KEBS** (Standardization Mark).'
    ),
    "agpo": (
        "**AGPO** (Access to Government Procurement Opportunities) "
        "inatenga **asilimia 30 ya manunuzi yote ya serikali** kwa "
        "makampuni yanayomilikiwa na vijana (miaka 18-34, yaani chini ya 35), wanawake, na "
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
        '**Mkopo wa Personal Finance** wa Hustler Fund hutoa **KES 500 hadi KES 50,000**, kulingana na alama zako za mkopo, kwa riba **isiyozidi 8% kwa mwaka** (hukokotolewa kwa uwiano), unaolipwa ndani ya **siku 14**. Unaweza kutumika kwa biashara au mahitaji binafsi, bila dhamana.\n'
        '\n'
        '**Kuupata**: piga ***254#** kwenye laini yako iliyosajiliwa. Unahitaji kuwa raia wa Kenya mwenye umri wa miaka 18 au zaidi, kitambulisho halali cha taifa, akaunti hai ya pesa za simu (M-PESA, Airtel Money au T-Kash), na laini iliyotumika kwa angalau siku 90.\n'
        '\n'
        'Mfuko pia umetangaza mikopo ya Micro, SME na Start-up; angalia *254# au njia rasmi za Hustler Fund kujua kinachopatikana sasa. Kiwango chako cha mkopo kinategemea alama zako.'
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
    'barber_salon_taxes': (
        'Wajibu wa kodi kwa biashara ya kinyozi au saluni nchini Kenya unategemea mauzo yako ya mwaka na kama una wafanyakazi -- si aina ya biashara yenyewe:\n'
        '\n'
        '- **Kodi ya Mauzo (TOT)**: 1.5% ya mauzo ghafi ikiwa mauzo yako ya mwaka ni zaidi ya KES 1,000,000 lakini hayazidi KES 25,000,000. Hutozwa kwa mauzo ghafi **bila kutoa gharama**. Kwa mfano, mauzo ya mwaka ya KES 2,000,000 yanamaanisha TOT ya KES 30,000 (2,000,000 x 1.5%). Chini ya KES 1,000,000 hulipi TOT.\n'
        '- **VAT**: mauzo yako yakifikia KES 5,000,000 na unauza bidhaa au huduma zinazotozwa VAT, lazima pia ujisajili kwa VAT.\n'
        '- **Ukiwa na wafanyakazi**: PAYE (viwango kuanzia 10% hadi 35%, ukitoa nafuu ya kibinafsi ya KES 2,400 kwa mwezi), NSSF (6% mfanyakazi + 6% mwajiri), SHIF (2.75% ya mshahara ghafi) na Ushuru wa Nyumba (1.5% mfanyakazi + 1.5% mwajiri) -- uliza kuhusu "wajibu wa mishahara" kupata orodha kamili.\n'
        '- **Kibali cha kaunti**: kibali kimoja cha biashara kutoka serikali ya kaunti yako; aina na ada hutofautiana kwa kila kaunti.\n'
        '\n'
        'Mahali unapofanyia biashara huathiri kibali na ada za kaunti, lakini sheria za kodi za kitaifa hapo juu ni sawa katika kila kaunti. Thibitisha hali yako kupitia iTax (itax.kra.go.ke).'
    ),
    'compliance_software': (
        'Hakuna programu moja unayolazimika kutumia, lakini hii ndiyo mifumo rasmi ambayo biashara nyingi ndogo nchini Kenya zinahitaji kwa utiifu:\n'
        '\n'
        '- **eTIMS** (mfumo wa KRA wa ankara za kodi za kielektroniki): unahitajika kwa watu wote wanaofanya biashara, isipokuwa walioondolewa -- si biashara zilizosajiliwa kwa VAT pekee -- na unahitajika ili gharama za biashara yako zikubalike kupunguzwa kwenye kodi. Chaguo la bure la **eTIMS Lite** ndilo njia rahisi zaidi kwa biashara ndogo kutii bila kununua vifaa.\n'
        '- **KRA iTax (itax.kra.go.ke)**: tovuti ya KRA ya kuwasilisha ritani, ikiwemo ritani ya kila mwezi ya PAYE (P10) ikiwa una wafanyakazi.\n'
        '- **Tovuti ya Huduma Binafsi ya Waajiri ya NSSF (selfservice.nssf.or.ke)**: jisajili kama mwajiri na simamia wajibu wako wa NSSF ikiwa una wafanyakazi.\n'
        '\n'
        'Ukitaka pia programu ya uhasibu au mishahara juu ya hii, siwezi kupendekeza bidhaa mahususi, lakini hakikisha inakokotoa kwa usahihi viwango vya sasa vya PAYE, ngazi za NSSF, SHIF (2.75% ya mshahara ghafi) na Ushuru wa Nyumba (1.5% kila mmoja kwa mfanyakazi na mwajiri), na kwamba inaweza kutoa ankara zinazokubalika na eTIMS.'
    ),
    'employee_compliance_checklist': (
        'Kwa biashara ya uuzaji yenye wafanyakazi wa kudumu, haya ndiyo unayopaswa kudumisha:\n'
        '\n'
        '**Mikataba ya ajira**: mkataba wa maandishi kwa ajira yoyote ya miezi mitatu au zaidi (Sheria ya Ajira, Kifungu cha 9), unaoonyesha tarehe ya kuanza, maelezo ya kazi, mshahara, saa za kazi, na haki ya likizo.\n'
        '\n'
        '**Makato ya kisheria, kwa kila mfanyakazi, kila mwezi**:\n'
        '- **NSSF**: 6% mfanyakazi + 6% mwajiri (sawa), Ngazi ya I hadi KES 9,000, Ngazi ya II hadi KES 108,000\n'
        '- **PAYE**: viwango vinavyopanda kuanzia 10% hadi 35%, ukitoa nafuu ya kibinafsi ya KES 2,400\n'
        '- **SHIF** (Mfuko wa Bima ya Afya ya Jamii -- ulichukua nafasi ya NHIF Oktoba 2024): 2.75% ya mshahara ghafi, upande wa mfanyakazi pekee, bila kikomo\n'
        '- **Ushuru wa Nyumba**: 1.5% mfanyakazi + 1.5% mwajiri, bila kiwango cha chini cha mapato\n'
        '\n'
        '**Rekodi za likizo**: angalau siku 21 za kazi za likizo ya mwaka kwa kila miezi 12 ya huduma (Sheria ya Ajira, Kifungu cha 28).\n'
        '\n'
        '**Rekodi za mishahara**: andika mshahara wa kila mwezi wa kila mfanyakazi na makato yote hapo juu, na uyalipe kwa wakati -- NSSF na PAYE hulipwa kabla ya tarehe 9 ya mwezi unaofuata, Ushuru wa Nyumba kabla ya siku ya 9 ya kazi baada ya mwisho wa mwezi (hutangazwa kwenye ritani ya PAYE), na thibitisha tarehe ya SHIF na Mamlaka ya Afya ya Jamii (SHA). Weka rekodi hizi tayari kwa ukaguzi, na uhifadhi mkataba wa maandishi na maelezo ya kila mfanyakazi kwa miaka mitano baada ya ajira yake kuisha (Sheria ya Ajira).'
    ),
    'regulations_not_exhaustive': (
        'Hapana -- hakuna orodha moja kamili, kwa sababu kinachokuhusu kinategemea aina ya biashara yako, mauzo yako na kama una wafanyakazi. Haya ndiyo mambo ya msingi yanayohusu biashara nyingi nchini Kenya:\n'
        '\n'
        '- **Usajili**: sajili jina la biashara yako (eCitizen/BRS) na upate PIN ya KRA\n'
        '- **Kibali cha kaunti**: kibali kimoja cha biashara kutoka serikali ya kaunti yako -- aina na ada hutofautiana kwa kila kaunti\n'
        '- **Mfumo wa kodi ya mapato**: Kodi ya Mauzo (1.5% ya mauzo ghafi) ikiwa mauzo yako ya mwaka ni kati ya KES 1,000,000 na KES 25,000,000; usajili wa VAT mara mauzo yako ya mwaka yanayotozwa kodi yanapofikia KES 5,000,000\n'
        '- **eTIMS**: mfumo wa KRA wa ankara za kielektroniki, unaohitajika kwa watu wote wanaofanya biashara isipokuwa walioondolewa, na unahitajika ili gharama zako zikubalike kupunguzwa kwenye kodi (chaguo la bure la eTIMS Lite ndilo rahisi zaidi kwa biashara ndogo)\n'
        '- **Ukiwa na wafanyakazi**: NSSF (6% mfanyakazi + 6% mwajiri), PAYE, SHIF (2.75% ya mshahara ghafi) na Ushuru wa Nyumba (1.5% mfanyakazi + 1.5% mwajiri), pamoja na mikataba ya maandishi na rekodi za likizo -- uliza kuhusu "wajibu wa mishahara" kupata orodha kamili\n'
        '\n'
        'Baadhi ya sekta pia zinahitaji leseni zao (kwa mfano biashara za chakula au maduka ya dawa). Niambie aina ya biashara yako na nitakupa mahitaji ninayoweza kuthibitisha kwa ajili yake.'
    ),
    'relocation_county': (
        'Kenya ina kaunti badala ya majimbo, na kuhamisha biashara yako kutoka kaunti moja hadi nyingine hubadilisha zaidi **leseni za kaunti**, si kodi zako za kitaifa.\n'
        '\n'
        '- **Kodi za kitaifa hazibadiliki**: Kodi ya Mauzo (1.5% ya mauzo ghafi kwa mauzo kati ya KES 1,000,000 na KES 25,000,000), VAT (mauzo yanayotozwa kodi yakifikia KES 5,000,000) na, ukiwa na wafanyakazi, PAYE, NSSF, SHIF na Ushuru wa Nyumba zimewekwa kitaifa na hukusanywa kupitia KRA. Hazitegemei kaunti unayofanyia biashara.\n'
        '- **Leseni za kaunti hubadilika**: kibali kimoja cha biashara hutolewa na kila serikali ya kaunti, na aina na ada hutofautiana kwa kila kaunti. Katika kaunti yako mpya utahitaji kibali kutoka ofisi ya leseni za biashara ya kaunti hiyo.\n'
        '\n'
        'Thibitisha aina na ada kamili na kaunti yako mpya.'
    ),
    'sole_prop_llc_mistakes': (
        'Makosa ya kawaida wakati wa kuhama kutoka biashara ya mtu binafsi kwenda kampuni ya kibinafsi (limited company):\n'
        '\n'
        '- **Kutarajia ubadilishaji wa hatua moja**: kwenye tovuti ya Huduma ya Usajili wa Biashara (brsv2.ecitizen.go.ke) ni hatua mbili zinazofuatana. Kwanza sitisha jina la biashara yako, ukichagua "convert" kama sababu na kupakia **Fomu BN 6** iliyotiwa sahihi (ada **KES 250**). Usitishaji ukishaidhinishwa ndipo chaguo la kuibadilisha kuwa kampuni hujitokeza; kisha jaza maelezo ya kampuni mpya na ulipe ada ya usajili.\n'
        '- **Kuendelea kutumia PIN yako binafsi ya KRA**: kampuni ni mlipakodi tofauti mwenye PIN yake ya KRA, inayotolewa pamoja na hati zake za usajili. Usiwasilishe kodi za kampuni kwa PIN yako binafsi.\n'
        '- **Kuanza kabla kila mtu hajapata PIN**: kila mkurugenzi na mwanahisa lazima awe tayari na PIN yake binafsi ya KRA kabla kampuni haijasajiliwa.\n'
        '- **Kupanga bajeti ya malipo moja tu**: tarajia malipo mawili tofauti ya serikali -- usitishaji wa jina la biashara (KES 250) na usajili wa kampuni.\n'
        '- **Kuchelewa kwa sababu ya mtaji wa hisa**: hakuna kiwango cha chini cha mtaji wa hisa kinachohitajika kisheria.\n'
        '\n'
        'Thibitisha hatua na ada za sasa kwenye tovuti ya BRS kabla ya kuwasilisha.'
    ),
    'start_business': (
        '**Kuanzisha biashara ndogo nchini Kenya** -- hatua za msingi:\n'
        '\n'
        '1. **Pata PIN ya KRA** (bure, kwenye iTax: itax.kra.go.ke).\n'
        '2. **Sajili jina la biashara yako** kwenye eCitizen kupitia Huduma ya Usajili wa Biashara (BRS), ukitumia kitambulisho chako cha taifa na PIN ya KRA, na ulipe ada ya KES 950. Ukitaka kampuni (limited company) badala yake, uliza kuhusu "biashara ya mtu binafsi au kampuni".\n'
        '3. **Pata kibali kimoja cha biashara kutoka serikali ya kaunti yako** kabla ya kuanza kufanya biashara -- aina na ada hutofautiana kwa kila kaunti (Nairobi ni Unified Business Permit).\n'
        '4. **Leseni za sekta**: baadhi ya biashara zinahitaji pia leseni zao, kwa mfano biashara za chakula au maduka ya dawa.\n'
        '5. **Kodi**: ikiwa mauzo yako ya mwaka ni zaidi ya KES 1,000,000 hadi KES 25,000,000 unalipa Kodi ya Mauzo (1.5% ya mauzo ghafi); jisajili kwa VAT mauzo yanayotozwa kodi yanapofikia KES 5,000,000. Ankara za eTIMS zinahitajika kwa watu wote wanaofanya biashara isipokuwa walioondolewa.\n'
        '6. **Ukiajiri watu**: jisajili kama mwajiri na NSSF, na ukate PAYE, NSSF, SHIF (iliyochukua nafasi ya NHIF Oktoba 2024) na Ushuru wa Nyumba.\n'
        '\n'
        'Kwa hiyo ndiyo -- jisajili na upate kibali cha kaunti kabla ya kuanza kufanya biashara; kufanya biashara bila kibali cha kaunti ni kinyume cha sheria. Uliza kuhusu hatua yoyote kwa maelezo zaidi.'
    ),
    'afcfta': (
        '**Kuuza bidhaa katika nchi nyingine za Afrika chini ya AfCFTA** (Eneo Huru la Biashara la Bara la Afrika):\n'
        '\n'
        'AfCFTA ilianzishwa mwaka 2018 ili kuunda soko moja la bara kwa nchi 55 wanachama wa Umoja wa Afrika. Ili kuuza nje kwa ushuru wa chini wa AfCFTA, bidhaa zako zinahitaji **cheti cha asili cha AfCFTA** (certificate of origin). Nchini Kenya hutolewa na **Idara ya Forodha na Udhibiti wa Mipaka ya KRA** (Customs & Border Control).\n'
        '\n'
        '1. **Jisajili kama msafirishaji bidhaa nje** na Forodha ya KRA: jaza fomu ya usajili katika ofisi ya Rules of Origin (Nairobi, Mombasa, Nakuru, Eldoret au Kisumu), ukiwa na cheti cha usajili wa biashara, PIN ya KRA na leseni za biashara zinazohusika\n'
        '2. KRA hukagua kwamba bidhaa zako zinatimiza **kanuni za asili** za AfCFTA (Annex 2 ya Protocol on Trade in Goods) kabla ya kukuidhinisha\n'
        '3. Ukiidhinishwa utapata nambari ya kumbukumbu, na unaweza kununua vyeti vya asili kwa **USD 3** kila kimoja\n'
        '\n'
        'Kwa mwongozo wa kuuza nje, taarifa za masoko na maonyesho ya biashara, uliza kuhusu **KEPROBA**.'
    ),
}


# Where each verified answer was checked: topic -> (short source name, URL, date checked).
# source_report.py lists verified answers with no entry here, or checked too long ago.
CANNED_SOURCES = {
    'paye_bands': ('KRA', 'https://www.kra.go.ke/individual/filing-paying/types-of-taxes/paye', '2026-10-03'),
    'paye_remit': ('KRA', 'https://www.kra.go.ke/individual/filing-paying/types-of-taxes/paye', '2026-10-02'),
    'housing_levy': ('KRA', 'https://www.kra.go.ke/news-center/public-notices/2099-collection-of-the-affordable-housing-levy-by-kenya-revenue-authority', '2026-10-03'),
    'nssf': ('NSSF', 'https://gaa.go.ke/sites/default/files/2026-02/Notice%20To%20Employers%20%E2%80%94%20Year%204%20(2026)%20NSSF%20Contribution%20Rates%20.pdf', '2026-10-03'),
    'shif_rate': ('Social Health Insurance Regulations 2024', 'https://www.ey.com/en_gl/technical/tax-alerts/kenya-employers-to-begin-making-contributions-to-social-health-insurance-fund', '2026-10-03'),
    'turnover_tax': ('KRA', 'https://www.kra.go.ke/individual/filing-paying/types-of-taxes/turnover-tax-tot', '2026-10-03'),
    'late_filing_penalty': ('KRA', 'https://www.kra.go.ke/business/business-compliance-penalties/business-how-to-file/business-offences-penalties', '2026-10-03'),
    'vat_penalty': ('KRA', 'https://www.kra.go.ke/business/business-compliance-penalties/business-how-to-file/business-offences-penalties', '2026-10-02'),
    'leave': ('Employment Act 2007', 'https://www.a-mla.org/en/country/pdf/1903', '2026-10-03'),
    'maternity_paternity_leave': ('Employment Act 2007', 'https://www.a-mla.org/en/country/pdf/1903', '2026-10-03'),
    'probation_period': ('Employment Act 2007', 'https://www.a-mla.org/en/country/pdf/1903', '2026-10-03'),
    'minimum_wage': ('Kenya Gazette, LN 95 & 96 of 2026', 'https://www.grantthornton.co.ke/globalassets/1.-member-firms/kenya/insights/pdf/wages-guide-2026.pdf', '2026-10-03'),
    'capital': ('Legal Notice 60 of 2016', 'https://taxsummaries.pwc.com/kenya/corporate/other-taxes', '2026-10-03'),
    'etims_general': ('eTIMS Regulations 2024', 'https://www.rsm.global/kenya/news/kenya-tax-alert-tax-procedures-electronic-tax-invoice-regulations-2024', '2026-10-03'),
    'agpo': ('National Treasury (AGPO)', 'https://tenders.go.ke/storage/Documents/1750773716675-agpo-registration-and-sensitization-of-suppliers-through-university-website.pdf', '2026-10-03'),
    'wef': ('Women Enterprise Fund', 'https://wef.go.ke/tuinuke-loan/', '2026-10-03'),
    'hustler_fund_business': ('MSEA (Hustler Fund FAQs)', 'https://msea.go.ke/wp-content/uploads/2024/11/Hustler-Fund-FAQs.pdf', '2026-10-03'),
    'yedf': ('Youth Enterprise Development Fund', 'https://x.com/YouthFund_Ke/status/2018249406655475950', '2026-10-03'),
    'loan': ('YEDF, MSEA, WEF', 'https://msea.go.ke/wp-content/uploads/2024/11/Hustler-Fund-FAQs.pdf', '2026-10-03'),
    'class_r_permit': ('Government statement, 10 Sep 2026', 'https://thekenyatimes.com/national/mudavadi-class-r-permit/', '2026-10-03'),
    'sacco_vs_bank': ('SASRA', 'https://www.sasra.go.ke/frequently-asked-questions/', '2026-10-03'),
    'vat': ('KRA (VAT guide)', 'https://www.kra.go.ke/images/publications/VAT_8112023.pdf', '2026-10-03'),
    'tcc_application': ('KRA', 'https://www.kra.go.ke/business/business-compliance-penalties/business-how-to-file/tax-compliance', '2026-10-03'),
    'nssf_penalty': ('NSSF', 'https://www.nssf.or.ke/?p=1094', '2026-10-03'),
    'compliance_software': ('KRA, SHA', 'https://www.rsm.global/kenya/news/kenya-tax-alert-tax-procedures-electronic-tax-invoice-regulations-2024', '2026-10-03'),
    'regulations_not_exhaustive': ('KRA, NSSF, SHA', 'https://www.kra.go.ke/images/publications/VAT_8112023.pdf', '2026-10-03'),
    'employee_compliance_checklist': ('Employment Act 2007; KRA, NSSF, SHA', 'https://www.a-mla.org/en/country/pdf/1903', '2026-10-03'),
    'barber_salon_taxes': ('KRA, NSSF, SHA', 'https://www.kra.go.ke/individual/filing-paying/types-of-taxes/turnover-tax-tot', '2026-10-03'),
    'relocation_county': ('KRA', 'https://www.kra.go.ke/individual/filing-paying/types-of-taxes/turnover-tax-tot', '2026-10-03'),
    'sole_prop_llc_mistakes': ('Business Registration Service', 'https://brs.go.ke/wp-content/uploads/2026/05/Step-by-Step-Guide_Cessation-Conversion.pdf', '2026-10-03'),
    'sole_prop_to_llc': ('Business Registration Service', 'https://brs.go.ke/wp-content/uploads/2026/05/Step-by-Step-Guide_Cessation-Conversion.pdf', '2026-10-03'),
    'termination': ('Employment Act 2007', 'https://www.a-mla.org/en/country/pdf/1903', '2026-10-03'),
    'business_insurance': ('Work Injury Benefits Act 2007', 'https://new.kenyalaw.org/akn/ke/act/2007/13/eng@2022-12-31', '2026-10-03'),
    'unified_business_permit': ('Nairobi City County', 'https://nairobi.go.ke/transition-to-unified-business-permit-nairobi-county-implements-no-cash-policy-encourages-digital-payments', '2026-10-03'),
    'kra_pin': ('KRA (PIN registration guide)', 'https://www.kra.go.ke/images/publications/Step-By-Step-Guide-for-Application-Of-PIN-Without-Obligation-2025.pdf', '2026-10-03'),
    'mpesa_paybill_till': ('Safaricom (M-PESA Paybill FAQs)', 'https://safaricom.co.ke/media-center-landing/frequently-asked-questions/m-pesa-paybill', '2026-10-03'),
    'ca_license': ('Communications Authority of Kenya', 'https://www.ca.go.ke/node/236', '2026-10-03'),
    'registration': ('BRS (FAQs); Strathmore iBizAfrica', 'https://brs.go.ke/wp-content/uploads/2024/05/FAQs.pdf', '2026-10-05'),
    'no_permit_penalty': ('KRA (Nairobi notice); Kiambu Trade Licence Act 2016', 'https://www.kra.go.ke/news-center/public-notices/1086-renewal-of-nairobi-county-permits-and-licences', '2026-10-05'),
    'nssf_registration': ('NSSF (employer obligations)', 'https://www.nssf.or.ke/new-nssf-rates-employer-obligations', '2026-10-05'),
    'start_business': ('KenInvest; BRS, KRA, NSSF, SHA', 'https://eprocedures.investkenya.go.ke/menu/1?l=en', '2026-10-05'),
    'afcfta': ('KRA (AfCFTA FAQs)', 'https://www.kra.go.ke/helping-tax-payers/faqs/the-african-continental-free-trade-area-afcfta', '2026-10-05'),
}

# Contextual follow-ups: after <topic>, a short question containing a cue word goes to <related topic>.
# Used by query_pack.contextual_topic() and Router.kt; built into the pack's followups table.
CANNED_FOLLOWUPS = {
    'vat': {
        'vat_penalty': ['late', 'penalty', 'penalties', 'fine', 'chelewa', 'faini', 'adhabu'],
    },
    'paye_bands': {
        'paye_remit': ['when', 'due', 'deadline', 'remit', 'submit', 'late', 'penalty', 'lini', 'tarehe'],
    },
    'paye_remit': {
        'paye_bands': ['rate', 'band', 'how much', 'kiasi', 'kiwango'],
    },
    'nssf': {
        'nssf_penalty': ['late', 'penalty', 'fine', 'chelewa', 'faini'],
        'nssf_registration': ['register', 'sajili'],
    },
    'loan': {
        'hustler_fund_business': ['hustler', 'limit', '254'],
        'yedf': ['youth', 'vijana', 'yedf'],
        'wef': ['women', 'wanawake', 'wef'],
    },
    'license': {
        'unified_business_permit': ['nairobi'],
        'food_business_license': ['food', 'chakula', 'restaurant', 'hotel'],
        'pharmacy_license': ['chemist', 'pharmacy', 'dawa'],
        'no_permit_penalty': ['without', 'penalty', 'fine', 'bila'],
    },
    'food_business_license': {
        'unified_business_permit': ['nairobi'],
    },
    'unified_business_permit': {
        'no_permit_penalty': ['late', 'penalty', 'without', 'fine', 'bila'],
    },
    'start_business': {
        'registration': ['register', 'name', 'sajili', 'jina'],
        'license': ['permit', 'licence', 'license', 'kibali', 'leseni'],
        'kra_pin': ['pin'],
        'turnover_tax': ['tax', 'kodi'],
    },
    'registration': {
        'sole_prop_vs_limited': ['limited', 'company', 'kampuni'],
    },
    'turnover_tax': {
        'vat': ['vat'],
    },
}

TOPIC_KEYWORDS = {
    "nssf_penalty": ["nssf penalty", "late nssf", "nssf late payment", "penalty for late nssf", "nssf fine", "adhabu ya nssf", "faini ya nssf kuchelewa"],
    "mpesa_paybill_till": ["paybill", "till number", "buy goods till", "set up paybill", "mpesa business", "namba ya paybill", "namba ya till", "kuweka paybill"],
    "nssf_registration": ["register my business and employees", "nssf registration", "register for nssf", "register my employees for nssf", "kusajili wafanyakazi nssf", "kujisajili nssf"],
    "nssf": ["nssf", "national social security fund"],
    "maternity_paternity_leave": ["maternity leave", "paternity leave", "maternity leave entitlement", "likizo ya uzazi", "likizo ya baba"],
    "leave": ["annual leave", "leave days", "likizo ya mwaka", "siku za likizo", "annual leave entitlement"],
    "capital": ["minimum share capital", "share capital requirement", "mtaji wa chini", "mtaji unaohitajika"],
    "yedf": ["yedf", "youth enterprise development fund", "rausha", "inua loan", "vuka loan", "mfuko wa vijana", "mkopo wa yedf", 'mkopo wa vijana', 'vijana', 'youth loan', 'youth fund',],
    "hustler_fund_business": ["hustler fund business", "hustler fund for my business", "hustler fund biashara loan", "business tier hustler fund", "hustler fund enterprise loan", "personal loan and business loan", "hustler fund personal loan and business", "difference between the hustler fund", "apply for the hustler fund", "hustler fund and what are the eligibility", "eligibility requirements for the hustler fund", "mkopo kutoka hustler fund", "kupata mkopo kutoka hustler fund", "hustler fund na ninahitaji", "ninahitaji nini kustahili", 'hustler fund limit', 'hustler limit',],
    "loan": ["apply for a loan", "apply for financing", "get a loan", "startup loan", "hustler fund", "loan to start", "mkopo wa biashara", "jinsi ya kupata mkopo", "kupata mkopo wa kuanzisha"],
    "sole_prop_to_llc": ["transition into a limited", "convert my sole proprietorship", "converting sole proprietorship", "convert a sole proprietorship", "sole proprietorship into a limited", "sole proprietorship to a limited", "convert business name to company", "business name to limited company", "sole prop to llc", "sole proprietorship to llc", "kubadilisha biashara kuwa kampuni", "kutoka umiliki binafsi kwenda kampuni"],
    "kra_pin": ["how do i get a kra pin", "kra pin registration", "apply for kra pin", "get a kra pin", "kra pin for my business", "namba ya pin ya kra", "kupata pin ya kra", "jinsi ya kupata pin"],
    "vat": ["vat registration", "vat threshold", "register for vat", "required to register for vat", "do i need to register for vat", "vat registration threshold", "kusajili vat", "ni lini nasajili vat", "kikomo cha vat", "vat rate", "rate of vat", "how much is vat", "kiwango cha vat", "asilimia ya vat"],
    "vat_penalty": ["vat penalty", "vat penalties", "penalty for late vat", "late filing of vat", "vat late filing", "vat returns late", "vat return late", "late vat return", "late vat returns", "late payment of vat", "vat late payment", "adhabu ya vat", "faini ya vat", 'kuchelewa kulipa vat', 'nikichelewa kulipa vat', 'vat late',],
    "termination": ["terminate an employee", "termination", "dismissal", "dismiss an employee", "redundancy", "fire an employee", "firing an employee", "kumfukuza mfanyakazi", "kuachisha kazi", "kufukuza mfanyakazi"],
    "food_business_license": ["food business need to operate", "licenses does a food business", "restaurant license kenya", "food business licenses", "licenses for a restaurant", "leseni ya mkahawa", "leseni ya biashara ya chakula", "leseni gani kwa biashara ya chakula"],
    "license": ["kufungua duka", "open a shop", "start a shop", "single business permit", "what license do i need", "what licence do i need", "trade license requirements", "leseni ya biashara", "kibali cha biashara", "ninahitaji leseni gani", 'permit to sell', 'sell at the market', 'market permit', 'do i need a permit', 'hawker',],
    "turnover_tax": ["turnover tax", "tot rate", "tot threshold", "kodi ya mauzo", "kodi ya turnover"],
    "paye_bands": ["paye rate", "paye band", "paye tax rate", "income tax band", "income tax rate", "kiwango cha paye", "ushuru wa paye", "kodi ya mshahara"],
    "paye_remit": ["pay paye", "remit paye", "file paye", "paye return", "paye returns", "submit paye", "paye due date", "when is paye due", "deadline for paye", "paye deadline", "paye penalty", "late paye", "late payment of paye", "kulipa paye", "kuwasilisha paye"],
    "shif_rate": ["what is shif", "shif replace nhif", "shif replaced nhif", "replace nhif", "replaced nhif", "nhif to shif", "from nhif", "shif vs nhif", "shif and nhif", "nhif and shif", "what happened to nhif", "is nhif still", "shif ni nini", "nhif imebadilishwa", "shif rate", "shif contribution", "shif percentage", "how much shif", "shif deduction", "contribute to shif", "employer shif", "shif employer", "pay to shif", "shif pay", "obligations to shif", "shif obligations", "obligations under shif", "kiwango cha shif", "mchango wa shif", 'nhif bado', 'nhif still',],
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
    "pharmacy_license": ["duka ya dawa", "kufungua duka ya dawa", "leseni ya duka ya dawa", "pharmacy license", "chemist shop license", "poisons board", "pharmacy and poisons board", "open a pharmacy", "chemist shop kenya", "pharmacy need to operate", "chemist shop need to operate", "licenses does a pharmacy", "licenses does a chemist", "leseni ya duka la dawa", "kufungua duka la dawa", 'chemist', 'pharmacy business',],
    "ca_license": ["communications authority", "ca license kenya", "telecommunications license kenya", "mamlaka ya mawasiliano", "leseni ya mawasiliano"],
    "keproba": ["keproba", "kenya export promotion", "export promotion and branding agency", "brand kenya agency", "usafirishaji nje ya nchi", "kuuza bidhaa nje", 'export', 'exporting', 'sell my products in', 'sell outside kenya', 'uganda', 'tanzania',],
    "no_permit_penalty": ["without a county permit", "operate a business without", "without a permit", "penalty for operating without", "no business permit", "bila kibali cha kaunti", "adhabu ya kutokuwa na kibali"],
    "sole_prop_vs_limited": ["difference between a sole proprietorship", "sole proprietorship and a limited company", "sole proprietorship vs limited company", "sole proprietorship or a limited company", "tofauti kati ya umiliki binafsi na kampuni"],
    "late_filing_penalty": ["penalties for late filing", "late filing of tax returns", "penalty for late filing", "what happens if i file late", "late tax return penalty", "adhabu ya kuchelewa kuwasilisha", "kuchelewa kuwasilisha marejesho"],
    "etims_general": ["what is etims", "why does my business need etims", "why do i need etims", "etims ni nini", "kwa nini nahitaji etims", 'etims for', 'is etims', 'who needs etims', 'etims small',],
    "sacco_vs_bank": ["saccos offer loans differently", "sacco vs bank", "sacco or bank loan", "difference between sacco and bank", "saccos differently from commercial banks", "tofauti kati ya sacco na benki"],
    "business_insurance": ["insurance does a", "business insurance", "insurance for my business", "what insurance", "bima ya biashara", "bima gani", "nahitaji bima"],
    "registration": ["register a business name", "business name registration", "steps to register a business", "register a small business", "register a business in kenya", "how to register a business", "start a business in kenya", "steps to start a business", "kusajili biashara", "naweza kusajili biashara", "jinsi ya kusajili biashara", "kuanzisha biashara", "nataka kusajili", 'regista biznes', 'register biznes', 'biznes name',],
    'start_business': ['start a business', 'start a small business', 'starting a business', 'start my business', 'open a business', 'set up a business', 'begin a business', 'is it a must to register', 'must i register', 'must register', 'register before', 'before i start', 'start operating', 'kuanzisha biashara', 'kuanza biashara', 'kufungua biashara', 'nataka kuanza biashara'],
    'afcfta': ['afcfta', 'african continental free trade', 'continental free trade area', 'other african countries', 'export to africa', 'export to african countries', 'afcfta certificate of origin', 'rules of origin', 'eneo huru la biashara', 'nchi nyingine za afrika', 'kuuza nje afrika'],
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
