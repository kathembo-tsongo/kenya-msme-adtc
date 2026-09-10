"""Apply two consistency fixes to REPORT.md:
1. Replace the Performance Summary table with the corrected version.
2. Add the explicit 61.27 official Gate 1 score into the Accuracy prose
   paragraph in Benchmarks, so it's not first seen in the table."""

with open("REPORT.md", "r", encoding="utf-8") as f:
    content = f.read()

changes = []

old_table = '''| Metric | Result | Target |
|--------|--------|--------|
| Generation speed (Sperf) | 16.0-17.7 tokens/sec | >= 15.0 tokens/sec |
| Efficiency Score (Seff) | ~76% (RAM efficiency, official profiler) | Higher is better |
| Model size (Q4_K_M) | 934.69 MiB | <= 7GB |
| Full app memory | ~3.3GB combined | <= 7GB |
| Parameters | 1,543,714,304 | 1.5B declared |
| RAG corpus | 18,307 chunks / 323 docs | Zero extraction failures |
| Self-measured accuracy (30-question set) | 88.7-90.0% (3 runs) | -- |
| CPU temp, turbo disabled (official profiler) | 59C, throttled: false | < 85C |
| CPU temp, turbo enabled (official profiler, pre-fix) | 96-100C, throttled: true | Root cause found and fixed |
| Digest-override topics | 17 (EN + Kiswahili) | -- |'''

new_table = '''| Metric | Result | Target |
|--------|--------|--------|
| Generation speed (Sperf) | 16.0-17.7 tokens/sec | >= 15.0 tokens/sec |
| Efficiency Score (Seff), raw model | ~76% (RAM efficiency, official profiler) | Higher is better |
| Full application memory (model + RAG server) | ~3.3GB combined* | <= 7GB |
| Model size (Q4_K_M) | 934.69 MiB | <= 7GB |
| Parameters | 1,543,714,304 | 1.5B declared |
| RAG corpus | 18,307 chunks / 323 docs | Zero extraction failures |
| CPU temperature (official profiler, current) | 59C, throttled: false | < 85C |
| Official Gate 1 Accuracy Score | 61.27 | -- |
| Self-measured accuracy, chat path only (30-question set)** | 88.7-90.0% (3 runs) | -- |
| Digest-override topics | 17 (EN + Kiswahili) | -- |

*The official Efficiency Score (Seff) is calculated from the raw model's
memory footprint alone (~1.7GB), matching how the reference profiler
measures it via `llama-bench` with no server wrapper. ~3.3GB is the actual
combined footprint of the deployed application (model server + Flask RAG
proxy) that a real user would run -- still comfortably under the 7GB
ceiling, but reported separately since the two numbers measure different
things and are not interchangeable.

**Not directly comparable to the official score above -- see "Two
distinct accuracy-evaluation paths" for why. This reflects only the
qualitative/chat component we can influence via the digest-override
layer; the official score's multiple-choice component tests raw model
log-likelihood, which this measurement does not touch and which our
mitigations cannot reach.'''

if old_table not in content:
    print("ERROR: could not find the old Performance Summary table. No table changes made.")
else:
    content = content.replace(old_table, new_table, 1)
    changes.append("Performance Summary table replaced with corrected version")

old_para_tail = '''After fixing both and applying the digest-override expansion described
above, three independent full runs scored 88.7%, 90.0%, and 89.3% --
a stable result, not a single favorable sample. We report the flawed first
measurement alongside the corrected ones because it is a real part of how
this number was produced, not because it reflects the submitted system's
actual accuracy.'''

new_para_tail = '''After fixing both and applying the digest-override expansion described
above, three independent full runs scored 88.7%, 90.0%, and 89.3% --
a stable result, not a single favorable sample. This is not directly
comparable to our official Gate 1 Accuracy Score of **61.27**: as
explained above, that score's multiple-choice component evaluates the
raw model's own weights via log-likelihood scoring, which our
digest-override and RAG mitigations cannot reach, while this
self-measured figure reflects only the qualitative chat path those
mitigations do protect. We report the flawed first measurement
alongside the corrected ones because it is a real part of how this
number was produced, not because it reflects the submitted system's
actual accuracy.'''

if old_para_tail not in content:
    print("ERROR: could not find the Accuracy paragraph tail. No prose changes made.")
else:
    content = content.replace(old_para_tail, new_para_tail, 1)
    changes.append("Accuracy prose paragraph updated with explicit 61.27 reference")

with open("REPORT.md", "w", encoding="utf-8") as f:
    f.write(content)

print("\n".join(changes) if changes else "No changes were made -- check errors above.")
print(f"\nNew file length: {len(content.splitlines())} lines")
