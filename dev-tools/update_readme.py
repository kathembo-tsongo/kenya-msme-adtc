with open("README.md", "r", encoding="utf-8") as f:
    content = f.read()

old = "bypasses generation entirely for 17 hand-checked, high-risk topics"
new = "bypasses generation entirely for 37 hand-checked, high-risk topics"

count = content.count(old)
print(f"Anchor occurrences found: {count}")
if count == 1:
    content = content.replace(old, new, 1)
    print("Updated topic count 17 -> 37")
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)
else:
    print(f"ERROR: anchor found {count} times, expected 1 -- no changes made")
