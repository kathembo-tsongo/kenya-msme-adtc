import json

with open("metadata.json", "r", encoding="utf-8") as f:
    data = json.load(f)

if "git_commit_sha" in data:
    del data["git_commit_sha"]
    print("Removed git_commit_sha from metadata.json root (schema conflict).")
else:
    print("git_commit_sha was not present -- nothing to remove.")

with open("metadata.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
    f.write("\n")

print(json.dumps(data, indent=2))
