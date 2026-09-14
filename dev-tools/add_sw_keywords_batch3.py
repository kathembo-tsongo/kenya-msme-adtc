with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

changes = []

pairs = [
    ('    "unified_business_permit": ["unified business permit", "ubp nairobi", "nairobi business permit"],\n',
     '    "unified_business_permit": ["unified business permit", "ubp nairobi", "nairobi business permit", "leseni ya nairobi", "kibali cha biashara nairobi"],\n'),

    ('    "pharmacy_license": ["pharmacy license", "chemist shop license", "poisons board", "pharmacy and poisons board", "open a pharmacy", "chemist shop kenya", "pharmacy need to operate", "chemist shop need to operate", "licenses does a pharmacy", "licenses does a chemist"],\n',
     '    "pharmacy_license": ["pharmacy license", "chemist shop license", "poisons board", "pharmacy and poisons board", "open a pharmacy", "chemist shop kenya", "pharmacy need to operate", "chemist shop need to operate", "licenses does a pharmacy", "licenses does a chemist", "leseni ya duka la dawa", "kufungua duka la dawa"],\n'),

    ('    "ca_license": ["communications authority", "ca license kenya", "telecommunications license kenya"],\n',
     '    "ca_license": ["communications authority", "ca license kenya", "telecommunications license kenya", "mamlaka ya mawasiliano", "leseni ya mawasiliano"],\n'),

    ('    "nssf_registration": ["register my business and employees", "nssf registration", "register for nssf", "register my employees for nssf"],\n',
     '    "nssf_registration": ["register my business and employees", "nssf registration", "register for nssf", "register my employees for nssf", "kusajili wafanyakazi nssf", "kujisajili nssf"],\n'),

    ('    "keproba": ["keproba", "kenya export promotion", "export promotion and branding agency", "brand kenya agency"],\n',
     '    "keproba": ["keproba", "kenya export promotion", "export promotion and branding agency", "brand kenya agency", "usafirishaji nje ya nchi", "kuuza bidhaa nje"],\n'),

    ('    "no_permit_penalty": ["without a county permit", "operate a business without", "without a permit", "penalty for operating without", "no business permit"],\n',
     '    "no_permit_penalty": ["without a county permit", "operate a business without", "without a permit", "penalty for operating without", "no business permit", "bila kibali cha kaunti", "adhabu ya kutokuwa na kibali"],\n'),

    ('    "sole_prop_vs_limited": ["difference between a sole proprietorship", "sole proprietorship and a limited company", "sole proprietorship vs limited company", "sole proprietorship or a limited company"],\n',
     '    "sole_prop_vs_limited": ["difference between a sole proprietorship", "sole proprietorship and a limited company", "sole proprietorship vs limited company", "sole proprietorship or a limited company", "tofauti kati ya umiliki binafsi na kampuni"],\n'),

    ('    "late_filing_penalty": ["penalties for late filing", "late filing of tax returns", "penalty for late filing", "what happens if i file late", "late tax return penalty"],\n',
     '    "late_filing_penalty": ["penalties for late filing", "late filing of tax returns", "penalty for late filing", "what happens if i file late", "late tax return penalty", "adhabu ya kuchelewa kuwasilisha", "kuchelewa kuwasilisha marejesho"],\n'),

    ('    "etims_general": ["what is etims", "why does my business need etims", "why do i need etims"],\n',
     '    "etims_general": ["what is etims", "why does my business need etims", "why do i need etims", "etims ni nini", "kwa nini nahitaji etims"],\n'),

    ('    "sacco_vs_bank": ["saccos offer loans differently", "sacco vs bank", "sacco or bank loan", "difference between sacco and bank", "saccos differently from commercial banks"],\n',
     '    "sacco_vs_bank": ["saccos offer loans differently", "sacco vs bank", "sacco or bank loan", "difference between sacco and bank", "saccos differently from commercial banks", "tofauti kati ya sacco na benki"],\n'),

    ('    "food_business_license": ["food business need to operate", "licenses does a food business", "restaurant license kenya", "food business licenses", "licenses for a restaurant"],\n',
     '    "food_business_license": ["food business need to operate", "licenses does a food business", "restaurant license kenya", "food business licenses", "licenses for a restaurant", "leseni ya mkahawa", "leseni ya biashara ya chakula"],\n'),
]

for old, new in pairs:
    count = content.count(old)
    topic_name = old.split('"')[1]
    if count == 1:
        content = content.replace(old, new, 1)
        changes.append(f"OK: {topic_name}")
    else:
        changes.append(f"ERROR ({count} occurrences): {topic_name}")

with open("rag_server.py", "w", encoding="utf-8") as f:
    f.write(content)

for c in changes:
    print(c)

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("SYNTAX CHECK: PASSED")
except SyntaxError as e:
    print(f"SYNTAX CHECK: FAILED -- {e}")
