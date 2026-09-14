import json
import random

random.seed(11)
SYS = "You are a helpful assistant advising Kenyan MSME operators on tax, registration, financing, and regulatory compliance."
examples = []
eac_countries = ["Ugandan", "Tanzanian", "Rwandan", "Burundian", "South Sudanese"]
biz_types = ["a small retail shop", "a salon", "a mechanic workshop", "a restaurant", "a tech startup",
             "a farming business", "a boutique", "a hardware store", "a barber shop", "a trading business"]
professions = ["accountant", "lawyer", "architect", "engineer"]

def add(user, assistant):
    examples.append({"messages": [{"role": "system", "content": SYS}, {"role": "user", "content": user}, {"role": "assistant", "content": assistant}]})

classr_answer = ("Go to the **Kenya eFNS portal** on eCitizen and apply for a **Class R Permit** -- the special permit "
                  "for East African Community nationals (Burundi, DR Congo, Rwanda, South Sudan, Tanzania, Uganda), "
                  "covering residing, working, trading, or running a business in Kenya. The permit itself is **free** "
                  "(KES 0 processing, KES 0 issuance), gazetted under the Kenya Citizenship and Immigration Amendment "
                  "Regulations 2024. You'll separately need a **Foreigner Certificate (Alien Card)** at KES 5,000/year. "
                  "Typical documents: valid passport, cover letter, KRA PIN if doing business, and police clearance for "
                  "small-scale traders. Apply online, then print and submit physically at Nyayo House, Nairobi.")
classr_qs = [
    "I'm a {nat} national running {biz} in Kenya without proper documentation. Where do I start?",
    "What permit do East African Community citizens need to legally trade in Kenya?",
    "How does a {nat} small business owner regularize their stay in Kenya?",
]
for _ in range(6):
    q = random.choice(classr_qs).format(nat=random.choice(eac_countries), biz=random.choice(biz_types))
    add(q, classr_answer)

etims_answer = ("When you sell to another business, they need a valid **eTIMS invoice with your KRA PIN and their "
                 "buyer PIN** to claim their own input VAT or expense deduction -- so yes, it's necessary even for "
                 "B2B sales, arguably more so than cash retail. If your annual turnover is below **KES 5,000,000**, "
                 "a simplified 'reverse invoicing' arrangement can apply. The free **eTIMS Lite** option (web or USSD "
                 "*222#) is the simplest compliance route for most small businesses. Non-compliance penalties can "
                 "reach up to **KES 1,000,000 or 10% of the tax involved**, whichever is higher.")
etims_qs = [
    "Does my {biz} need to issue eTIMS invoices even for small, informal sales?",
    "I sell to other businesses, not the public. Do I still need eTIMS?",
    "What happens if my {biz} doesn't comply with eTIMS?",
]
for _ in range(6):
    q = random.choice(etims_qs).format(biz=random.choice(biz_types))
    add(q, etims_answer)

tcc_answer = ("Log in to **itax.kra.go.ke** with your business KRA PIN, go to the **'Certificates'** menu, select "
              "**'Apply for Tax Compliance Certificate (TCC)'**, review your auto-filled details, select your reason "
              "for applying, and click Submit. If compliant, it's often approved within a day or two and emailed to "
              "you. It's **free** and valid for **12 months**. Unfiled returns, unpaid balances, or eTIMS "
              "non-compliance can block approval until resolved.")
tcc_qs = [
    "What's the simplest way to apply for a Tax Compliance Certificate for {biz}?",
    "How do I get a TCC for a government tender application?",
    "Why might my Tax Compliance Certificate application be rejected?",
]
for _ in range(6):
    q = random.choice(tcc_qs).format(biz=random.choice(biz_types))
    add(q, tcc_answer)

tm_answer = ("Trademark registration is handled by **KIPI** under the Trade Marks Act: run a **TM27 search** for "
             "conflicting marks, choose your **Nice classification**, file the **TM2 application**, go through "
             "examination, then a **60-day opposition window** after publication in the Industrial Property Journal. "
             "If unopposed, you get a certificate valid for **10 years** (renewable). Fees vary by number of classes "
             "and whether you use an agent -- confirm the current schedule directly with KIPI.")
tm_qs = [
    "How do I protect my {biz}'s brand name and logo legally?",
    "Someone might copy my business name. How do I register a trademark in Kenya?",
    "What's the process and typical timeline for trademark registration?",
]
for _ in range(6):
    q = random.choice(tm_qs).format(biz=random.choice(biz_types))
    add(q, tm_answer)

prob_answer = ("Under **Section 42 of the Employment Act 2007**, probation cannot exceed **6 months initially**, "
               "extendable once for a further **6 months** with the employee's written consent -- maximum aggregate "
               "**12 months**. Most employers use 3 months as standard practice. Probationary employees are excluded "
               "from Section 41's fair-hearing requirement before termination, but dismissal must still be "
               "non-discriminatory and for a legitimate reason.")
prob_qs = [
    "How long can I legally keep a new employee on probation at {biz}?",
    "Can I put a new hire on a full year of probation to be safe?",
    "What are my rights during an employee's probation period?",
]
for _ in range(6):
    q = random.choice(prob_qs).format(biz=random.choice(biz_types))
    add(q, prob_answer)

