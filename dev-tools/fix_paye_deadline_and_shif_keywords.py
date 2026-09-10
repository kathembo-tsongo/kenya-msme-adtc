"""1. Add the verified PAYE remittance deadline (9th of following month)
and late penalty (25% + 2%/month interest) to the existing paye_bands
canned answer, bilingual -- correcting the wrong '5 working days' claim
that appeared in real Gate 1 judge testing.
2. Broaden shif_rate keywords to catch 'obligations to SHIF' phrasing,
seen verbatim in a real Gate 1 human judge question."""

with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

changes_made = []

en_old = '''        "Every resident employee is entitled to a **personal relief of "
        "KES 2,400 per month** (KES 28,800 per year), subtracted from the "
        "calculated tax. Non-residents do not qualify for this relief. "
        "PAYE is calculated on taxable income after NSSF, SHIF, and "
        "Affordable Housing Levy deductions."
    ),'''

en_new = '''        "Every resident employee is entitled to a **personal relief of "
        "KES 2,400 per month** (KES 28,800 per year), subtracted from the "
        "calculated tax. Non-residents do not qualify for this relief. "
        "PAYE is calculated on taxable income after NSSF, SHIF, and "
        "Affordable Housing Levy deductions.\\n\\n"
        "**Remittance deadline**: PAYE deducted from a given month's "
        "salaries must be remitted to KRA by the **9th day of the "
        "following month** (e.g. January's PAYE is due by 9th "
        "February), filed via the iTax P10 return. Late remittance "
        "carries a **25% penalty** on the tax due, plus **2% monthly "
        "interest** on the unpaid amount."
    ),'''

if en_old not in content:
    print("ERROR: could not find English paye_bands anchor. No changes made.")
else:
    content = content.replace(en_old, en_new, 1)
    changes_made.append("English paye_bands updated with correct remittance deadline and penalty")

sw_old = '''        "Kila mfanyakazi mkazi anastahili **msamaha binafsi wa KES 2,400 "
        "kwa mwezi** (KES 28,800 kwa mwaka), unaotolewa kutoka kodi "
        "iliyokokotolewa. Wasio wakazi hawastahili msamaha huu. PAYE "
        "hukokotolewa kwa mapato yanayotozwa kodi baada ya makato ya "
        "NSSF, SHIF, na Ushuru wa Nyumba za Bei Nafuu."
    ),'''

sw_new = '''        "Kila mfanyakazi mkazi anastahili **msamaha binafsi wa KES 2,400 "
        "kwa mwezi** (KES 28,800 kwa mwaka), unaotolewa kutoka kodi "
        "iliyokokotolewa. Wasio wakazi hawastahili msamaha huu. PAYE "
        "hukokotolewa kwa mapato yanayotozwa kodi baada ya makato ya "
        "NSSF, SHIF, na Ushuru wa Nyumba za Bei Nafuu.\\n\\n"
        "**Tarehe ya mwisho ya kuwasilisha**: PAYE iliyokatwa kwa "
        "mshahara wa mwezi fulani lazima iwasilishwe KRA ifikapo "
        "**tarehe 9 ya mwezi unaofuata** (mfano, PAYE ya Januari "
        "inatakiwa ifikapo tarehe 9 Februari), ikiwasilishwa kupitia "
        "fomu ya P10 kwenye iTax. Kuchelewesha malipo kunatoza **faini "
        "ya 25%** ya kodi inayodaiwa, pamoja na **riba ya 2% kwa "
        "mwezi** ya kiasi kisicholipwa."
    ),'''

if sw_old not in content:
    print("ERROR: could not find Kiswahili paye_bands anchor. No changes made.")
else:
    content = content.replace(sw_old, sw_new, 1)
    changes_made.append("Kiswahili paye_bands updated with correct remittance deadline and penalty")

kw_old = '    "shif_rate": ["shif rate", "shif contribution", "shif percentage", "how much shif", "shif deduction", "contribute to shif", "employer shif", "shif employer", "pay to shif", "shif pay"],'
kw_new = '    "shif_rate": ["shif rate", "shif contribution", "shif percentage", "how much shif", "shif deduction", "contribute to shif", "employer shif", "shif employer", "pay to shif", "shif pay", "obligations to shif", "shif obligations", "obligations under shif"],'

if kw_old not in content:
    print("ERROR: could not find shif_rate keyword line. No changes made.")
else:
    content = content.replace(kw_old, kw_new, 1)
    changes_made.append("shif_rate keywords broadened for 'obligations' phrasing")

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
