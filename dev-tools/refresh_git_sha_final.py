with open("REPORT.md", "r", encoding="utf-8") as f:
    content = f.read()

old_sha = "8e3f0496c44e2fcfb2a7b071f36f311c5a93b5ca"
new_sha = "6006f1e1f313114862a84ff866dcc16138b98e71"

count = content.count(old_sha)
print(f"Old SHA occurrences found: {count}")
if count == 1:
    content = content.replace(old_sha, new_sha, 1)
    print(f"Updated SHA reference to {new_sha}")
    with open("REPORT.md", "w", encoding="utf-8") as f:
        f.write(content)
else:
    print(f"ERROR: old SHA found {count} times, expected 1 -- no changes made")