agpo_answer = ("**AGPO** (Access to Government Procurement Opportunities) reserves **30% of government procurement** "
               "for enterprises owned by youth (18-35), women, and persons with disabilities, each requiring **70% "
               "ownership and 100% leadership** from that group. Register your business, gather your registration "
               "certificate, KRA PIN/VAT certificate, TCC, and CR12 (companies) or partnership deed, then register "
               "at **agpo.go.ke**. Once certified, your status applies across all national and county procuring "
               "entities.")
agpo_qs = [
    "As a young entrepreneur, how do I access government tenders set aside for people like me?",
    "What is AGPO and how does a woman-owned {biz} register for it?",
    "How does the 30% government procurement set-aside for youth and women actually work?",
]
for _ in range(6):
    q = random.choice(agpo_qs).format(biz=random.choice(biz_types))
    add(q, agpo_answer)

hustler_answer = ("The **Personal Loan** tier (KES 500-50,000, 8% p.a., 14-day repayment) can be used for business or "
                   "personal needs, accessible via *254#. For business specifically, group-based Biashara/Enterprise "
                   "loans and higher tiers for registered businesses with a KRA PIN offer larger amounts and longer "
                   "repayment periods, still at 8% p.a. Your loan limit and access to higher tiers grows with "
                   "consistent on-time repayment history.")
hustler_qs = [
    "How does the Hustler Fund work for someone wanting to grow {biz}?",
    "What's the difference between the personal and business Hustler Fund products?",
    "How do I increase my Hustler Fund loan limit over time?",
]
for _ in range(6):
    q = random.choice(hustler_qs).format(biz=random.choice(biz_types))
    add(q, hustler_answer)

mw_answer = ("Kenya does **not** have a single national minimum wage -- rates are set by occupation, sector, and "
             "geographic zone under periodic Regulation of Wages Orders, revised around Labour Day. As a reference: "
             "the general (unskilled) labourer minimum in Nairobi, Mombasa, Kisumu, Nakuru, and Eldoret was set at "
             "**KES 18,047.40/month** under the most recent Wage Order, with lower rates elsewhere and higher rates "
             "for skilled/sector-specific roles. Confirm the exact current figure for your occupation and zone via "
             "the Ministry of Labour and Social Protection.")
mw_qs = [
    "What's the minimum wage I should pay a general worker at my {biz} in {loc}?",
    "Is there one fixed minimum wage figure for all of Kenya?",
    "How much should I pay an unskilled labourer legally in {loc}?",
]
locations = ["Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret"]
for _ in range(6):
    q = random.choice(mw_qs).format(biz=random.choice(biz_types), loc=random.choice(locations))
    add(q, mw_answer)

nssfpen_answer = ("Late NSSF remittance carries a penalty of **5% of the outstanding contribution** for each month, "
                   "or part of a month, that payment remains late. Some sources note additional monthly interest on "
                   "top of this -- confirm the full current figure with NSSF directly. Persistent non-compliance can "
                   "lead to legal action, and directors can be held personally liable for unpaid contributions.")
nssfpen_qs = [
    "I'm late on NSSF remittance for {biz}. What penalty am I facing?",
    "What happens if I consistently miss NSSF payment deadlines?",
    "Is there a grace period before NSSF penalties kick in?",
]
for _ in range(6):
    q = random.choice(nssfpen_qs).format(biz=random.choice(biz_types))
    add(q, nssfpen_answer)

mpesa_answer = ("Apply through **Safaricom**, not a bank. A **Till Number** suits retail/point-of-sale (one till per "
                 "outlet, customer pays no fee, merchant pays ~0.5-1% settlement fee). A **Paybill Number** suits "
                 "recurring collections with account references. Apply via m-pesaforbusiness.co.ke or any Safaricom "
                 "shop with your national ID, KRA PIN, business registration documents, and bank details. Application "
                 "is **free**; activate via *234# once approved.")
mpesa_qs = [
    "How do I set up a Till number for {biz}?",
    "What's the difference between Paybill and Till for my business?",
    "Do I apply for M-Pesa Till at a bank or through Safaricom directly?",
]
for _ in range(6):
    q = random.choice(mpesa_qs).format(biz=random.choice(biz_types))
    add(q, mpesa_answer)

prof_answer = ("Yes -- professional certification doesn't replace the standard county trade license. A practicing "
               "**{prof}** needs both their professional body's practicing certificate (e.g. ICPAK for accountants, "
               "Law Society of Kenya for lawyers) **and** a standard county-level trade license/business permit, the "
               "same as most other businesses. Confirm the exact county trade license category and fee with your "
               "specific county government.")
prof_qs = [
    "I'm a practicing {prof}. Do I need a county trade license on top of my professional certification?",
    "Does my professional body registration exempt my {prof} practice from county business permits?",
]
for _ in range(5):
    prof = random.choice(professions)
    q = random.choice(prof_qs).format(prof=prof)
    add(q, prof_answer.format(prof=prof))

print(f"Generated {len(examples)} more qualitative examples")

with open("generated_qualitative_batch2.jsonl", "w", encoding="utf-8") as f:
    for ex in examples:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

print(f"Wrote {len(examples)} examples to generated_qualitative_batch2.jsonl")
