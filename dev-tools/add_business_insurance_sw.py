with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

anchor = '''        "juu zaidi hukua kwa historia thabiti ya kurejesha kwa wakati."
    ),
}'''

new_content = '''        "juu zaidi hukua kwa historia thabiti ya kurejesha kwa wakati."
    ),
    "business_insurance": (
        "Sekta ya bima nchini Kenya inasimamiwa na **Insurance Regulatory "
        "Authority (IRA)**, si KRA -- KRA ni mamlaka ya kodi na haihusiki "
        "na bima kabisa.\\n\\n**Bima ya lazima, ikiwa una wafanyakazi**: "
        "bima chini ya **Work Injury Benefits Act (WIBA)**, inayolinda "
        "wafanyakazi wanaoumia au kulemazwa kazini -- hii ni ya lazima "
        "kisheria, si hiari. Ikiwa biashara yako inatumia gari lolote, "
        "**bima ya dhima ya mtu wa tatu ya gari** pia ni ya "
        "lazima.\\n\\n**Bima za hiari zinazofaa kuzingatiwa**: bima ya "
        "dhima ya umma (inashughulikia jeraha kwa wateja/wageni katika "
        "majengo yako), bima ya mali/moto (inashughulikia bidhaa, vifaa, "
        "na majengo yako), na bima ya usumbufu wa biashara (inashughulikia "
        "mapato yaliyopotea ikiwa utalazimika kufunga kwa muda, kwa "
        "mfano baada ya moto).\\n\\nMaelezo ya bima, vizuizi, na bei "
        "hutofautiana sana kwa kampuni ya bima -- thibitisha maelezo na "
        "**kampuni ya bima au wakala aliyeidhinishwa** (angalia orodha ya "
        "IRA ya watoa huduma walioidhinishwa kwenye ira.go.ke), si KRA."
    ),
}'''

count = content.count(anchor)
print(f"Anchor occurrences found: {count}")
if count == 1:
    content = content.replace(anchor, new_content, 1)
    print("Added business_insurance (Kiswahili) canned answer")
    with open("rag_server.py", "w", encoding="utf-8") as f:
        f.write(content)
else:
    print(f"ERROR: anchor found {count} times, expected 1 -- no changes made")

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("SYNTAX CHECK: PASSED")
except SyntaxError as e:
    print(f"SYNTAX CHECK: FAILED -- {e}")
