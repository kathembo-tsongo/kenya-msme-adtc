with open("REPORT.md", "r", encoding="utf-8") as f:
    content = f.read()

old = "- Colab execution link: [PLACEHOLDER -- pending]"
new = "- Colab execution link: https://colab.research.google.com/drive/1jpcZW0uXTLsfxPQCT2AYnKfoLRiyrdIV?usp=sharing"

if old not in content:
    print("ERROR: could not find the placeholder. No changes made.")
else:
    content = content.replace(old, new, 1)
    with open("REPORT.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: Colab link added.")
