with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

changes = []

en_anchor = '''        "and activate it by dialing *234# on the registered line."
    ),
}'''

en_new = '''        "and activate it by dialing *234# on the registered line."
    ),
    "class_r_permit": (
        "Go to the **Kenya eFNS portal** on eCitizen and apply for a **Class R "
        "Permit** -- the special permit for East African Community nationals "
        "(Burundi, DR Congo, Rwanda, South Sudan, Tanzania, Uganda), covering "
        "residing, working, trading, or running a business in Kenya. The "
        "permit itself is **free** (KES 0 processing, KES 0 issuance), "
        "gazetted under the Kenya Citizenship and Immigration Amendment "
        "Regulations 2024. You will separately need a **Foreigner Certificate "
        "(Alien Card)**, which costs **KES 5,000 per year**.\\n\\nTypical "
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
        "Submit.\\n\\nIf your returns and payments are up to date, it's often "
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
        "**12 months**, not a straight 1-year probation from the start.\\n\\n"
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
        "from that group.\\n\\nTo register: have your business legally "
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
        "needs, accessible via *254#.\\n\\nFor business specifically, Hustler "
        "Fund also offers group-based **Biashara/Enterprise loans** (for "
        "chamas, cooperatives, or registered groups) and higher-tier loans "
        "for **registered businesses with a KRA PIN**, both at the same 8% "
        "per annum rate but with larger amounts and longer repayment periods "
        "than the personal tier. Your loan limit and access to higher tiers "
        "grows with consistent on-time repayment history."
    ),
}'''

if en_anchor not in content:
    print("ERROR: could not find English anchor. No changes made to CANNED_ANSWERS.")
else:
    content = content.replace(en_anchor, en_new, 1)
    changes.append("English CANNED_ANSWERS: added 5 new topics")

with open("rag_server.py", "w", encoding="utf-8") as f:
    f.write(content)

print("\n".join(changes) if changes else "No changes were made -- check errors above.")

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("SYNTAX CHECK: PASSED")
except SyntaxError as e:
    print(f"SYNTAX CHECK: FAILED -- {e}")
