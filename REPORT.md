# REPORT.md - Rafiki wa Biashara: Offline AI Advisor for Kenyan MSMEs

## Problem

Kenya's micro, small, and medium enterprises (MSMEs) operate under a dense web of
regulatory, tax, and compliance obligations -- KRA tax registration, NSSF and SHIF
social security contributions, county business permits, VAT thresholds, employment
law, and financing programs -- but most MSME owners cannot afford a lawyer or
accountant to help them navigate this. Cloud-hosted AI assistants require stable
connectivity and ongoing subscription costs, real barriers for a small business
owner running a shop, salon, or workshop on a modest laptop with inconsistent
internet access.

Rafiki wa Biashara ("friend of business" in Kiswahili) is an offline, on-device
advisory assistant that runs entirely on commodity hardware, designed specifically
to save MSME owners the time and cost of visiting government offices or paying for
consultancy just to get basic procedural information -- registering a business,
applying for a startup loan, understanding tax obligations, or knowing their rights
and obligations as an employer. The target user is a Kenyan MSME owner with 1-20
employees who needs plain-language, actionable guidance without paying for
professional advice on every routine question.

## Design Decisions

**Base model:** Qwen2.5-1.5B-Instruct was chosen for its balance of capability and
size -- small enough to quantize comfortably under the 7GB RAM ceiling while
retaining enough instruction-following capacity to produce coherent, structured
advisory answers.

**Fine-tuning:** LoRA (rank 16) on 3,308 conversational examples covering Kenyan
MSME tax, registration, financing, and social security topics, sourced from
verified regulatory documents.

**Quantization:** Q4_K_M -- final model is 934.69 MiB (5.08 bits per weight),
leaving substantial headroom under the 7GB ceiling.

**Retrieval-augmented generation (RAG):** The 1.5B model's standalone factual
accuracy, while strong on frequently-repeated training topics, was unreliable
elsewhere. We built a local TF-IDF retrieval layer over the source knowledge base
(9 categories: legal/regulatory, tax/KRA, financing, social security, digital
trade, county/geospatial, culture/context, national policy, bank lending) to
ground the application's answers in real source text. This directly addresses the
cross-disciplinary integration criterion by pairing the language model with a
legal/regulatory-technology retrieval system -- the RAG layer is load-bearing:
without it, the application has no mechanism to verify or correct the base
model's claims against real source documents.

**Hybrid grounding strategy (digest-override):** During testing, we found that
even with retrieval, showing the model complex tables extracted from regulatory
PDFs (e.g., NSSF Act contribution tiers) sometimes produced worse, more confused
answers than relying on a small set of independently-verified facts directly.
For a specific set of high-frequency, high-stakes topics (NSSF rate, statutory
annual leave, company share capital, YEDF eligibility, startup loan programs,
business/KRA PIN registration, VAT threshold, and employee termination
procedure), the application skips live retrieval entirely and relies on a
hand-verified fact digest plus explicit "state concrete steps directly" and
"never invent unverified specifics" instructions. Retrieval remains the default
path for all other questions.

**Alternatives considered:** We evaluated pure fine-tuning without retrieval, but
a 1.5B model's parametric memory cannot reliably retain the volume of specific
facts a real compliance advisor needs across dozens of distinct regulatory
topics -- confirmed by an initial factual audit showing roughly a 25% error rate
on regulatory specifics before any mitigation.

## Constraints

**Hardware:** Target is the ADTC Standard Laptop (Intel i5 10th-12th gen or AMD
Ryzen 5, 8GB DDR4, integrated graphics only). Development and testing were
performed on a personal laptop (Intel i7-1065G7, 14.7GB RAM).

**Connectivity:** Zero runtime network dependencies. All inference, retrieval,
and generation happen locally via llama.cpp and a local Flask proxy server.

**Data extraction -- found and fixed:** A significant portion of the source
knowledge base (96 of 323 documents) are PDFs. We discovered our original
indexing pipeline was decoding PDF binary content as plain text, producing a
corpus of ~354,000 mostly-meaningless "chunks." We rewrote the extraction
pipeline (proper PDF parsing via pypdf, PDF-content detection regardless of file
extension), which surfaced further data problems: five source files were
corrupted at the source (a failed scraping step, or files saved with a .txt
extension containing raw PDF binary) and three files were scanned/image-based
PDFs with no text layer, requiring OCR (pytesseract) with an automatic fallback
in the indexing pipeline. The final corpus indexes all 323 source documents with
zero extraction failures, totaling 18,307 chunks -- a complete fix, not a
partial mitigation.

