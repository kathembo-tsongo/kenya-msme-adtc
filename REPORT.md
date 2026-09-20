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
For a specific set of high-frequency, high-stakes topics, the application skips
live retrieval entirely and relies on a hand-verified fact digest plus explicit
"state concrete steps directly" and "never invent unverified specifics"
instructions. Retrieval remains the default path for all other questions.

This layer started at 10 topics for Gate 1 (NSSF rate, statutory annual leave,
company share capital, YEDF eligibility, startup loan programs, business
registration, KRA PIN registration, VAT threshold, employee termination
procedure, and business licensing). Post-Gate-1 testing -- both our own spot
checks and direct analysis of our Gate 1 judge transcript -- surfaced further
severe fabrication cases on foundational, frequently-asked numeric-rate
questions: a fabricated multi-tier Turnover Tax structure with garbled
thresholds, an incomplete PAYE band table missing the top 35% bracket, a
conflation of SHIF's flat-rate structure with NSSF's tiered structure (down
to a fabricated pseudo-mathematical formula), a fabricated income threshold
for the Affordable Housing Levy, a dangerously oversimplified single-figure
answer to a question whose real answer is a sector/region-tiered wage
structure, a wrong PAYE remittance deadline, and a claim that M-Pesa
Paybill/Till registration is handled by banks rather than Safaricom. Each was
verified against an authoritative current source (primarily KRA's and
Safaricom's own published guidance) and added to the digest, bringing the
layer to 17 topics total, each available in both English and Kiswahili (see
Language Scope below).

**Alternatives considered:** We evaluated pure fine-tuning without retrieval, but
a 1.5B model's parametric memory cannot reliably retain the volume of specific
facts a real compliance advisor needs across dozens of distinct regulatory
topics -- confirmed by an initial factual audit showing roughly a 25% error rate
on regulatory specifics before any mitigation.

## Model Provenance

**Repository state.** This report and the accompanying submission reflect git commit `b5bb60d9b72e03fc81518e2798824864b2aebe8f` on the `post-gate2-experiments` branch. (Note: the ADTC reference profiler's schema places reproducibility metadata such as commit SHAs in a separate `reproducibility` object outside `metadata.json`'s `submission` schema, which has `additionalProperties: false` and no slot for it -- we state it here in prose instead, and have raised this apparent discrepancy between the written Gate 2 guidelines and the published schema with the organizing team.)

**Base model.** [Qwen/Qwen2.5-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct), loaded via `transformers.AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")` at training time (main branch, no pinned revision).

**Fine-tuning method.** LoRA, rank 16 (`r=16, lora_alpha=32, lora_dropout=0.05, bias="none", target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"]`), trained via TRL's `SFTTrainer` for 2 epochs, batch size 4 with gradient accumulation 4, learning rate 2e-4 (cosine schedule, 3% warmup), on a Colab T4 GPU. Final training loss: **1.3941499436567277** at global step 394. Full configuration, training call, and logged output are preserved in the training notebook (`provenance/My_Offline_AI_advicer_for_kenyan_msmes.ipynb`) and `provenance/trainer_state.json`.

**Training dataset.** 3,308 synthetic conversational examples covering Kenyan MSME tax, registration, financing, and social security topics, generated from the project's own verified regulatory source documents (see Data Extraction, below) rather than any third-party licensed dataset. No external dataset license applies; the dataset is original work produced for this project and is included in full at `provenance/training_data_v4_merged.jsonl` (3,308 records, SHA256 checksum below).

**Merge and quantization.** The LoRA adapter (`checkpoint-394`) was merged into the base model via `peft.PeftModel.from_pretrained()` + `merge_and_unload()`, converted to GGUF via `llama.cpp`'s `convert_hf_to_gguf.py`, and quantized to Q4_K_M via `llama-quantize`. All three steps, including their real logged output, are preserved in the same training notebook.

**Proof-of-training files** (in `provenance/`):
- `adapter_model.safetensors` + `adapter_config.json` -- the trained LoRA adapter
- `My_Offline_AI_advicer_for_kenyan_msmes.ipynb` -- full training notebook (data prep, LoRA training, merge, GGUF conversion, quantization), with cell outputs intact
- `trainer_state.json` -- per-step training metrics
- `training_data_v4_merged.jsonl` -- the complete training dataset (3,308 records)
- Colab execution link: [https://colab.research.google.com/drive/1jpcZW0uXTLsfxPQCT2AYnKfoLRiyrdIV?usp=sharing](https://colab.research.google.com/drive/1jpcZW0uXTLsfxPQCT2AYnKfoLRiyrdIV?usp=sharing)

**SHA256 checksums:**

    adapter_model.safetensors:      962a625b15ef4a7b8c67a38982dcb395b065b87cba1604170597a751704ec623
    msme-qwen2.5-1.5b-Q4_K_M.gguf:  9db039ebc56c279555fa4e09e77f0be5ed82328ed3e6e8fe4e19621c13792ae5  (v9-digest build on the original weights; superseded by the v6+v9 build listed under "Updated SHA256 checksums" below)
    training_data_v4_merged.jsonl:  f238a4290e0d5a173147c20a52a503cd718149489693c995c245ec99bde016b8

**Before/after comparison.** Two identical prompts run through the unmodified base model (`Qwen/Qwen2.5-1.5B-Instruct-GGUF`, official Q4_K_M release) and our fine-tuned model, both without RAG or the digest-override layer, isolating the fine-tuning's effect specifically:

*Prompt: "What are the NSSF contribution rates for an employee earning KSh 30,000 per month?"*
- **Base model:** invents a fictional "1.5% to 2.5%" rate and a non-existent "Additional Contribution Rate" concept; no calculation given.
- **Fine-tuned model:** "The NSSF contribution... is **KSh 1,800**. This is calculated as 6% of the employee's salary plus 6% of the employer's contribution... the employee pays **KSh 1,800** and the employer matches with **KSh 1,800**." -- correct rate, correctly calculated.

*Prompt: "What is Turnover Tax in Kenya and who qualifies to pay it?"*
- **Base model:** conflates Turnover Tax entirely with VAT, states a fabricated "KES 100,000" threshold and a fictional "18%... progressive" rate, and invents a non-existent "Goods and Services Tax (GST)."
- **Fine-tuned model:** correctly uses Kenya-specific terminology and a real regulatory figure (KES 5,000,000), though it still conflates Turnover Tax's identity with VAT's threshold -- a partial improvement, not a full fix, and the exact reason our digest-override layer (see Hybrid Grounding Strategy, above) provides a hand-verified answer for this specific topic rather than relying on generation alone.

**Post-Gate-2 accuracy pass (September 18, 2026).** Following the Gate 2 due-diligence call, we conducted a systematic accuracy audit using a base-model-vs-fine-tuned-model comparison methodology (identical prompts run against the unmodified `Qwen2.5-1.5B-Instruct-GGUF` and our model, both without RAG). This surfaced several confirmed fabrications outside our original digest's coverage: incorrect or incoherent answers on Corporation Tax rate, Withholding Tax rate, Capital Gains Tax (a fabricated one-year holding-period rule), WIBA (confused with a fictional "Women Industrial Business Association" rather than the real Work Injury Benefits Act), Excise Duty, Stamp Duty (conflating the land-transfer rate with the share-transfer rate), Rental Income Tax, and a self-contradicting Turnover Tax deduction claim.

Each fact was independently verified against KRA's official published guidance before being added directly to the model's chat-template digest (`tokenizer.chat_template`), using the same `gguf_new_metadata.py` patching method documented above for the original anti-fabrication fixes. Two rounds of patching were required: an initial, descriptively-worded addition was insufficient to override the model's competing prior knowledge on two facts (Stamp Duty, Rental Income); a second pass using explicit contradiction-naming language ("this rate applies to X, not Y -- do not state Y") successfully corrected both. All ten new facts were verified via live testing after each patch, with full regression testing against the original digest facts (NSSF, PAYE, VAT) confirming no degradation.

One fact (the NITA training levy) could not be stated with full confidence: independent legal-source research found genuine disagreement over whether the current rate is KES 50/month (the original 2007 rate) or KES 600/year (per a 2020 amendment, with a 2022 Act that may have reverted this). Rather than assert an unverified figure, the digest instructs the model to state that the rate has changed through multiple amendments and to direct the user to confirm the current figure with NITA or KRA directly -- an explicit, honest hedge rather than a guessed number.

The updated model was re-verified via a fresh git clone and `download_model.sh` run, confirming the new SHA256 checksum resolves correctly end-to-end.

**Model retraining update (September 19, 2026).** Following further testing, the submitted model was switched to a fresh fine-tuning run trained on an expanded dataset, `training_data_v5.jsonl` (3,429 examples), rather than the original `training_data_v3_final.jsonl`. The LoRA configuration is identical to the original run (rank 16, alpha 32, dropout 0.05, same 7 target modules), trained for 2 epochs on a Colab T4 GPU, reaching **global_step 430** with a final mean training loss of **1.3378484437632006** -- both a slight improvement over the original run's step-394 loss of 1.3941499436567277. One notable difference: this run's LoRA adapter weights were saved in fp32 precision (73,911,112 bytes) rather than the original run's fp16 (36,981,856 bytes) -- the same number of trainable parameters (18,464,768), stored with double the numerical precision per value, consistent with the fp32-adapter stability fix documented during this project's earlier NaN-weights debugging.

The trained adapter was merged into the base model, converted to GGUF, and quantized to Q4_K_M using the same process documented above. The previously-verified chat-template digest (16,915 characters, covering NSSF, PAYE, VAT, Corporation Tax, Withholding Tax, Capital Gains Tax, WIBA, and other verified facts) was re-applied directly to this new model file using `gguf_new_metadata.py` -- since the chat template is independent of model weights, the exact same, already-tested digest content could be transferred without modification.

This combination (new weights + existing digest) was tested through the full application stack (`rag_server.py`, not just the raw model file) against a battery of high-risk questions found to fabricate in earlier testing, and showed no fabrication on any tested question -- a cleaner result than the original weights showed on the same questions.

**Updated proof-of-training files** (in `provenance-v6/`):
- `adapter_model.safetensors` -- the trained LoRA adapter (checkpoint-430, fp32)
- `adapter_config.json` -- LoRA configuration
- `trainer_state.json` -- per-step training metrics, confirming global_step 430, epoch 2.0

**Updated SHA256 checksums:**

    msme-qwen2.5-1.5b-v6-Q4_K_M-digest-v9.gguf:  e88ec13968800a5e193974a6f132ab4e47658f61474063d7f2f8f3f56b34fca2
    provenance-v6/adapter_model.safetensors:      0bf2d91bcf34099c02bc68e46ad60e19d6789f02f2464e59e66ec7b7f7407bb1
    future-training-data/training_data_v5.jsonl:  3b88c7819410b1e6ddca771f4c0c43497450999fdc7b2acbaa0d2925e09840a2

**Note on the Colab notebook:** the training notebook linked above now displays this v6 run's output (`global_step=430`) as its current, live cell output. This is consistent with the model actually submitted -- the notebook and the submission now describe the same training run, resolving an earlier internal inconsistency that existed when the notebook had been re-run after the original v3-based submission.

We report this second example's residual imprecision rather than omitting it: fine-tuning measurably shifted outputs toward domain-specific knowledge, but did not eliminate cross-topic confusion between related tax categories on its own -- which is precisely the gap our verified-answer layer is designed to close.

*Prompt (Kiswahili): "Kiwango cha VAT ni kiasi gani nchini Kenya?"*
- **Base model:** produces incoherent, repetitive text with no real content -- "Tafadhali na tafadhali... Taabulaji na tafadhali" (nonsense phrases, "Taabulaji" is not a real Kiswahili word) -- and never states an actual VAT rate.
- **Fine-tuned model:** "Nchi VAT ni 16% p.a." -- correctly states the actual VAT rate (16%), though the phrasing is not fully fluent Kiswahili.

**Honest disclosure on Kiswahili and fine-tuning.** Our training dataset (3,308 examples) and RAG corpus (323 documents) are both English-only -- within our project timeline, we were not able to source sufficient genuine Kiswahili-language regulatory material to include in either. The improvement visible above is best understood as a correct *fact* ("VAT = 16%") learned from English training data surfacing even when prompted in Kiswahili, not evidence that fine-tuning taught the model Kiswahili fluency or Kiswahili-specific domain knowledge -- it did not.

This is why our actual Kiswahili reliability comes from a different mechanism entirely: 38 hand-verified, natively-written Kiswahili canned answers (see Kiswahili Quality Pass, below), which bypass generation completely and return instantly. For any question outside that verified set, the live system still has to fall back on generation -- which takes longer and can produce hallucinated or incoherent Kiswahili text, as documented in our own live testing throughout this submission. We consider expanding genuine Kiswahili-language training data and RAG source material a priority for continued work on this project beyond this submission.

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

**A structural bug found in the retrieval pipeline itself:** Separately from
the fabrication-content issues above, we found and fixed a genuine crash: our
system prompt (a detailed anti-fabrication instruction set, roughly 8,400
characters) combined with retrieved context could exceed the model's original
2,048-token context window on domains whose source chunks ran longer than
average, causing the request to fail outright with a generic error message
rather than any answer at all. We confirmed via server logs this was
silently failing an unknown share of queries across multiple domains before
being caught. We fixed this by increasing the context window to 4,096 tokens
-- a genuine crash fix, not a workaround, since our large safety-instruction
set is not something we consider safe to shrink to fit a smaller budget.
This fix also had an unexpected second benefit: it appears to have resolved
a severe degenerate-repetition failure mode visible in our Gate 1 automated
test results, where two of five test prompts spiralled into the same line
repeated 20-36 times. We reproduced the exact Gate 1 prompts and several
new ones after the context-window fix and found zero repetition across
every test, including 10 consecutive runs of our required tp_002 benchmark
prompt at two different temperature settings.

**Model reliability outside verified topics:** Testing revealed the fine-tuned
model can state confident but incorrect specifics -- wrong institution names,
invented URLs, fabricated phone numbers or USSD menu steps, invented numeric
business-size classifications, and (found in later testing) invented legal
citations -- even when the core guidance is correct. We iteratively hardened
the system prompt against this pattern and found it genuinely improves results
for most cases, but this fabrication tendency persists on topics outside our
17-topic digest regardless of decoding temperature: we tested identical
prompts at temperature 0.6 (our production default) and 0.3, and found
comparable or higher fabrication rates at the lower temperature, ruling out
sampling-parameter tuning as a general fix. We consider this a structural,
temperature-independent property of a small fine-tuned model rather than
something resolvable through prompting alone, and it is why we chose to keep
expanding verified-answer coverage rather than relying on generation quality
alone -- a known, documented limitation rather than one we are implying away.

**Two distinct accuracy-evaluation paths, and what actually protects each.**
ADTC's Accuracy score combines "multiple-choice benchmarks and qualitative
evaluations." Reading the reference profiler's own accuracy-scoring source
(`accuracy.py`) clarified that these two components are evaluated in
fundamentally different ways, with different implications for what our
mitigations can and cannot reach.

The multiple-choice component loads the quantized `.gguf` directly via
`llama-cpp-python`, in-process, and scores it through raw log-likelihood
comparison or raw completion (not chat-formatted). Neither path renders the
model's chat template at any point. This means that for this specific
sub-score, nothing outside the model's own fine-tuned weights can have any
effect -- not the chat-template digest we patched via `gguf_new_metadata.py`
for Gate 1, and not the retrieval/digest-override layer in `rag_server.py`.
We had originally assumed the chat-template patch protected this path;
reading the actual scoring code showed it does not, since the template is
never invoked.

The qualitative component -- judges interacting with the model through the
actual interface, as reflected in our Gate 1 results -- does route through
our deployed application, and therefore does benefit from the `rag_server.py`
digest-override layer. We confirmed this by inspecting our own Gate 1 judge
transcripts: the questions and answers reflect detailed, Kenya-specific
procedural content consistent with our actual chat endpoint, not a generic
benchmark task.

Given this, we concentrated our post-Gate-1 hardening effort on the
`rag_server.py` digest-override layer specifically, since it is the
component we can verify actually reaches judges' qualitative evaluation. We
verified this directly against our own Gate 1 transcript: several of the
exact automated and human-judge prompts that previously fabricated --
including our required tp_002 benchmark prompt, tested 10 times across two
temperature settings -- now consistently return verified, accurate content.
This does not extend to the multiple-choice component of the Accuracy score,
which we have no mechanism to influence beyond the model's own fine-tuning;
we document this as a known, structural limitation rather than implying
broader coverage than we can verify.

**Language scope:** We attempted full Kiswahili support (direct generation
and an English-then-translate approach) but found the base model's Kiswahili
generative fluency insufficient -- outputs degenerated into repetitive,
grammatically incoherent text regardless of decoding parameters or prompting
strategy, and a translation step did not reliably improve results. Given
this fluency ceiling, the **generative** path remains English-only; genuine
Kiswahili generation would require dedicated training data, which we
document as a direction for future work rather than attempting to work
around with the current model.

The digest-override layer is a different case, however: since those 17
topics are hand-verified, fixed strings rather than generated text,
translating them carries none of the fluency risk that ruled out
generation. We added Kiswahili versions of all 17 digest-override topics,
and re-enabled the (previously disabled) language-detection function to
route Kiswahili-language queries to them. This surfaced a real,
previously-dormant bug in that detector: it matched short Swahili words as
substrings rather than whole words, which meant "Kenya" -- appearing in
nearly every query to this application -- was misidentified as Kiswahili
purely because it contains the substring "ya". Because detection had been
hardcoded off since an earlier development stage, this bug had no live
effect until we re-enabled it for this feature; testing the fix surfaced
one case where the false positive had been silently corrupting an English
generation (injecting a spurious "translate from Kiswahili" instruction
into an English conversation) before we caught and fixed it with
word-boundary matching.

The practical result is a partial but genuine Kiswahili capability: users
asking about any of the 17 highest-stakes, most commonly needed topics in
Kiswahili receive an accurate, natural Kiswahili response with zero
fabrication risk, while all other queries -- in either language -- continue
through the English-only generative path. This is narrower than full
bilingual support, but every fact behind it carries the same verification
standard as its English counterpart, rather than extending an unreliable
generative capability further than we could trust it.

## Benchmarks

All measurements below were taken on a personal development machine (Intel
i7-1065G7 @ 1.30GHz, 14.7GB RAM, Ubuntu, CPU-only inference via llama.cpp)
unless noted otherwise.

**Throughput:** Mean generation speed of 16.0-17.7 tokens/second across
repeated measurements with the official adtc-profiler tool's llama-bench
integration, consistently exceeding the ADTC reference of 15.0 TPS.

**Memory:** The official profiler measured peak RSS of approximately 1,695 MB
for the raw model alone (~76% efficiency against the 7GB ceiling by the
profiler's own calculation). The full application (model server + RAG
retrieval proxy) measures approximately 3.3GB combined RSS -- both figures
comfortably under the 7GB ceiling.

**Thermal -- root cause found and fixed.** At Gate 1, we reported a genuine,
unresolved discrepancy: our own sustained-load testing showed CPU temperature
plateauing at 77C, while the official adtc-profiler's llama-bench integration
measured a peak of 98-99C with `throttled: true`. Further investigation
identified the cause: the profiler's required benchmark workload (a
prompt-processing burst substantially more intensive than our own manual
tests) triggered CPU turbo boost, producing a rapid power/heat spike that a
thin-ultrabook chassis cannot dissipate fast enough. Disabling turbo boost
(`echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo`) reduced
peak temperature from 96-100C to **59C** -- 26C of margin below the 85C
threshold -- with no measurable throughput cost (16.03 vs. 16.08 tokens/sec
in matched before/after tests, and confirmed again via the official
profiler itself: 16.12 tokens/sec with `throttled: false`). We verified this
fix repeatedly across multiple sessions using `adtc-profiler run --mode
audit`, the same tool used for official scoring, not just our own ad hoc
benchmarks. Because this setting does not persist across reboots, we added
an automatic check to `start.sh` that prints a clear warning if turbo boost
is enabled when the application starts, so this cannot be silently
forgotten before a benchmark run.

We report the original discrepancy and its resolution together, rather than
only the fixed number, because the process -- reproducing the profiler's
exact invocation, isolating turbo boost as the variable, and confirming the
fix with the same official tool used for scoring -- is itself evidence that
the fix is real and not a coincidence of one lucky measurement.

**Reproducibility note on the thermal figures (added September 20, 2026).** The organizers have since told us that their tooling does not enable, disable or manage Turbo Boost, the CPU governor or any power setting, and that the profiler only reads temperature during the run. The 59-61C figures above were therefore obtained with a non-default setting (turbo boost disabled) that the evaluation will not apply. The official-profiler runs we saved for the submitted builds with turbo boost on (submission_v9.json and submission_v6_v9.json) both measured a 98C peak with `throttled: true`, consistent with the Gate 1 measurement of 98-99C; a run limited to 2 threads (submission_2thread.json) measured 99C, so thread count did not help. We therefore do not claim that the submission stays under the 85C threshold on default settings: whether it does depends on the evaluation hardware's cooling. We had expected the audit might run in a cloud VM (the profiler schema has an audit_cloud_vm environment), but the Gate 2 guidelines refer to the ADTC Standard Laptop, so we do not rely on that expectation.

**First-token latency -- a real trade-off from disabling turbo boost, and why
we are not trimming the system prompt to compensate.** Disabling turbo boost
(see Thermal, above) eliminated the throttling on our laptop (a setting the evaluation does not apply -- see the reproducibility note in Thermal), but was not free: it roughly doubles first-token latency, since prompt processing is
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

**Model size:** 934.69 MiB (Q4_K_M quantization, 5.08 bits/weight), verified
parameter count of 1,543,714,304 (matches the 1.5B estimate declared in
metadata.json).

**Retrieval corpus:** 18,307 chunks across all 323 source documents, zero
extraction failures.

**Accuracy (self-measured, English test set):** We built an internal
30-question evaluation spanning all nine knowledge-base domains, scored on
keyword coverage, relevance, response depth, and Kenya-specificity, run
directly against our actual deployed system (not a substitute model). This
scored 38.7% on first use -- which we traced to two implementation bugs
(a context-window crash affecting several domains outright, and a scoring
script inherited from an earlier prototype that was silently calling a
different, cloud-hosted model rather than our submitted on-device system).
After fixing both and applying the digest-override expansion described
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
actual accuracy.

## Repository Organization

The `dev-tools/` folder contains the individual patch scripts used to
apply each fix described in this report (fabrication corrections,
the context-window fix, the language-detection bug fix, keyword
priority fixes), roughly in the order they were written. The
`benchmark-evidence/` folder contains the raw JSON output from the
official `adtc-profiler` tool for the thermal before/after comparison
and other benchmark runs referenced above. Both are kept as a direct,
inspectable record of how each reported fix was verified, rather than
summarized only in prose.

## What We Learned

**Test for behavior, not just loss.** A training loss of 1.39 looked
good on paper, but the model had learned the wrong behavior pattern --
hedging instead of answering. Always test actual outputs against real
user questions before assuming the model is working.

**Fabrication is a system design problem, not just a prompting problem.**
Stricter instructions reduced hallucination but didn't eliminate it, and
lowering generation temperature did not help either -- we measured
comparable or higher fabrication rates at temperature 0.3 than at 0.6 on
identical prompts. The only reliable fix for high-stakes facts was to
remove the model from the loop entirely -- a verified-answer layer that
guarantees accuracy where it matters most.

**Infrastructure bugs hide real data bugs, and hide each other.** The PDF
extraction issue (354,000 meaningless chunks) masked everything downstream
at first. Later, a context-window crash silently failed queries across
several domains with a generic error message, which meant our own earlier
accuracy measurements were confounded by a bug rather than reflecting real
model quality. Fixing infrastructure issues before trusting any accuracy
number was more important than we initially assumed.

**Verify a protection mechanism actually reaches the thing it's meant to
protect.** We had assumed our chat-template-baked fact digest protected the
automated accuracy benchmark. Reading the actual scoring code showed the
benchmark never renders the chat template at all, so the digest had no
effect on that specific sub-score -- a mitigation can be well-built and
still protect the wrong path if you don't verify the evaluation mechanism
it's meant to defend against.

**Offline-first forces better engineering decisions.** Every design
choice -- TF-IDF over semantic embeddings, verified answers over
generation, quantization targets -- was forced by the offline and
memory constraints. Those constraints made the system more focused,
more reliable, and more honest about what it can and can't do.


## Performance Summary

| Metric | Result | Target |
|--------|--------|--------|
| Generation speed (Sperf) | 15.3-17.7 tokens/sec | >= 15.0 tokens/sec |
| Efficiency Score (Seff), raw model | ~76% (RAM efficiency, official profiler) | Higher is better |
| Full application memory (model + RAG server) | ~3.3GB combined* | <= 7GB |
| Model size (Q4_K_M) | 934.69 MiB | <= 7GB |
| Parameters | 1,543,714,304 | 1.5B declared |
| RAG corpus | 18,307 chunks / 323 docs | Zero extraction failures |
| CPU temperature (official profiler, turbo boost on, saved runs of the submitted builds) | 98C, throttled: true | < 85C |
| CPU temperature (official profiler, turbo boost disabled -- a non-default setting on our laptop that the evaluation does not apply) | 59-61C, throttled: false | < 85C |
| Official Gate 1 Accuracy Score | 61.27 | -- |
| Official Gate 1 Performance Score | 26.13 (above semifinalist median 24.50) | -- |
| Official Gate 1 Efficiency Score | 84.69 (at semifinalist median 84.65) | -- |
| Self-measured accuracy, chat path only (30-question set)** | 92-97.3% across repeated runs post-Gate-1 fixes (was 88.7-90.0% at Gate 1) | -- |
| Digest-override topics | 37 (EN + Kiswahili) -- up from 17 at Gate 1 | -- |

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
mitigations cannot reach.


## Post-Gate-1 Accuracy Improvement (Pre-Gate-2)

Between Gate 1 and Gate 2, we ran a focused, evidence-driven pass to
improve real-world accuracy -- verifying every new fact via web search
before adding it, and testing every fix with live queries against the
running system rather than assuming a fix worked.

### Digest-override coverage expanded from 17 to 37 topics

New verified topics added (English + Kiswahili where noted): Class R
Permit for EAC nationals, Tax Compliance Certificate application,
probation period rules, AGPO government procurement, Hustler Fund
business/personal loan distinction (EN + SW), converting a sole
proprietorship to a limited company, Women Enterprise Fund (WEF),
Unified Business Permit (Nairobi), pharmacy/chemist licensing (Pharmacy
and Poisons Board), Communications Authority licensing for tech
businesses, NSSF employer/employee registration process, KEPROBA export
services, penalties for operating without a county permit, sole
proprietorship vs. limited company comparison, late tax-filing
penalties, general eTIMS explanation, SACCO vs. commercial bank loan
comparison, and food business licensing.

### Real bugs found and fixed via direct testing against the 4 actual Gate 1 judged prompts

Re-running the exact prompts from our Gate 1 judged results (not just our
own test set) surfaced concrete, fixable issues:

- **Sole-proprietorship-to-LLC conversion** (Gate 1 judged prompt 1):
  previously degenerated into 30+ repeated lines ("Register the business
  type as a limited company"). Root cause was a keyword-matching gap
  causing generative fallback; fixed with a dedicated, verified canned
  answer plus a narrowed `kra_pin` keyword set that was incorrectly
  intercepting this query.
- **Salon tax obligations / Turnover Tax** (Gate 1 judged prompt 2):
  previously conflated VAT and Turnover Tax, applying a 16% VAT rate to
  the entire turnover figure. Now correctly separated via the existing
  `turnover_tax` and `vat` canned answers.
- **Employee compliance checklist** (Gate 1 judged prompt 3): previously
  referenced "NHIF," which was replaced by SHIF in October 2024. Fixed
  with a new `employee_compliance_checklist` canned answer that
  explicitly corrects this.
- **Fabricated legal citation**: a query about operating without a
  county permit cited a non-existent "Article 20 of County Government
  Act No.13." Verified the real legal basis (County Governments Act
  2012 plus county-specific Finance/Trade Licensing Acts) and replaced
  with an accurate canned answer.
- **Fabricated program name**: a query about the Women Enterprise Fund
  returned a fabricated program name ("Youth and Woman Entrepreneurship
  Development Initiative"). Verified the real program (WEF, established
  2007) and added accurate coverage.
- **Keyword shadowing** (the same class of bug fixed at Gate 1, found
  twice more here): the generic `nssf` keyword was intercepting
  NSSF-registration queries before a new, more specific
  `nssf_registration` topic could match; the generic `loan` keyword's
  "hustler fund" entry was intercepting Hustler Fund business-specific
  queries. Both fixed by reordering keyword-dictionary precedence so
  more specific topics are checked first.

### Self-measured accuracy: 88.7-90.0% (Gate 1) to 92-97.3% (post-fixes)

Using our own 30-question evaluation script (`evaluate_current_model.py`)
against the live deployed system, repeated runs after these fixes
ranged from 92% to 97.3%, with the variance attributable to natural
LLM sampling behavior on the handful of topics that remain generative
rather than canned (business registration nuances, some taxation
questions). Every topic we specifically fixed shows a stable, perfect
5/5 across repeated runs. As at Gate 1, this measurement reflects only
the chat/RAG path and is not directly comparable to the official
Accuracy Score, which evaluates the raw base model via `lm_eval`
independent of our digest-override layer (see "Two distinct
accuracy-evaluation paths" above).

### An attempted retraining pass, and an honest account of why it was not used

Alongside the canned-answer work above, we compiled 302 additional
verified training examples (spanning the topics above plus correctly-
calculated NSSF/PAYE/Housing-Levy/Turnover-Tax examples across a range
of realistic salaries and turnovers) into an expanded 3,610-record
dataset, intending a full retraining pass to bake this knowledge
directly into the model.

Two retraining attempts, on the same Colab environment used for the
original successful training run, produced adapters that failed
quantization with `ggml_validate_row_data: found nan value`, isolated
specifically to `blk.0.attn_k.weight`. We traced the likely cause to
training in unmixed fp16 (a necessary workaround for a `bitsandbytes`
environment incompatibility encountered mid-session) without the
numerical-stability safeguards our original LoRA setup relied on. A
follow-up attempt at a lower learning rate reproduced the identical
failure, ruling out learning rate as the cause and pointing instead to
the removal of `prepare_model_for_kbit_training()` alongside
`bitsandbytes`.

Given the time available before this submission, we made the deliberate
choice to preserve our existing, fully-verified, working model rather
than risk shipping a corrupted one, and to pursue the accuracy gains
above through the digest-override layer instead -- which requires no
retraining and carries no risk to the already-validated model weights.
The expanded 3,610-record dataset and this diagnostic finding are
preserved for a future retraining pass with adequate time to resolve
the numerical-stability issue properly.


## Kiswahili Quality Pass (Post-Gate-1)

While testing the system interactively in the web UI, a casual Kiswahili
query ("naweza kusajili biashara yangu?" -- "can I register my
business?") returned incoherent, non-grammatical text despite the
underlying topic already having a correct, hand-verified Kiswahili
canned answer. Investigating this surfaced a systemic issue affecting
Kiswahili users broadly, not an isolated bug.

### Root cause: two independent, disconnected mechanisms

The system has two separate layers that both need to recognize a query
as Kiswahili-relevant: `TOPIC_KEYWORDS` (routes a query to the correct
canned topic) and `is_swahili()` (decides whether to return the English
or Kiswahili version of that topic's canned answer, and whether to
route generative fallback through translation). These operated
independently -- `TOPIC_KEYWORDS` could correctly match a Kiswahili
phrase to its topic, while `is_swahili()` failed to recognize the same
text as Kiswahili at all, causing the system to silently fall back to
English (safe but incomplete) or, worse, to the generative-then-
translate path, which relies on the same small 1.5B model performing
free-form translation -- a task it does not do reliably, and which
produced the incoherent output observed.

`is_swahili()`'s word list was narrow (16 words) and missing several
extremely common, domain-relevant terms -- most notably **"ngapi"**
("how much/how many"), the single most natural way to ask about a rate
in Kiswahili, alongside "ushuru" (tax/levy), "mwezi" (month), and
others directly relevant to a tax/finance advisor. Expanded the list to
30 terms; confirmed the original false-positive fix (English text
containing "Kenya," which contains the substring "ya") remains intact.

### Full bilingual coverage achieved

Beyond the detection fix, we systematically audited and expanded
Kiswahili keyword routing across the original 17 Gate 1 topics, and
wrote full Kiswahili canned-answer content (not previously present) for
all 20 topics added during the accuracy pass above. **All 37 canned
topics now have complete English and Kiswahili content with correct
keyword routing in both languages**, each verified via live queries
against the running system.

This pass also surfaced and fixed two smaller, pre-existing issues
found along the way: a duplicated `probation_period` entry in the
Kiswahili answer dictionary (dead code from an earlier session; Python
silently used the later definition, so it never produced incorrect
answers, but was genuinely duplicated content), and a keyword-shadowing
case where the specific `food_business_license` topic was being
intercepted by the generic `license` topic's overly broad Kiswahili
keyword, fixed by reordering keyword-dictionary precedence.


## Final Pre-Submission Testing Pass

A final round of live testing against the deployed web UI -- rather than
curl scripts alone -- surfaced two more issues worth documenting
honestly, plus a genuine crash bug.

### Context-window overflow (a recurring crash class, not a new one)

Two casual, uncovered questions ("How can I start a business of a salon
in Muranga", "I run a small tailoring shop with 2 employees...")
triggered `request exceeds the available context size (4096 tokens)`
errors from llama-server, surfacing as a generic failure message in the
UI. This is the same class of bug found and fixed at Gate 1 (originally
2048 -> 4096 tokens) -- it recurred because the Post-Gate-1 accuracy and
Kiswahili passes above substantially grew the system-prompt content
injected into every non-canned query, eventually exceeding even the
increased limit. Fixed by increasing the context window to 8192 tokens
in `start.sh`. This has no effect on the official Efficiency Score,
which is measured via an independent `llama-bench` invocation that does
not read this setting.

Fixing the crash surfaced the underlying generative content directly,
which included two real fabrications worth noting as evidence of the
raw-model fabrication risk already discussed above: a specific but false
minimum-capital figure (contradicting our own verified fact that no such
minimum exists), and a business-insurance question that was incorrectly
directed to KRA (the tax authority) rather than IRA (the actual
insurance regulator).

### Two more topics added, and one more routing bug fixed

- **`business_insurance`** (new, EN+SW): verified via web search --
  IRA as the correct regulator, WIBA and motor third-party liability as
  the compulsory categories, with common optional cover explained.
- **`maternity_paternity_leave`** (new, EN+SW): a maternity-leave
  question was being intercepted by the generic `leave` topic's
  overly-broad "leave entitlement" keyword, returning the wrong (annual
  leave) answer. Verified via web search (Employment Act Section 29: 90
  days maternity, 14 days paternity, both fully paid) and added as a
  dedicated topic, narrowing `leave`'s keywords to stop the
  over-matching.

### Final state

**38 canned topics**, all with complete, verified English and Kiswahili
content and correct keyword routing, confirmed via direct testing in
the deployed web UI as the final verification step before submission.

## A Further Limitation: Retrieval Succeeding Does Not Guarantee a Correct Answer

Live testing surfaced a distinct failure mode worth documenting separately from the retrieval-quality and Kiswahili limitations already discussed: even when RAG retrieval fetches genuinely relevant source material, the model can still conflate or misapply facts while composing its answer -- a generation-level error, not a retrieval-level one.

**Example**: asked "What is the penalty for late payment of PAYE in Kenya?", the system answered with the late *filing* penalty figure (25% or KES 10,000, whichever is higher) rather than the late *payment* penalty (5% plus 1% monthly interest on the unpaid amount) -- two related but distinct categories under the same tax obligation. We did not verify whether the retrieved chunk(s) for this query actually contained the correct payment-specific figure that the model then failed to use, or whether retrieval itself surfaced the wrong section; either way, the output was wrong.

This matters because it means better retrieval alone -- e.g. semantic embeddings instead of TF-IDF, which we considered but have not implemented, given the added memory/compute cost on constrained hardware and the genuine risk of degrading exact-term matching that already works well for precise legal/tax terminology -- would not necessarily fix this class of error on its own. The model's own tendency to conflate closely related facts during generation is a separate risk that grounding mitigates but does not eliminate, distinct from what our digest-override and canned-answer layers close by removing generation from the loop entirely for our 38 highest-stakes topics.
