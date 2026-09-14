with open("REPORT.md", "r", encoding="utf-8") as f:
    content = f.read()

changes = []

old_table_rows = """| Generation speed (Sperf) | 16.0-17.7 tokens/sec | >= 15.0 tokens/sec |
| Efficiency Score (Seff), raw model | ~76% (RAM efficiency, official profiler) | Higher is better |
| Full application memory (model + RAG server) | ~3.3GB combined* | <= 7GB |
| Model size (Q4_K_M) | 934.69 MiB | <= 7GB |
| Parameters | 1,543,714,304 | 1.5B declared |
| RAG corpus | 18,307 chunks / 323 docs | Zero extraction failures |
| CPU temperature (official profiler, current) | 59C, throttled: false | < 85C |
| Official Gate 1 Accuracy Score | 61.27 | -- |
| Self-measured accuracy, chat path only (30-question set)** | 88.7-90.0% (3 runs) | -- |
| Digest-override topics | 17 (EN + Kiswahili) | -- |"""

new_table_rows = """| Generation speed (Sperf) | 15.3-17.7 tokens/sec | >= 15.0 tokens/sec |
| Efficiency Score (Seff), raw model | ~76% (RAM efficiency, official profiler) | Higher is better |
| Full application memory (model + RAG server) | ~3.3GB combined* | <= 7GB |
| Model size (Q4_K_M) | 934.69 MiB | <= 7GB |
| Parameters | 1,543,714,304 | 1.5B declared |
| RAG corpus | 18,307 chunks / 323 docs | Zero extraction failures |
| CPU temperature (official profiler, current) | 61C, throttled: false | < 85C |
| Official Gate 1 Accuracy Score | 61.27 | -- |
| Official Gate 1 Performance Score | 26.13 (above semifinalist median 24.50) | -- |
| Official Gate 1 Efficiency Score | 84.69 (at semifinalist median 84.65) | -- |
| Self-measured accuracy, chat path only (30-question set)** | 92-97.3% across repeated runs post-Gate-1 fixes (was 88.7-90.0% at Gate 1) | -- |
| Digest-override topics | 37 (EN + Kiswahili) -- up from 17 at Gate 1 | -- |"""

count1 = content.count(old_table_rows)
print(f"Table anchor occurrences found: {count1}")
if count1 == 1:
    content = content.replace(old_table_rows, new_table_rows, 1)
    changes.append("Updated Performance Summary table")
else:
    changes.append(f"ERROR: table anchor found {count1} times, expected 1")

with open("REPORT.md", "w", encoding="utf-8") as f:
    f.write(content)

for c in changes:
    print(c)
