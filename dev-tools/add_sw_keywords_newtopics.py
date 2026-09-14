with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

changes = []

pairs = [
    ('    "sole_prop_to_llc": ["transition into a limited", "convert my sole proprietorship", '
     '"converting sole proprietorship", "convert a sole proprietorship", '
     '"sole proprietorship into a limited", "sole proprietorship to a limited", '
     '"convert business name to company", "business name to limited company", '
     '"sole prop to llc", "sole proprietorship to llc"],\n',
     '    "sole_prop_to_llc": ["transition into a limited", "convert my sole proprietorship", '
     '"converting sole proprietorship", "convert a sole proprietorship", '
     '"sole proprietorship into a limited", "sole proprietorship to a limited", '
     '"convert business name to company", "business name to limited company", '
     '"sole prop to llc", "sole proprietorship to llc", "kubadilisha biashara kuwa kampuni", '
     '"kutoka umiliki binafsi kwenda kampuni"],\n'),

    ('    "wef": ["women enterprise fund", "wef loan", "tuinuke chama loan", '
     '"woman-owned business access", "woman-owned business fund", '
     '"women group loan kenya", "constituency women enterprise scheme"],\n',
     '    "wef": ["women enterprise fund", "wef loan", "tuinuke chama loan", '
     '"woman-owned business access", "woman-owned business fund", '
     '"women group loan kenya", "constituency women enterprise scheme", '
     '"mfuko wa wanawake", "mkopo wa wanawake"],\n'),

    ('    "agpo": ["agpo", "government procurement opportunities", "government tenders for youth", '
     '"30% government procurement", "access to government procurement"],\n',
     '    "agpo": ["agpo", "government procurement opportunities", "government tenders for youth", '
     '"30% government procurement", "access to government procurement", '
     '"zabuni za serikali", "manunuzi ya serikali"],\n'),

    ('    "tcc_application": ["tax compliance certificate", "apply for tcc", "tcc application", '
     '"how to get tcc", "tax compliance certificate application"],\n',
     '    "tcc_application": ["tax compliance certificate", "apply for tcc", "tcc application", '
     '"how to get tcc", "tax compliance certificate application", '
     '"cheti cha ulipaji kodi", "kupata tcc"],\n'),

    ('    "probation_period": ["probation period", "probation length", "how long can probation", '
     '"maximum probation", "probation extension"],\n',
     '    "probation_period": ["probation period", "probation length", "how long can probation", '
     '"maximum probation", "probation extension", "kipindi cha majaribio", '
     '"muda wa majaribio kazini"],\n'),
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
