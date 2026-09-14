import json

examples = [
{"messages": [
    {"role": "system", "content": "You are a helpful assistant advising Kenyan MSME operators on tax, registration, financing, and regulatory compliance."},
    {"role": "user", "content": "I sell supplies to other small businesses, not directly to the public. Do I really need to issue eTIMS invoices for those transactions?"},
    {"role": "assistant", "content": "Yes \u2014 arguably more so than for cash retail sales. When you sell to another business, they need a valid **eTIMS invoice with your KRA PIN and their buyer PIN** to claim their own input VAT or expense deduction. If you can't issue one, a business buyer will eventually switch to a supplier who can, since your invoice is what protects their own tax position.\n\nIf your annual turnover is below **KES 5,000,000**, a simplified 'reverse invoicing' arrangement can apply, where the buyer issues the invoice on your behalf \u2014 but you're still required to be onboarded to eTIMS. For most small businesses, the free **eTIMS Lite** option (web portal or USSD *222#) is the simplest way to comply. Non-compliance penalties can reach up to **KES 1,000,000 or 10% of the tax involved**, whichever is higher, so it's worth setting up properly even if you only deal B2B."}
]},
{"messages": [
    {"role": "system", "content": "You are a helpful assistant advising Kenyan MSME operators on tax, registration, financing, and regulatory compliance."},
    {"role": "user", "content": "My company's financial year runs from July to June instead of the calendar year. How does that change my tax filing deadlines?"},
    {"role": "assistant", "content": "Your deadlines shift to follow your own financial year-end rather than the standard calendar-year dates. Your **corporation tax return is due within six months after your financial year-end** \u2014 so with a June year-end, that's by **31 December**, not the following June 30 that calendar-year companies use.\n\nYour **instalment tax payments** are also relative to your own year: due on the 20th day of the 4th, 6th, 9th, and 12th months of *your* financial year, not fixed calendar months. You do need KRA's approval if you ever want to change your financial year-end. Keep in mind that individual (not company) tax return deadlines are governed by separate rules and are moving to a fixed calendar date under recent Finance Act changes, so don't assume the same shift applies to your personal returns if you're also filing individually."}
]},
{"messages": [
    {"role": "system", "content": "You are a helpful assistant advising Kenyan MSME operators on tax, registration, financing, and regulatory compliance."},
    {"role": "user", "content": "The KRA website is confusing. What's the simplest way to actually apply for a Tax Compliance Certificate for my business?"},
    {"role": "assistant", "content": "It's simpler than the rest of the KRA site once you know exactly where to click: log in to **itax.kra.go.ke** with your business's KRA PIN (not a director's personal PIN), go to the **'Certificates'** menu, and select **'Apply for Tax Compliance Certificate (TCC)'**. The form auto-fills your registered details \u2014 review them, select your reason for applying (tender, licensing, etc.), and click Submit.\n\nIf your returns and payments are up to date, it's often approved automatically within a day or two and emailed to you. If something's outstanding \u2014 an unfiled return, unpaid balance, or (since late 2024) eTIMS non-compliance \u2014 the system will flag it so you can resolve it before reapplying. It's **free**, and once issued it's valid for 12 months."}
]},
{"messages": [
    {"role": "system", "content": "You are a helpful assistant advising Kenyan MSME operators on tax, registration, financing, and regulatory compliance."},
    {"role": "user", "content": "I don't have any full-time employees right now. Do I still need to file NSSF and SHIF returns?"},
    {"role": "assistant", "content": "If you've never registered as an employer for NSSF/SHIF because you've genuinely never had an employee under a contract of service, you generally don't have an obligation to begin with \u2014 these schemes are built around the employer-employee relationship. If you're self-employed with no staff, participation is currently voluntary rather than mandatory.\n\nHowever, if you're already **registered** as an employer (for example, you had staff before and let them go, or your staffing is seasonal), the exact procedure for whether you need to file a 'Nil' return during a period with no active employees is something I'd confirm directly with **NSSF** and the **SHA (Social Health Authority)** \u2014 I don't want to guess at a specific filing mechanic I'm not fully certain of, since getting a compliance filing wrong can carry real penalties."}
]},
{"messages": [
    {"role": "system", "content": "You are a helpful assistant advising Kenyan MSME operators on tax, registration, financing, and regulatory compliance."},
    {"role": "user", "content": "I'm setting up a small accounting practice. Do I need a county trade license on top of my professional certification?"},
    {"role": "assistant", "content": "Yes \u2014 your professional certification doesn't replace the standard county trade license. As a practicing accountant, you need **both**: your practicing certificate from the **ICPAK** (Institute of Certified Public Accountants of Kenya), which governs your professional standing, **and** a standard county-level trade license/business permit, the same as most other businesses operating in that county.\n\nThe same layered pattern applies to other regulated professions \u2014 lawyers need a Law Society of Kenya practicing certificate alongside standard business registration, for example. Confirm the exact county trade license category and fee with your specific **county government**, since these vary by location."}
]},
]

with open("new_training_examples_batch3.jsonl", "w", encoding="utf-8") as f:
    for ex in examples:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

print(f"Wrote {len(examples)} training examples to new_training_examples_batch3.jsonl")
