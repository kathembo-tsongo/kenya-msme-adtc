with open("REPORT.md", "r", encoding="utf-8") as f:
    content = f.read()

if "First-token latency" in content:
    print("A 'First-token latency' section already exists -- removing it first so we don't duplicate.")
    start_marker = "**First-token latency"
    start = content.index(start_marker)
    end = content.index("**Model size:**", start)
    content = content[:start] + content[end:]

anchor = "**Model size:** 934.69 MiB (Q4_K_M quantization, 5.08 bits/weight), verified"

section = '''**First-token latency -- a real trade-off from disabling turbo boost, and why
we are not trimming the system prompt to compensate.** Disabling turbo boost
(see Thermal, above) eliminates the thermal penalty risk entirely, but is not
free: it roughly doubles first-token latency, since prompt processing is
compute-bound and directly benefits from turbo's burst clock speed. We
measured this directly and controlled for confounds: with turbo enabled,
first-token latency averaged 3.7 seconds (but carries thermal risk); with
turbo disabled, it averaged 7.5-7.8 seconds across repeated runs, including
on an otherwise idle system, ruling out background load as the cause.
Generation throughput itself is unaffected either way (16-17 tokens/sec).

Two things are worth noting about this trade-off rather than treating it as
simply solved or simply accepted. First, the ADTC profiler's own schema
distinguishes `participant_laptop` from `audit_cloud_vm` measurement
environments -- the real Gate 2 audit most likely runs on server-grade cloud
infrastructure with adequate cooling, not this specific thin-chassis
development laptop. If so, the thermal throttling that makes disabling turbo
necessary here may not occur in the actual audit environment at all, making
this entire trade-off specific to our own local testing rather than the
environment that determines scoring. We flag this as a reasonable
expectation, not a certainty, since we cannot directly verify the audit
environment's thermal behavior.

Second, we considered and rejected shortening our system prompt
(`SCOPE_INSTRUCTION`) as a way to reduce prefill length and therefore
latency independent of turbo settings. Nearly every sub-rule in that prompt
corresponds directly to a specific fabrication pattern found and fixed during
development (fabricated phone numbers, invented URLs, fabricated business-size
classifications, garbled-table numeric confusion, invented worked examples) --
it is a record of real, previously-observed failures, not verbose padding.
Cutting it to save latency risks silently reintroducing exactly the
fabrication risks this report documents fixing, and doing so under deadline
pressure without a full re-test of every previously-fixed case is a trade we
are not willing to make. We consider a guaranteed 10-point thermal penalty a
larger cost to Stotal than several seconds of added latency, and prefer
expanding verified-answer coverage (which removes queries from the slow
generative path entirely, dropping response time to near-zero) as the safer
lever for improving perceived responsiveness going forward.

'''

if anchor not in content:
    print("ERROR: could not find the Model size anchor. No changes made.")
else:
    content = content.replace(anchor, section + anchor, 1)
    with open("REPORT.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: finalized first-token latency trade-off section written.")
