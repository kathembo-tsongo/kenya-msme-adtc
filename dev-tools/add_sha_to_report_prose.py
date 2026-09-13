with open("REPORT.md", "r", encoding="utf-8") as f:
    content = f.read()

old = "**Base model.** [Qwen/Qwen2.5-1.5B-Instruct]"
new = (
    "**Repository state.** This report and the accompanying submission "
    "reflect git commit `8ad132c6256d5d2ab47e0cb270c5637d3799e0c1` on the "
    "`main` branch. (Note: the ADTC reference profiler's schema places "
    "reproducibility metadata such as commit SHAs in a separate "
    "`reproducibility` object outside `metadata.json`'s `submission` "
    "schema, which has `additionalProperties: false` and no slot for it "
    "-- we state it here in prose instead, and have raised this apparent "
    "discrepancy between the written Gate 2 guidelines and the published "
    "schema with the organizing team.)\n\n"
    "**Base model.** [Qwen/Qwen2.5-1.5B-Instruct]"
)

if old not in content:
    print("ERROR: could not find anchor. No changes made.")
else:
    content = content.replace(old, new, 1)
    with open("REPORT.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: commit SHA and schema-discrepancy note added to REPORT.md prose.")
