import json
import random

random.seed(31)
SYS = "You are a helpful assistant advising Kenyan MSME operators on tax, registration, financing, and regulatory compliance."
examples = []
biz_types = ["a small retail shop", "a salon", "a mechanic workshop", "a restaurant", "a tech startup",
             "a farming business", "a boutique", "a hardware store", "a barber shop"]

def add(user, assistant):
    examples.append({"messages": [{"role": "system", "content": SYS}, {"role": "user", "content": user}, {"role": "assistant", "content": assistant}]})

pin_answer = ("**Getting a KRA PIN**:\n\n1. Go to iTax at itax.kra.go.ke\n2. Log in / register using your national ID\n"
              "3. Click \"Register\" -- your PIN is issued once you complete registration\n\nYou'll need this PIN before "
              "registering for VAT, PAYE, or any other tax obligation.")
pin_qs = [
    "I forgot my KRA iTax password. How do I recover my account?",
    "Does every single business in Kenya need a KRA PIN, no exceptions?",
    "How do I update my personal details on my existing KRA PIN?",
]
for _ in range(6):
    add(random.choice(pin_qs), pin_answer)

etims_answer = ("When you sell to another business, they need a valid **eTIMS invoice with your KRA PIN and their "
                 "buyer PIN** to claim their own input VAT or expense deduction -- so yes, it's necessary even for "
                 "B2B sales. If your annual turnover is below **KES 5,000,000**, a simplified 'reverse invoicing' "
                 "arrangement can apply. The free **eTIMS Lite** option (web or USSD *222#) is the simplest "
                 "compliance route. Non-compliance penalties can reach up to **KES 1,000,000 or 10% of the tax "
                 "involved**, whichever is higher.")
etims_qs2 = [
    "Can I use eTIMS on my phone without a computer or point-of-sale system?",
    "What happens if my internet is down and I can't issue an eTIMS invoice right away?",
    "Do very small shops with low transaction volumes still need eTIMS?",
]
for _ in range(6):
    add(random.choice(etims_qs2), etims_answer)

license_answer = ("Business/trade licenses in Kenya are administered at the **county level**, not nationally, so exact "
                   "categories, fees, and thresholds vary by county. You'll generally need a **Single Business Permit** "
                   "from your county government, renewed annually. Confirm the exact category and fee for your specific "
                   "business type and location directly with your county's business licensing office.")
license_qs2 = [
    "Do I need a permit to run {biz} entirely from home?",
    "What happens if my county business permit expires and I keep operating?",
    "Do online-only businesses still need a county trade license?",
]
for _ in range(6):
    q = random.choice(license_qs2).format(biz=random.choice(biz_types))
    add(q, license_answer)

print(f"Generated {len(examples)} final examples")

with open("generated_qualitative_final.jsonl", "w", encoding="utf-8") as f:
    for ex in examples:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

print(f"Wrote {len(examples)} examples to generated_qualitative_final.jsonl")
