import json
import random

random.seed(7)
SYS = "You are a helpful assistant advising Kenyan MSME operators on tax, registration, financing, and regulatory compliance."
examples = []

biz_types = ["a small retail shop", "a salon", "a mechanic workshop", "a restaurant", "a tech startup",
             "a farming business", "a boutique", "a hardware store", "a barber shop", "a trading business"]
locations = ["Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret", "Kiambu", "Machakos"]

def add(user, assistant):
    examples.append({"messages": [{"role": "system", "content": SYS}, {"role": "user", "content": user}, {"role": "assistant", "content": assistant}]})

reg_answer = ("**Registering a business name in Kenya**:\n\n1. Search for name availability via the eCitizen portal "
              "(ecitizen.go.ke) or the Business Registration Service (brs.go.ke)\n2. Submit your registration with your "
              "national ID and KRA PIN\n3. Once approved, you'll receive a business registration certificate")
reg_qs = [
    "I want to start {biz} in {loc}. What are the basic steps to register it?",
    "How do I register my business name for {biz} I'm opening in {loc}?",
    "Nataka kufungua {biz} {loc}, ni steps gani za kuregister?",
    "What's the process to register a small business in Kenya?",
    "Can I register my business online without visiting an office?",
    "How long does business registration usually take in Kenya?",
]
for _ in range(8):
    q = random.choice(reg_qs).format(biz=random.choice(biz_types), loc=random.choice(locations))
    add(q, reg_answer)

pin_answer = ("**Getting a KRA PIN**:\n\n1. Go to iTax at itax.kra.go.ke\n2. Log in / register using your national ID\n"
              "3. Click \"Register\" -- your PIN is issued once you complete registration\n\nYou'll need this PIN before "
              "registering for VAT, PAYE, or any other tax obligation.")
pin_qs = [
    "How do I get a KRA PIN for my business?",
    "Do I need a separate KRA PIN for my {biz}, or can I use my personal one?",
    "Nataka KRA PIN ya biashara yangu, nifanye aje?",
    "What's the process to register for a KRA PIN online?",
]
for _ in range(6):
    q = random.choice(pin_qs).format(biz=random.choice(biz_types))
    add(q, pin_answer)

vat_answer = ("VAT registration is mandatory once your annual taxable turnover exceeds **KES 5,000,000**; register via "
              "iTax. Businesses below this threshold are not required to register, though voluntary registration is "
              "possible in some cases. The standard VAT rate is 16%.")
vat_qs = [
    "When is {biz} required to register for VAT in Kenya?",
    "My {biz} is approaching KES 5 million in annual sales. Do I need to register for VAT now?",
    "What is the VAT registration threshold for a small business?",
    "Should my {biz} register for VAT if we're still below KES 5,000,000?",
]
for _ in range(6):
    q = random.choice(vat_qs).format(biz=random.choice(biz_types))
    add(q, vat_answer)

term_answer = ("Terminating an employee in Kenya is governed by the **Employment Act 2007**. You must have a valid, "
               "fair reason (e.g. misconduct, poor performance, redundancy) and follow due process -- give notice "
               "(per contract or statutory minimum), explain the reason in writing, and give the employee a genuine "
               "chance to respond before finalizing the decision. Skipping notice or the hearing step can make a "
               "dismissal unfair even with a valid underlying reason. Redundancy specifically has additional rules "
               "(notifying the labour office, selection criteria, severance pay).")
term_qs = [
    "What is the correct process to terminate an employee at my {biz}?",
    "Nataka kumfukuza worker wangu, nifanye nini kisheria?",
    "Can I fire an employee immediately for poor performance?",
    "What notice period do I owe an employee I'm letting go?",
    "My employee keeps coming late. Can I dismiss them without warning?",
]
for _ in range(8):
    q = random.choice(term_qs).format(biz=random.choice(biz_types))
    add(q, term_answer)

license_answer = ("Business/trade licenses in Kenya are administered at the **county level**, not nationally, so exact "
                   "categories, fees, and thresholds vary by county. You'll generally need a **Single Business Permit** "
                   "from your county government, renewed annually. Confirm the exact category and fee for your specific "
                   "business type and location directly with your county's business licensing office, since these are "
                   "not standardized nationwide.")
license_qs = [
    "Do I need a county business permit for my {biz} in {loc}?",
    "How much does a Single Business Permit cost for {biz}?",
    "What happens if I operate my {biz} without a county trade license?",
    "Nataka permit ya {biz} yangu {loc}, nianze wapi?",
]
for _ in range(8):
    q = random.choice(license_qs).format(biz=random.choice(biz_types), loc=random.choice(locations))
    add(q, license_answer)

print(f"Generated {len(examples)} qualitative variety examples so far")

with open("generated_qualitative_batch1.jsonl", "w", encoding="utf-8") as f:
    for ex in examples:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

print(f"Wrote {len(examples)} examples to generated_qualitative_batch1.jsonl")
