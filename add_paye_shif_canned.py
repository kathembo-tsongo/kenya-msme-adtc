"""Add PAYE bands and SHIF rate as verified canned answers, bilingual.
Anchors on the exact, unique closing text of the existing turnover_tax
entries in each dict, inserting new content immediately after it --
i.e. still INSIDE the dict, before its closing brace."""

with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

changes_made = []

en_anchor = '''        "Confirm your specific position via iTax (itax.kra.go.ke), since "
        "individual circumstances can affect eligibility."
    ),'''

en_new_entries = '''        "Confirm your specific position via iTax (itax.kra.go.ke), since "
        "individual circumstances can affect eligibility."
    ),
    "paye_bands": (
        "**PAYE tax bands in Kenya** are progressive, applied monthly "
        "(Finance Act 2023):\\n\\n"
        "- **10%** on the first KES 24,000\\n"
        "- **25%** on the next KES 8,333 (KES 24,001-32,333)\\n"
        "- **30%** on KES 32,334-500,000\\n"
        "- **32.5%** on KES 500,001-800,000\\n"
        "- **35%** above KES 800,000\\n\\n"
        "Every resident employee is entitled to a **personal relief of "
        "KES 2,400 per month** (KES 28,800 per year), subtracted from the "
        "calculated tax. Non-residents do not qualify for this relief. "
        "PAYE is calculated on taxable income after NSSF, SHIF, and "
        "Affordable Housing Levy deductions."
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
    ),'''

if en_anchor not in content:
    print("ERROR: could not find English anchor text. No changes made to CANNED_ANSWERS.")
else:
    content = content.replace(en_anchor, en_new_entries, 1)
    changes_made.append("English CANNED_ANSWERS updated (paye_bands, shif_rate)")

sw_anchor = '''        "Thibitisha msimamo wako mahususi kupitia iTax (itax.kra.go.ke), kwa "
        "kuwa hali za kibinafsi zinaweza kuathiri ustahiki."
    ),'''

sw_new_entries = '''        "Thibitisha msimamo wako mahususi kupitia iTax (itax.kra.go.ke), kwa "
        "kuwa hali za kibinafsi zinaweza kuathiri ustahiki."
    ),
    "paye_bands": (
        "**Viwango vya kodi ya PAYE nchini Kenya** hupanda kwa hatua, "
        "hutumika kila mwezi (Sheria ya Fedha 2023):\\n\\n"
        "- **10%** kwa KES 24,000 za kwanza\\n"
        "- **25%** kwa KES 8,333 zinazofuata (KES 24,001-32,333)\\n"
        "- **30%** kwa KES 32,334-500,000\\n"
        "- **32.5%** kwa KES 500,001-800,000\\n"
        "- **35%** zaidi ya KES 800,000\\n\\n"
        "Kila mfanyakazi mkazi anastahili **msamaha binafsi wa KES 2,400 "
        "kwa mwezi** (KES 28,800 kwa mwaka), unaotolewa kutoka kodi "
        "iliyokokotolewa. Wasio wakazi hawastahili msamaha huu. PAYE "
        "hukokotolewa kwa mapato yanayotozwa kodi baada ya makato ya "
        "NSSF, SHIF, na Ushuru wa Nyumba za Bei Nafuu."
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
    ),'''

if sw_anchor not in content:
    print("ERROR: could not find Kiswahili anchor text. No changes made to CANNED_ANSWERS_SW.")
else:
    content = content.replace(sw_anchor, sw_new_entries, 1)
    changes_made.append("Kiswahili CANNED_ANSWERS_SW updated (paye_bands, shif_rate)")

kw_anchor = '    "turnover_tax": ["turnover tax", "tot rate", "tot threshold"],'
kw_new_entries = '''    "turnover_tax": ["turnover tax", "tot rate", "tot threshold"],
    "paye_bands": ["paye rate", "paye band", "paye tax rate", "income tax band", "income tax rate"],
    "shif_rate": ["shif rate", "shif contribution", "shif percentage", "how much shif", "shif deduction"],'''

if kw_anchor not in content:
    print("ERROR: could not find TOPIC_KEYWORDS anchor line. No changes made there.")
else:
    content = content.replace(kw_anchor, kw_new_entries, 1)
    changes_made.append("TOPIC_KEYWORDS updated (paye_bands, shif_rate)")

with open("rag_server.py", "w", encoding="utf-8") as f:
    f.write(content)

print("\n".join(changes_made) if changes_made else "No changes were made -- check errors above.")

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("\nSYNTAX CHECK: PASSED")
except SyntaxError as e:
    print(f"\nSYNTAX CHECK: FAILED -- {e}")
    print("Do NOT restart the server until this is fixed.")
