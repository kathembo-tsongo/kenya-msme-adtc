import json
import random

random.seed(23)
SYS = "You are a helpful assistant advising Kenyan MSME operators on tax, registration, financing, and regulatory compliance."
examples = []
biz_types = ["a small retail shop", "a salon", "a mechanic workshop", "a restaurant", "a tech startup",
             "a farming business", "a boutique", "a hardware store", "a barber shop", "a trading business",
             "a photography business", "a cleaning company", "a catering business"]
locations = ["Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret", "Kiambu", "Machakos", "Nyeri"]

def add(user, assistant):
    examples.append({"messages": [{"role": "system", "content": SYS}, {"role": "user", "content": user}, {"role": "assistant", "content": assistant}]})

reg_answer = ("**Registering a business name in Kenya**:\n\n1. Search for name availability via the eCitizen portal "
              "(ecitizen.go.ke) or the Business Registration Service (brs.go.ke)\n2. Submit your registration with your "
              "national ID and KRA PIN\n3. Once approved, you'll receive a business registration certificate")
reg_qs2 = [
    "Can I register {biz} using just my phone, without a computer?",
    "What documents do I need on hand before registering {biz} in {loc}?",
    "Is there a difference between registering a business name and registering a limited company?",
    "I want to register {biz} with my spouse as a co-owner. Is that possible?",
    "Can I reserve a business name before I'm ready to fully register?",
]
for _ in range(8):
    q = random.choice(reg_qs2).format(biz=random.choice(biz_types), loc=random.choice(locations))
    add(q, reg_answer)

vat_answer = ("VAT registration is mandatory once your annual taxable turnover exceeds **KES 5,000,000**; register via "
              "iTax. Businesses below this threshold are not required to register, though voluntary registration is "
              "possible in some cases. The standard VAT rate is 16%.")
vat_qs2 = [
    "My {biz} is well below KES 5 million in sales. Can I still voluntarily register for VAT?",
    "What's the current standard VAT rate in Kenya?",
    "If my {biz} crosses the VAT threshold partway through the year, when exactly do I need to register?",
]
for _ in range(6):
    q = random.choice(vat_qs2).format(biz=random.choice(biz_types))
    add(q, vat_answer)

term_answer = ("Terminating an employee in Kenya is governed by the **Employment Act 2007**. You must have a valid, "
               "fair reason (e.g. misconduct, poor performance, redundancy) and follow due process -- give notice "
               "(per contract or statutory minimum), explain the reason in writing, and give the employee a genuine "
               "chance to respond before finalizing the decision. Skipping notice or the hearing step can make a "
               "dismissal unfair even with a valid underlying reason. Redundancy specifically has additional rules "
               "(notifying the labour office, selection criteria, severance pay).")
term_qs2 = [
    "What is redundancy and how is it different from a normal dismissal?",
    "Do I need to pay severance if I let an employee go at {biz}?",
    "What if my employee at {biz} just stopped coming to work without notice?",
    "Can an employee take my {biz} to court over a dismissal they think was unfair?",
]
for _ in range(8):
    q = random.choice(term_qs2).format(biz=random.choice(biz_types))
    add(q, term_answer)

dp_answer = ("Under the **Data Protection Act, 2019**, if you collect customer information (phone numbers, names, "
             "addresses) for your business, you're generally required to have a lawful basis for collecting it "
             "(such as the customer's consent), use it only for the purpose you collected it for, and take "
             "reasonable steps to keep it secure. Avoid sharing customer data with third parties without their "
             "knowledge, and be cautious about sending unsolicited promotional messages without consent. For "
             "specific compliance obligations depending on your business size and how you process data, the "
             "**Office of the Data Protection Commissioner (ODPC)** is the relevant authority to confirm with.")
dp_qs = [
    "Can I collect and store my customers' phone numbers at {biz}?",
    "What are my responsibilities under data protection law when running {biz}?",
    "Can I send promotional SMS to my customer list without asking first?",
]
for _ in range(6):
    q = random.choice(dp_qs).format(biz=random.choice(biz_types))
    add(q, dp_answer)

ip_answer = ("If someone is using your business name, logo, or a confusingly similar brand without permission, your "
             "strongest protection is a **registered trademark** with KIPI -- without one, you have weaker legal "
             "footing to stop them. If you already have a registered trademark, you can pursue enforcement through "
             "the courts. If you haven't registered yet, this is worth doing promptly, since trademark rights in "
             "Kenya are generally tied to registration rather than just first use. For an urgent situation, "
             "consulting an IP lawyer about your specific options (including a formal cease-and-desist letter) is "
             "worth doing before taking further action.")
ip_qs = [
    "Someone is using a name almost identical to my {biz}. What can I do?",
    "A competitor copied my logo. Do I have any legal recourse?",
]
for _ in range(5):
    q = random.choice(ip_qs).format(biz=random.choice(biz_types))
    add(q, ip_answer)

books_answer = ("Keep a simple, consistent record of: daily sales, expenses, stock purchases, and amounts customers "
                "or suppliers owe you (or you owe them). Even a basic notebook, spreadsheet, or phone app is fine as "
                "long as it's consistent and dated. Keep receipts and invoices for at least the period KRA can "
                "audit back to (commonly cited as several years -- confirm the exact current retention period, since "
                "it's worth being precise here). Good records make tax filing, loan applications, and tracking "
                "whether you're actually profitable much easier.")
books_qs = [
    "What records should I be keeping for {biz} on a daily basis?",
    "How long should I keep my business receipts and invoices?",
    "How do I know if {biz} is actually making a profit, not just generating sales?",
]
for _ in range(6):
    q = random.choice(books_qs).format(biz=random.choice(biz_types))
    add(q, books_answer)

print(f"Generated {len(examples)} more examples in this batch")

with open("generated_qualitative_batch4.jsonl", "w", encoding="utf-8") as f:
    for ex in examples:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

print(f"Wrote {len(examples)} examples to generated_qualitative_batch4.jsonl")