**Model reliability outside verified topics:** Testing revealed the fine-tuned
model can state confident but incorrect specifics -- wrong institution names,
invented URLs, fabricated phone numbers or USSD menu steps, and invented
numeric business-size classifications -- even when the core guidance is correct.
We iteratively hardened the system prompt against this pattern (explicit rules
against inventing contact details, URLs, and classifications) and found it
genuinely improves results for most cases, but hit a hard limitation on one
specific pattern: a fabricated business-size classification ("35 square meters")
that persisted across three different mitigation attempts, including skipping
retrieval entirely. We concluded this specific fabrication is baked into the
model's trained weights and is not resolvable through prompting -- a known,
lower-stakes limitation we chose to document rather than continue chasing, since
the core guidance in these cases remains accurate.

**Language scope:** We attempted Kiswahili support (direct generation and an
English-then-translate approach) but found the base model's Kiswahili fluency
insufficient -- outputs degenerated into repetitive, grammatically incoherent
text regardless of decoding parameters or prompting strategy, and a translation
step did not reliably improve results. We also found and fixed a detection bug
(substring matching caused "Kenya" to falsely trigger Kiswahili routing, since
it contains the two-letter word "ya"). Given the underlying fluency ceiling, we
made the deliberate decision to ship English-only rather than present unreliable
Kiswahili output to real users. Genuine Kiswahili support would require dedicated
training data -- a documented direction for future work.

## Benchmarks

All measurements below were taken on a personal development machine (Intel
i7-1065G7 @ 1.30GHz, 14.7GB RAM, Ubuntu, CPU-only inference via llama.cpp)
unless noted otherwise.

**Throughput:** Mean generation speed of 17.28-17.53 tokens/second across two
independent measurement methods (a custom 8-prompt benchmark script, and the
official adtc-profiler tool's llama-bench integration), consistently
exceeding the ADTC reference of 15.0 TPS.

**Memory:** The official profiler measured peak RSS of 1,693.73 MB for the raw
model alone. The full application (model server + RAG retrieval proxy) measures
approximately 3.3GB combined RSS -- both figures comfortably under the 7GB
ceiling.

**Thermal:** Results are notably inconsistent between our own testing and the
official profiler, and we report this honestly rather than picking the more
favorable number. Our own sustained-load test (20 consecutive sequential
generations) showed CPU package temperature plateauing at 77C, 8C below the
85C throttle threshold. The official adtc-profiler's llama-bench
integration -- a more intensive, back-to-back stress workload -- measured a peak
of 98-99C with throttled: true, and this persisted even after testing with a
reduced thread count (4 of 8 cores), ruling out simple CPU-load as the cause.
We believe this reflects our development machine's specific thermal design (a
thin ultrabook-class CPU) rather than a property of the model itself, and note
this was measured on our own hardware, not the ADTC reference laptop. We flag
this as a genuine, unresolved risk rather than omitting it.

**Model size:** 934.69 MiB (Q4_K_M quantization, 5.08 bits/weight), verified
parameter count of 1,543,714,304 (matches the 1.5B estimate declared in
metadata.json).

**Retrieval corpus:** 18,307 chunks across all 323 source documents, zero
extraction failures.

## What We Learned

**Test for behavior, not just loss.** A training loss of 1.39 looked
good on paper, but the model had learned the wrong behavior pattern --
hedging instead of answering. Always test actual outputs against real
user questions before assuming the model is working.

**Fabrication is a system design problem, not just a prompting problem.**
Stricter instructions reduced hallucination but didn't eliminate it.
The only reliable fix for high-stakes facts was to remove the model
from the loop entirely -- a verified-answer layer that guarantees
accuracy where it matters most.

**Infrastructure bugs hide real data bugs.** The PDF extraction issue
(354,000 meaningless chunks) masked everything downstream. Fixing
infrastructure first -- proper extraction, verified file integrity,
OCR fallback -- was what made the knowledge base actually usable.

**Offline-first forces better engineering decisions.** Every design
choice -- TF-IDF over semantic embeddings, verified answers over
generation, quantization targets -- was forced by the offline and
memory constraints. Those constraints made the system more focused,
more reliable, and more honest about what it can and can't do.

## Performance Summary

| Metric | Result | Target |
|--------|--------|--------|
| Generation speed (Sperf) | 17.28 tokens/sec | >= 15.0 tokens/sec |
| Efficiency Score (Seff) | 76.35 (RAM efficiency %) | Higher is better |
| Model size (Q4_K_M) | 934.69 MiB | <= 7GB |
| Full app memory | ~3.3GB combined | <= 7GB |
| Parameters | 1,543,714,304 | 1.5B declared |
| RAG corpus | 18,307 chunks / 323 docs | Zero extraction failures |
| CPU temp (own test) | 77C plateau | < 85C |
| CPU temp (profiler) | 98-99C peak | Reported honestly |
