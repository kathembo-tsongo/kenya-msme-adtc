"""Add Housing Levy (verified 1.5%+1.5% facts) and Minimum Wage (correctly
communicating its genuinely tiered, non-single-figure nature) as canned
answers, bilingual. Anchors on the exact unique closing text of the
shif_rate entries just added, inserting new content immediately after --
still inside each dict, before its closing brace."""

with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

changes_made = []

en_anchor = '''        "directly via the SHA (Social Health Authority) or your payroll "
        "provider, since specifics can be updated."
    ),'''

en_new = '''        "directly via the SHA (Social Health Authority) or your payroll "
        "provider, since specifics can be updated."
    ),
    "housing_levy": (
        "**Affordable Housing Levy (AHL)** in Kenya:\\n\\n"
        "- **1.5%** of gross salary from the employee\\n"
        "- **1.5%** of gross salary matched by the employer\\n"
        "- **Total: 3%** of gross salary per employee, per month\\n\\n"
        "There is **no minimum income threshold** -- it applies to all "
        "gross salaried employees. Informal-sector and self-employed "
        "contributors pay 1.5% of declared income with no employer match, "
        "registering via the AHL/Boma Yangu portal. Remittance is due by "
        "the 9th working day after month-end via KRA iTax. Resident "
        "individuals who pay AHL are entitled to affordable housing "
        "relief. Late remittance carries a 3% per month penalty on the "
        "unpaid amount."
    ),
    "minimum_wage": (
        "**Kenya does not have a single national minimum wage.** Rates "
        "are set by occupation, sector, and geographic zone under "
        "periodic Regulation of Wages Orders (Labour Institutions Act), "
        "typically revised around Labour Day (1st May).\\n\\n"
        "As a reference point: the general (unskilled) labourer minimum "
        "in Nairobi, Mombasa, Kisumu, Nakuru, and Eldoret was set at "
        "**KES 18,047.40 per month** under the May 2026 Wage Order "
        "(Legal Notices No. 95 and 96), with lower rates in other zones. "
        "Skilled occupations (e.g. drivers, artisans, cashiers) and "
        "sector-specific roles (agricultural, security, domestic work) "
        "have their own, generally higher, statutory minimums.\\n\\n"
        "Because rates vary by role and location and are revised "
        "periodically, confirm the exact current figure for your "
        "specific occupation and zone via the Ministry of Labour and "
        "Social Protection or the current Kenya Gazette Wage Order, "
        "rather than relying on a single number."
    ),'''

if en_anchor not in content:
    print("ERROR: could not find English anchor. No changes made to CANNED_ANSWERS.")
else:
    content = content.replace(en_anchor, en_new, 1)
    changes_made.append("English CANNED_ANSWERS updated (housing_levy, minimum_wage)")

sw_anchor = '''        "kwa moja kupitia SHA (Social Health Authority) au mtoa huduma "
        "wako wa malipo, kwa kuwa maelezo yanaweza kubadilishwa."
    ),'''

sw_new = '''        "kwa moja kupitia SHA (Social Health Authority) au mtoa huduma "
        "wako wa malipo, kwa kuwa maelezo yanaweza kubadilishwa."
    ),
    "housing_levy": (
        "**Ushuru wa Nyumba za Bei Nafuu (AHL)** nchini Kenya:\\n\\n"
        "- **1.5%** ya mshahara wa jumla kutoka kwa mfanyakazi\\n"
        "- **1.5%** ya mshahara wa jumla inayolingana kutoka kwa mwajiri\\n"
        "- **Jumla: 3%** ya mshahara wa jumla kwa kila mfanyakazi, kila "
        "mwezi\\n\\n"
        "**Hakuna kiwango cha chini cha mapato** kinachotakiwa -- "
        "hutumika kwa wafanyakazi wote wenye mshahara wa jumla. "
        "Wachangiaji wa sekta isiyo rasmi na wanaojiajiri hulipa 1.5% ya "
        "mapato yaliyotangazwa bila mchango wa mwajiri, wakijisajili "
        "kupitia tovuti ya AHL/Boma Yangu. Malipo yanatakiwa kufikishwa "
        "ndani ya siku 9 za kazi baada ya mwisho wa mwezi kupitia iTax "
        "ya KRA. Watu wakazi wanaolipa AHL wanastahili msamaha wa nyumba "
        "za bei nafuu. Kuchelewesha malipo kunatoza faini ya 3% kwa "
        "mwezi ya kiasi kisicholipwa."
    ),
    "minimum_wage": (
        "**Kenya haina mshahara mmoja wa chini wa kitaifa.** Viwango "
        "huwekwa kulingana na kazi, sekta, na eneo la kijiografia chini "
        "ya Amri za Kanuni za Mishahara zinazotolewa mara kwa mara "
        "(Sheria ya Taasisi za Kazi), kwa kawaida hurekebishwa karibu na "
        "Siku ya Wafanyakazi (Mei 1).\\n\\n"
        "Kama kumbukumbu: mshahara wa chini wa kibarua wa kawaida "
        "(asiye na ujuzi maalum) Nairobi, Mombasa, Kisumu, Nakuru, na "
        "Eldoret uliwekwa kuwa **KES 18,047.40 kwa mwezi** chini ya Amri "
        "ya Mishahara ya Mei 2026, ukiwa na viwango vya chini zaidi "
        "katika maeneo mengine. Kazi zenye ujuzi (mfano, madereva, "
        "mafundi, wafanyakazi wa fedha) na kazi za sekta mahususi "
        "(kilimo, ulinzi, kazi za nyumbani) zina viwango vyao vya "
        "kisheria, kwa kawaida vya juu zaidi.\\n\\n"
        "Kwa kuwa viwango hutofautiana kulingana na kazi na eneo na "
        "hurekebishwa mara kwa mara, thibitisha kiwango halisi cha sasa "
        "kwa kazi yako mahususi na eneo lako kupitia Wizara ya Kazi na "
        "Ulinzi wa Jamii au Amri ya Mishahara ya sasa ya Kenya Gazette, "
        "badala ya kutegemea nambari moja."
    ),'''

if sw_anchor not in content:
    print("ERROR: could not find Kiswahili anchor. No changes made to CANNED_ANSWERS_SW.")
else:
    content = content.replace(sw_anchor, sw_new, 1)
    changes_made.append("Kiswahili CANNED_ANSWERS_SW updated (housing_levy, minimum_wage)")

kw_anchor = '    "shif_rate": ["shif rate", "shif contribution", "shif percentage", "how much shif", "shif deduction", "contribute to shif", "employer shif", "shif employer", "pay to shif", "shif pay"],'
kw_new = '''    "shif_rate": ["shif rate", "shif contribution", "shif percentage", "how much shif", "shif deduction", "contribute to shif", "employer shif", "shif employer", "pay to shif", "shif pay"],
    "housing_levy": ["housing levy", "affordable housing levy", "ahl rate", "housing levy rate"],
    "minimum_wage": ["minimum wage", "minimum salary", "lowest wage", "minimum pay"],'''

if kw_anchor not in content:
    print("ERROR: could not find TOPIC_KEYWORDS anchor. No changes made there.")
else:
    content = content.replace(kw_anchor, kw_new, 1)
    changes_made.append("TOPIC_KEYWORDS updated (housing_levy, minimum_wage)")

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
