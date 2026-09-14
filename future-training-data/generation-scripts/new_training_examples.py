import json

examples = [
{"messages": [
    {"role": "system", "content": "You are a helpful assistant advising Kenyan MSME operators on tax, registration, financing, and regulatory compliance."},
    {"role": "user", "content": "I run a small salon with annual sales of about KES 3,000,000. Someone told me I need to pay Turnover Tax. What is that and how much would I owe?"},
    {"role": "assistant", "content": "**Turnover Tax (TOT)** applies to Kenyan-resident businesses with annual gross turnover between **KES 1,000,000 and KES 25,000,000** \u2014 your salon falls within that range, so TOT applies to you.\n\nThe rate is a flat **1.5% of gross sales** (not profit), effective under the Finance Act 2023. It's a final tax, meaning you can't deduct business expenses against it, but you also don't file a separate income tax return for this turnover. Note that TOT does not apply to non-residents, and if your turnover later exceeds KES 5,000,000 you'll also need to register for VAT separately.\n\nAt KES 3,000,000 in annual sales, your TOT liability would be roughly KES 45,000 for the year (1.5% x 3,000,000), though I'd confirm the exact filing process with the **KRA**."}
]},
{"messages": [
    {"role": "system", "content": "You are a helpful assistant advising Kenyan MSME operators on tax, registration, financing, and regulatory compliance."},
    {"role": "user", "content": "I just hired my first employee at a monthly salary of KES 45,000. What PAYE do I need to deduct, and when do I have to pay it to KRA?"},
    {"role": "assistant", "content": "**PAYE** is calculated on progressive bands: 10% on the first KES 24,000, 25% on the next KES 8,333 (up to KES 32,333), 30% on the next portion up to KES 500,000, 32.5% up to KES 800,000, and 35% above that. For a KES 45,000 salary, most of it falls in the 30% band.\n\nEvery resident employee is entitled to a **personal relief of KES 2,400 per month**, which you subtract from the calculated tax before remitting.\n\n**Remittance deadline:** PAYE deducted from a given month's salary must reach KRA by the **9th day of the following month**, filed via the iTax P10 return. Missing this deadline carries a **25% penalty** on the tax due, plus **2% monthly interest** on the unpaid amount \u2014 so it's worth setting a reminder for the 9th of each month."}
]},
{"messages": [
    {"role": "system", "content": "You are a helpful assistant advising Kenyan MSME operators on tax, registration, financing, and regulatory compliance."},
    {"role": "user", "content": "Are there any obligations to SHIF for my small business, or any other obligations I should know about?"},
    {"role": "assistant", "content": "**SHIF (Social Health Insurance Fund)** contributions are charged at **2.75% of gross income**, with no upper cap \u2014 higher earners contribute proportionally more. SHIF replaced the old NHIF flat-rate system from October 2024, and it is not split into employer/employee tiers the way NSSF is.\n\nAs an employer, your main obligation is ensuring SHIF is correctly deducted from each employee's gross pay and remitted on their behalf. For the exact current employer/employee split and remittance process, confirm directly with the **SHA (Social Health Authority)** or your payroll provider, since implementation details can be updated."}
]},
{"messages": [
    {"role": "system", "content": "You are a helpful assistant advising Kenyan MSME operators on tax, registration, financing, and regulatory compliance."},
    {"role": "user", "content": "What is the Affordable Housing Levy and does it apply to a business with just 2 low-wage employees?"},
    {"role": "assistant", "content": "The **Affordable Housing Levy (AHL)** is charged at **1.5% of gross salary from the employee, matched by 1.5% from the employer** \u2014 3% total per employee, per month. Importantly, there is **no minimum income threshold**: it applies to all gross salaried employees regardless of how little they earn, so yes, it applies to your 2 employees even at low wages.\n\nRemittance is due by the 9th working day after month-end via KRA iTax. Late remittance carries a 3% per month penalty on the unpaid amount, so it's worth including in your regular monthly payroll routine alongside PAYE and NSSF."}
]},
{"messages": [
    {"role": "system", "content": "You are a helpful assistant advising Kenyan MSME operators on tax, registration, financing, and regulatory compliance."},
    {"role": "user", "content": "What's the minimum wage I need to pay a general labourer at my shop in Nairobi?"},
    {"role": "assistant", "content": "Kenya does not have a single national minimum wage \u2014 rates are set by occupation, sector, and geographic zone under periodic Regulation of Wages Orders, typically revised around Labour Day (1st May).\n\nAs a reference point, the general (unskilled) labourer minimum in Nairobi, Mombasa, Kisumu, Nakuru, and Eldoret was set at **KES 18,047.40 per month** under the most recent Wage Order, with lower rates in other zones. Skilled roles and sector-specific work (agricultural, security, domestic) have their own, generally higher, statutory minimums.\n\nBecause these rates are revised periodically, confirm the exact current figure for a general labourer in Nairobi via the Ministry of Labour and Social Protection or the current Kenya Gazette Wage Order before finalizing pay."}
]},
{"messages": [
    {"role": "system", "content": "You are a helpful assistant advising Kenyan MSME operators on tax, registration, financing, and regulatory compliance."},
    {"role": "user", "content": "I missed my NSSF remittance deadline for one of my employees last month. What penalty am I looking at?"},
    {"role": "assistant", "content": "Late NSSF remittance carries a penalty of **5% of the outstanding contribution** for each month, or part of a month, that the payment remains late. Some sources also note additional monthly interest on top of this base penalty, so I'd confirm the full current figure directly with **NSSF**.\n\nBeyond the financial penalty, persistent non-compliance can lead to legal action, and as a director you can be held personally liable for unpaid contributions \u2014 so it's worth remitting the overdue amount as soon as possible rather than letting it accumulate further."}
]},
{"messages": [
    {"role": "system", "content": "You are a helpful assistant advising Kenyan MSME operators on tax, registration, financing, and regulatory compliance."},
    {"role": "user", "content": "How do I actually set up an M-Pesa Till number for my shop? Do I do this at my bank?"},
    {"role": "assistant", "content": "You don't set this up through a bank \u2014 Till and Paybill numbers are **Safaricom's** M-Pesa for Business product, so you apply through them directly.\n\nA **Till Number** suits retail/point-of-sale businesses like your shop: one till per outlet, customers pay no fee, and you pay a small settlement fee (roughly 0.5-1%). Apply via m-pesaforbusiness.co.ke or at any Safaricom shop, with your national ID, KRA PIN, business registration documents, and bank details for settlement. Application is free, and once approved you'll get your Till number by SMS and activate it by dialing *234# on the registered line."}
]},
]

with open("provenance_v2_new_examples.jsonl", "w", encoding="utf-8") as f:
    for ex in examples:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

print(f"Wrote {len(examples)} new training examples to provenance_v2_new_examples.jsonl")
