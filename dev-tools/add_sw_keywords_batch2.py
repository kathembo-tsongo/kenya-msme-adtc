with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

changes = []

pairs = [
    ('    "nssf_penalty": ["nssf penalty", "late nssf", "nssf late payment", "penalty for late nssf", "nssf fine"],\n',
     '    "nssf_penalty": ["nssf penalty", "late nssf", "nssf late payment", "penalty for late nssf", "nssf fine", "adhabu ya nssf", "faini ya nssf kuchelewa"],\n'),

    ('    "mpesa_paybill_till": ["paybill", "till number", "buy goods till", "set up paybill", "mpesa business"],\n',
     '    "mpesa_paybill_till": ["paybill", "till number", "buy goods till", "set up paybill", "mpesa business", "namba ya paybill", "namba ya till", "kuweka paybill"],\n'),

    ('    "capital": ["minimum share capital", "share capital requirement"],\n',
     '    "capital": ["minimum share capital", "share capital requirement", "mtaji wa chini", "mtaji unaohitajika"],\n'),

    ('    "yedf": ["yedf", "youth enterprise development fund", "rausha", "inua loan", "vuka loan"],\n',
     '    "yedf": ["yedf", "youth enterprise development fund", "rausha", "inua loan", "vuka loan", "mfuko wa vijana", "mkopo wa yedf"],\n'),

    ('    "paye_bands": ["paye rate", "paye band", "paye tax rate", "income tax band", "income tax rate"],\n',
     '    "paye_bands": ["paye rate", "paye band", "paye tax rate", "income tax band", "income tax rate", "kiwango cha paye", "ushuru wa paye", "kodi ya mshahara"],\n'),

    ('    "shif_rate": ["shif rate", "shif contribution", "shif percentage", "how much shif", "shif deduction", "contribute to shif", "employer shif", "shif employer", "pay to shif", "shif pay", "obligations to shif", "shif obligations", "obligations under shif"],\n',
     '    "shif_rate": ["shif rate", "shif contribution", "shif percentage", "how much shif", "shif deduction", "contribute to shif", "employer shif", "shif employer", "pay to shif", "shif pay", "obligations to shif", "shif obligations", "obligations under shif", "kiwango cha shif", "mchango wa shif"],\n'),

    ('    "housing_levy": ["housing levy", "affordable housing levy", "ahl rate", "housing levy rate"],\n',
     '    "housing_levy": ["housing levy", "affordable housing levy", "ahl rate", "housing levy rate", "ushuru wa nyumba", "levy ya nyumba"],\n'),
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
