import json

with open("metadata.json", "r", encoding="utf-8") as f:
    data = json.load(f)

data["language_scope"] = ["en", "sw"]
data["african_alpha_claim"] = True

with open("metadata.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
    f.write("\n")

print("Updated metadata.json:")
print(json.dumps({
    "language_scope": data["language_scope"],
    "african_alpha_claim": data["african_alpha_claim"],
}, indent=2))
