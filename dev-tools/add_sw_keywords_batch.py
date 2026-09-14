with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

changes = []

pairs = [
    ('    "leave": ["annual leave", "leave entitlement", "leave days"],\n',
     '    "leave": ["annual leave", "leave entitlement", "leave days", "likizo ya mwaka", "siku za likizo", "haki ya likizo"],\n'),

    ('    "loan": ["apply for a loan", "apply for financing", "get a loan", "startup loan", "hustler fund", "loan to start"],\n',
     '    "loan": ["apply for a loan", "apply for financing", "get a loan", "startup loan", "hustler fund", "loan to start", "mkopo wa biashara", "jinsi ya kupata mkopo", "kupata mkopo wa kuanzisha"],\n'),

    ('    "kra_pin": ["how do i get a kra pin", "kra pin registration", "apply for kra pin", "get a kra pin", "kra pin for my business"],\n',
     '    "kra_pin": ["how do i get a kra pin", "kra pin registration", "apply for kra pin", "get a kra pin", "kra pin for my business", "namba ya pin ya kra", "kupata pin ya kra", "jinsi ya kupata pin"],\n'),

    ('    "vat": ["vat registration", "vat threshold", "register for vat", "required to register for vat", "do i need to register for vat", "vat registration threshold"],\n',
     '    "vat": ["vat registration", "vat threshold", "register for vat", "required to register for vat", "do i need to register for vat", "vat registration threshold", "kusajili vat", "ni lini nasajili vat", "kikomo cha vat"],\n'),

    ('    "termination": ["terminate an employee", "termination", "dismissal", "dismiss an employee", "redundancy", "fire an employee", "firing an employee"],\n',
     '    "termination": ["terminate an employee", "termination", "dismissal", "dismiss an employee", "redundancy", "fire an employee", "firing an employee", "kumfukuza mfanyakazi", "kuachisha kazi", "kufukuza mfanyakazi"],\n'),

    ('    "license": ["single business permit", "what license do i need", "what licence do i need", "trade license requirements"],\n',
     '    "license": ["single business permit", "what license do i need", "what licence do i need", "trade license requirements", "leseni ya biashara", "kibali cha biashara", "ninahitaji leseni gani"],\n'),

    ('    "turnover_tax": ["turnover tax", "tot rate", "tot threshold"],\n',
     '    "turnover_tax": ["turnover tax", "tot rate", "tot threshold", "kodi ya mauzo", "kodi ya turnover"],\n'),

    ('    "minimum_wage": ["minimum wage", "minimum salary", "lowest wage", "minimum pay"],\n',
     '    "minimum_wage": ["minimum wage", "minimum salary", "lowest wage", "minimum pay", "mshahara wa chini kabisa", "kima cha chini cha mshahara"],\n'),
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
