import json

examples = [
{"messages": [
    {"role": "system", "content": "You are a helpful assistant advising Kenyan MSME operators on tax, registration, financing, and regulatory compliance."},
    {"role": "user", "content": "What documents do I need to open a business bank account for my registered retail shop in Kenya?"},
    {"role": "assistant", "content": "For a registered business, banks typically require: your **business registration certificate** (from BRS/eCitizen), your **KRA PIN certificate** for the business, and the national ID plus personal KRA PIN of the owner or directors. If you're a limited company, you'll also usually need a **board resolution** authorizing the account opening and naming signatories, plus your certificate of incorporation and memorandum/articles of association.\n\nBanks vary in their minimum opening deposit and any additional requirements (proof of physical business address, passport photos, etc.), so I'd confirm the exact checklist with your chosen bank directly rather than assume it's identical everywhere."}
]},
{"messages": [
    {"role": "system", "content": "You are a helpful assistant advising Kenyan MSME operators on tax, registration, financing, and regulatory compliance."},
    {"role": "user", "content": "I want to import textiles from another country to resell in Kenya. What do I need to do?"},
    {"role": "assistant", "content": "You'll generally need to register with **KRA** for an import declaration and use the **Integrated Customs Management System (iCMS)** to lodge your import entry, pay applicable import duty and VAT based on the goods' tariff classification, and clear the shipment through customs. Depending on the specific type of textile, you may also need a **KEBS** conformity/standardization certificate before the goods can be cleared.\n\nExact timelines and additional permit requirements can vary depending on the product and current customs procedures, so I'd confirm the specific process and any lead time needed with **KRA Customs** or a licensed customs clearing agent before your shipment arrives, rather than assume a fixed timeline."}
]},
{"messages": [
    {"role": "system", "content": "You are a helpful assistant advising Kenyan MSME operators on tax, registration, financing, and regulatory compliance."},
    {"role": "user", "content": "What's the difference in how a partnership versus a private limited company is taxed in Kenya?"},
    {"role": "assistant", "content": "A **partnership** is not taxed as a separate entity in Kenya \u2014 profits flow through to the individual partners, who each declare their share of partnership income on their personal income tax return and pay tax at individual rates. The partnership itself files an informational return but doesn't pay corporate tax.\n\nA **private limited company**, by contrast, is a separate legal entity and is taxed directly on its profits at the corporate income tax rate (currently 30% for resident companies). If the company later distributes profits to shareholders as dividends, those dividends can also attract withholding tax at the shareholder level \u2014 meaning company profits can effectively be taxed twice (once at the company level, once on dividends), which doesn't happen with a partnership's pass-through treatment.\n\nWhich structure is better depends on your specific situation \u2014 I'd recommend discussing with a tax advisor or the **KRA** given your expected profit levels and reinvestment plans."}
]},
]

with open("provenance_v2_new_examples_batch2.jsonl", "w", encoding="utf-8") as f:
    for ex in examples:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

print(f"Wrote {len(examples)} additional training examples to provenance_v2_new_examples_batch2.jsonl")
