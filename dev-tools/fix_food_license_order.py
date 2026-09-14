with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

license_line = '    "license": ["single business permit", "what license do i need", "what licence do i need", "trade license requirements", "leseni ya biashara", "kibali cha biashara", "ninahitaji leseni gani"],\n'
old_food_line = '    "food_business_license": ["food business need to operate", "licenses does a food business", "restaurant license kenya", "food business licenses", "licenses for a restaurant", "leseni ya mkahawa", "leseni ya biashara ya chakula"],\n'
new_food_line = '    "food_business_license": ["food business need to operate", "licenses does a food business", "restaurant license kenya", "food business licenses", "licenses for a restaurant", "leseni ya mkahawa", "leseni ya biashara ya chakula", "leseni gani kwa biashara ya chakula"],\n'

count_license = content.count(license_line)
count_food = content.count(old_food_line)
print(f"license line found: {count_license}, food_business_license line found: {count_food}")

if count_license == 1 and count_food == 1:
    content = content.replace(old_food_line, '', 1)
    content = content.replace(license_line, new_food_line + license_line, 1)
    print("Moved food_business_license BEFORE license, added missing phrase")
    with open("rag_server.py", "w", encoding="utf-8") as f:
        f.write(content)
else:
    print("ERROR: could not cleanly locate both lines -- no changes made")

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("SYNTAX CHECK: PASSED")
except SyntaxError as e:
    print(f"SYNTAX CHECK: FAILED -- {e}")
