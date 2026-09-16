with open("REPORT.md", "r", encoding="utf-8") as f:
    content = f.read()

old_sha = "8ad132c6256d5d2ab47e0cb270c5637d3799e0c1"
new_sha = "8e3f0496c44e2fcfb2a7b071f36f311c5a93b5ca"

count = content.count(old_sha)
print(f"Old SHA occurrences found: {count}")
if count == 1:
    content = content.replace(old_sha, new_sha, 1)
    print(f"Updated SHA reference to {new_sha}")
    with open("REPORT.md", "w", encoding="utf-8") as f:
        f.write(content)
else:
    print(f"ERROR: old SHA found {count} times, expected 1 -- no changes made")
