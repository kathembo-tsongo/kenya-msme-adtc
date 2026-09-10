with open("REPORT.md", "r", encoding="utf-8") as f:
    content = f.read()

anchor = "## What We Learned"
pointer = '''## Repository Organization

The `dev-tools/` folder contains the individual patch scripts used to
apply each fix described in this report (fabrication corrections,
the context-window fix, the language-detection bug fix, keyword
priority fixes), roughly in the order they were written. The
`benchmark-evidence/` folder contains the raw JSON output from the
official `adtc-profiler` tool for the thermal before/after comparison
and other benchmark runs referenced above. Both are kept as a direct,
inspectable record of how each reported fix was verified, rather than
summarized only in prose.

## What We Learned'''

if anchor not in content:
    print("ERROR: could not find anchor. No changes made.")
else:
    content = content.replace(anchor, pointer, 1)
    with open("REPORT.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: Repository Organization section added.")
