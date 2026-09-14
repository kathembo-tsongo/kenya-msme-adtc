import json

examples = [
{"messages": [
    {"role": "system", "content": "You are a helpful assistant advising Kenyan MSME operators on tax, registration, financing, and regulatory compliance."},
    {"role": "user", "content": "How do I register a trademark for my business logo in Kenya, and how much does it cost?"},
    {"role": "assistant", "content": "Trademark registration in Kenya is handled by **KIPI** (Kenya Industrial Property Institute) under the Trade Marks Act. The process: run a **TM27 search** first to check for conflicting marks, choose your **Nice classification** (the category your goods/services fall under), file the **TM2 application**, go through KIPI's examination, and if accepted, your mark is published in the Industrial Property Journal for a **60-day opposition window**. If unopposed, you receive your registration certificate, valid for **10 years** (renewable indefinitely).\n\nOn cost: KIPI charges separate fees for filing, examination, and registration, and the exact total depends on your number of classes and whether you use an agent. I'd confirm the current fee schedule directly on **KIPI's website** rather than rely on a fixed figure, since published fees have varied across sources I've seen. Budget for professional agent fees too if you use one, typically an additional cost on top of KIPI's own fees."}
]},
{"messages": [
    {"role": "system", "content": "You are a helpful assistant advising Kenyan MSME operators on tax, registration, financing, and regulatory compliance."},
    {"role": "user", "content": "I want to put my new employee on probation for a year to be safe. Is that allowed?"},
    {"role": "assistant", "content": "Not directly, but you can get close to it. Under **Section 42 of the Employment Act 2007**, a probationary period cannot exceed **6 months initially**, but it can be extended for a further period of **not more than 6 months** with the employee's written consent \u2014 making the maximum possible aggregate **12 months**, not a straight 1-year probation from the start.\n\nMost employers actually use a shorter period (commonly 3 months) as standard practice, reserving the full 6-month (or extended) period for more senior or technical roles. Also worth knowing: probationary employees are excluded from Section 41's fair-hearing requirement before termination, but any dismissal must still be non-discriminatory and for a legitimate reason \u2014 courts do scrutinize very long or repeatedly-extended probation periods as potentially unfair."}
]},
{"messages": [
    {"role": "system", "content": "You are a helpful assistant advising Kenyan MSME operators on tax, registration, financing, and regulatory compliance."},
    {"role": "user", "content": "I'm a young entrepreneur and I heard the government sets aside tenders for people like me. What is that, and how do I access it?"},
    {"role": "assistant", "content": "You're thinking of **AGPO** (Access to Government Procurement Opportunities), which legally reserves **30% of all government procurement** for enterprises owned by youth, women, and persons with disabilities.\n\nFor the youth category specifically, your business must be **at least 70% owned by Kenyan citizens aged 18-35**, with all directors/partners/proprietors falling in that age bracket. To register: have your business legally registered (sole proprietorship, partnership, or company), gather your registration certificate, KRA PIN/VAT certificate, Tax Compliance Certificate, and (for companies) your CR12 or (for partnerships) your partnership deed, then register directly at **agpo.go.ke**. Once certified, your AGPO status is valid across all procuring entities \u2014 national ministries, counties, and parastatals \u2014 for the reserved tenders in that 30% pool."}
]},
{"messages": [
    {"role": "system", "content": "You are a helpful assistant advising Kenyan MSME operators on tax, registration, financing, and regulatory compliance."},
    {"role": "user", "content": "I want to borrow through the Hustler Fund specifically for my business, not just a personal loan. What's the difference?"},
    {"role": "assistant", "content": "The basic **Personal Loan** (KES 500 to KES 50,000, 8% per annum, repayable in 14 days) can technically be used for anything, business or personal \u2014 it's the entry-level tier everyone starts with via *254#.\n\nFor business specifically, Hustler Fund also offers group-based **Biashara/Enterprise loans** (for chamas, cooperatives, or registered groups) and higher-tier loans for **registered businesses with a KRA PIN**, both at the same 8% per annum rate but with larger amounts and longer repayment periods (up to several months) than the personal tier. Exact current limits for these business tiers can vary, so confirm your specific eligible amount via the Hustler Fund app or *254# once you've built some repayment history on the personal tier \u2014 your loan limit and access to higher products grows with consistent on-time repayment."}
]},
]

with open("new_training_examples_batch4.jsonl", "w", encoding="utf-8") as f:
    for ex in examples:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

print(f"Wrote {len(examples)} training examples to new_training_examples_batch4.jsonl")
