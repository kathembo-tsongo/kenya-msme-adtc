with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

duplicate_block = '''    "probation_period": (
        "Kwa mujibu wa **Kifungu cha 42 cha Sheria ya Ajira ya 2007**, "
        "kipindi cha majaribio (probation) hakiwezi kuzidi **miezi 6** "
        "mwanzoni, lakini kinaweza kuongezwa kwa kipindi kingine cha **si "
        "zaidi ya miezi 6** kwa ridhaa ya maandishi ya mfanyakazi -- hivyo "
        "muda wa juu unaowezekana ni **miezi 12** kwa jumla, si mwaka "
        "mmoja moja kwa moja tangu mwanzo.\\n\\nWaajiri wengi hutumia "
        "kipindi kifupi zaidi (kawaida miezi 3), wakihifadhi kipindi kizima "
        "cha miezi 6 (au kilichoongezwa) kwa nafasi za juu zaidi au za "
        "kitaalamu. Wafanyakazi walio kwenye majaribio hawapo chini ya "
        "sharti la usikilizwaji wa haki la Kifungu cha 41 kabla ya "
        "kufukuzwa, lakini uamuzi wowote lazima usiwe wa ubaguzi na uwe na "
        "sababu halali."
    ),
    "class_r_permit": ('''

replacement = '''    "class_r_permit": ('''

count = content.count(duplicate_block)
print(f"Duplicate block occurrences found: {count}")
if count == 1:
    content = content.replace(duplicate_block, replacement, 1)
    print("Removed the earlier duplicate probation_period block")
    with open("rag_server.py", "w", encoding="utf-8") as f:
        f.write(content)
else:
    print(f"ERROR: found {count} times, expected 1 -- no changes made, please check manually")

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("SYNTAX CHECK: PASSED")
except SyntaxError as e:
    print(f"SYNTAX CHECK: FAILED -- {e}")

import re
with open("rag_server.py", encoding="utf-8") as f:
    c = f.read()
print(f"probation_period key count now: {len(re.findall(chr(34)+'probation_period'+chr(34)+':', c))}")
