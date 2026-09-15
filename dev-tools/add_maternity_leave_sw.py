with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

anchor = '''        "Angalia mkataba wako wa ajira kwa likizo yoyote ya ziada zaidi ya kiwango "
        "cha chini kisheria."
    ),'''

new_content = '''        "Angalia mkataba wako wa ajira kwa likizo yoyote ya ziada zaidi ya kiwango "
        "cha chini kisheria."
    ),
    "maternity_paternity_leave": (
        "**Likizo ya uzazi** (Kifungu cha 29, Sheria ya Ajira 2007): "
        "wafanyakazi wa kike wanastahili **miezi 3 (siku 90 za kalenda)** za "
        "likizo ya uzazi yenye **malipo kamili** -- inaweza kuchukuliwa kabla "
        "au baada ya kujifungua. Likizo ya kila mwaka na likizo ya ugonjwa "
        "huendelea kukusanywa kawaida wakati wa likizo ya uzazi; anastahili "
        "kurudi kwenye nafasi ile ile au sawa baada ya "
        "hapo.\\n\\n**Likizo ya baba** (Kifungu cha 29(8)): wafanyakazi wa "
        "kiume wanastahili **wiki 2 (siku 14)** za likizo ya baba, pia "
        "yenye malipo kamili, karibu na kuzaliwa kwa mtoto.\\n\\nZote mbili "
        "ni tofauti na, na hazipunguzi, haki ya kawaida ya likizo ya "
        "siku 21 za kazi kwa mwaka. Kumfukuza au kumnyima mfanyakazi haki "
        "kwa kuchukua yoyote kati ya hizi ni kinyume cha sheria chini ya "
        "Sheria ya Ajira."
    ),'''

count = content.count(anchor)
print(f"Anchor occurrences found: {count}")
if count == 1:
    content = content.replace(anchor, new_content, 1)
    print("Added Kiswahili maternity_paternity_leave")
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
