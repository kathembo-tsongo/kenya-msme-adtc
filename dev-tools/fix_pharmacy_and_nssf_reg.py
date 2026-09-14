with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

old1 = '    "pharmacy_license": ["pharmacy license", "chemist shop license", "poisons board", "pharmacy and poisons board", "open a pharmacy", "chemist shop kenya"],\n'
new1 = '    "pharmacy_license": ["pharmacy license", "chemist shop license", "poisons board", "pharmacy and poisons board", "open a pharmacy", "chemist shop kenya", "pharmacy need to operate", "chemist shop need to operate", "licenses does a pharmacy", "licenses does a chemist"],\n'
count1 = content.count(old1)
print(f"Pharmacy anchor found: {count1}")
if count1 == 1:
    content = content.replace(old1, new1, 1)
    print("Broadened pharmacy_license keywords")

nssf_registration_line = '    "nssf_registration": ["register my business and employees", "nssf registration", "register for nssf", "register my employees for nssf"],\n'
nssf_generic_line = '    "nssf": ["nssf", "national social security fund"],\n'

count2 = content.count(nssf_registration_line)
count3 = content.count(nssf_generic_line)
print(f"nssf_registration line found: {count2}, generic nssf line found: {count3}")

if count2 == 1 and count3 == 1:
    content = content.replace(nssf_registration_line, '', 1)
    content = content.replace(nssf_generic_line, nssf_registration_line + nssf_generic_line, 1)
    print("Moved nssf_registration to appear BEFORE generic nssf (fixes shadowing)")
else:
    print("ERROR: could not cleanly locate both lines -- no reordering done")

with open("rag_server.py", "w", encoding="utf-8") as f:
    f.write(content)

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("SYNTAX CHECK: PASSED")
except SyntaxError as e:
    print(f"SYNTAX CHECK: FAILED -- {e}")
