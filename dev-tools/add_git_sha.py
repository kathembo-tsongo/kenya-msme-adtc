import json

with open("metadata.json", "r", encoding="utf-8") as f:
    data = json.load(f)

data["git_commit_sha"] = "8ad132c6256d5d2ab47e0cb270c5637d3799e0c1"

with open("metadata.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
    f.write("\n")

print("Added git_commit_sha to metadata.json")
print(json.dumps(data, indent=2))
