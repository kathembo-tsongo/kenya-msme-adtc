with open("start.sh", "r", encoding="utf-8") as f:
    content = f.read()

old = "  -c 4096 \\"
new = "  -c 8192 \\"

count = content.count(old)
print(f"Anchor occurrences found: {count}")
if count == 1:
    content = content.replace(old, new, 1)
    print("Increased context size 4096 -> 8192")
    with open("start.sh", "w", encoding="utf-8") as f:
        f.write(content)
else:
    print(f"ERROR: anchor found {count} times, expected 1 -- no changes made")
