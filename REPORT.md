# Technical Report: Rafiki wa Biashara, an offline advisor for Kenyan MSMEs

## Summary

Rafiki wa Biashara answers questions about Kenyan tax, business registration, employment obligations and financing, entirely offline. The model file (Qwen2.5-1.5B-Instruct, LoRA fine-tuned, quantized to Q4_K_M) runs at about 17 tokens per second on my laptop and needs about 1.7 GB of memory at peak.

In my tests the model file usually gets headline figures right (16% VAT, 6% NSSF per side), but it often adds wrong details around them, and it answers some topics wrongly: payroll obligations, SHIF and company-registration steps. A separate, optional application adds retrieval and pre-written verified answers that fix most of these, but only when the application is used. Kiswahili works only through those verified answers; the model file itself is English-only. The sections below give the measurements and say which part of the system each result comes from.

## Problem

Kenyan micro, small and medium enterprises (MSMEs) deal with a lot of rules: KRA tax registration, NSSF and SHIF contributions, county business permits, VAT thresholds, employment law and financing programmes. Most owners cannot pay a lawyer or accountant to explain them. Cloud AI assistants need a steady connection and often a subscription, which is a problem for someone running a shop, salon or workshop on a modest laptop with unreliable internet.

Rafiki wa Biashara ("friend of business" in Kiswahili) is an offline assistant that runs on ordinary hardware. It is meant to save an owner a trip to a government office, or a consultant's fee, for basic procedural questions: how to register a business, how to apply for a startup loan, which taxes apply, what an employer owes. The target user is an MSME owner with 1-20 employees who wants plain answers to routine questions.

## Design Decisions

### Two parts: the model file and the application

I keep these apart throughout the report because results depend on which one was used.

1. **The model file (GGUF).** Qwen2.5-1.5B-Instruct fine-tuned with LoRA and quantized to Q4_K_M, with a digest of verified facts written into its chat template. This is the file `download_model.sh` fetches and the file the profiler loads.
2. **An optional application** (`rag_server.py`, a small Flask proxy, plus a web interface). It adds a retrieval layer, a set of pre-written verified answers and a longer system prompt. It needs the model file, but the model file does not need it.

### Base model and quantization

I chose Qwen2.5-1.5B-Instruct because it is small enough to quantize well under the 7 GB memory ceiling and still follows instructions well enough to give structured advice. Q4_K_M brings the file to 986,062,592 bytes (about 940 MiB, roughly 5.1 bits per weight), which leaves a lot of headroom.

### Retrieval

A 1.5B model cannot hold the number of specific facts a compliance advisor needs. An initial factual audit before any mitigation found about a 25% error rate on regulatory specifics. So the application searches a local knowledge base with TF-IDF (chosen over semantic embeddings to keep memory use low) before the model answers. The knowledge base has 323 source documents in nine categories: legal and regulatory, tax and KRA, financing, social security, digital trade, county and geospatial, culture and context, national policy, and bank lending. The retrieval layer is what ties the language model to the legal and regulatory source material. It belongs to the application, not the model file.

### Verified answers

Retrieval alone was not enough. Showing the model tables extracted from regulatory PDFs (for example the NSSF contribution tiers) sometimes produced worse answers than giving it a few facts I had checked myself. For high-frequency, high-stakes topics the application therefore skips generation and returns a pre-written answer that I verified against KRA, NSSF and other official sources. The set grew from 10 topics to 17, then 37, and is now above 40. Most have both English and Kiswahili versions. The employee-compliance checklist and the five answers added on September 20 (compliance software, "are those all the regulations", county relocation, barber and salon taxes, sole-proprietor-to-company mistakes) are English-only.

### What is inside the model file

The chat template of the GGUF carries a digest of verified facts (16,915 characters, made of three copies of the same text, one for each branch of the template). A text search of the digest in the submitted file shows it covers NSSF tiers, PAYE, VAT, KRA PIN, Turnover Tax (including the rule that no expenses are deducted), Corporation Tax, Withholding Tax, Capital Gains Tax, WIBA, Excise Duty, Stamp Duty, Rental Income Tax, Digital Service Tax and the NITA levy. It does not contain SHIF, the Housing Levy, payroll remittance deadlines, eTIMS, sole proprietorship, company-registration forms, county permits or the steps for registering a business name. Several of my raw-model failures below trace to those gaps.

### Alternatives considered

Fine-tuning without retrieval, which the audit above ruled out. A larger digest, which I tried and describe under Development Notes. Semantic embeddings for retrieval, which I did not build because of the memory cost and the risk of weakening the exact-term matching that already works for legal and tax terms.

## Model Provenance

### Summary (matches `metadata.json`)

- **Base model source:** `huggingface:Qwen/Qwen2.5-1.5B-Instruct`
- **Base model commit SHA:** `989aa7980e4cf806f80c7fef2b1adb7bc71aa306` (in `metadata.json` as `model.base_model_commit_sha`)
- **Fine-tuning method:** `lora`
- **Training datasets:** `training_data_v5.jsonl` (3,610 records, used for the submitted weights) and `training_data_v4_merged.jsonl` (3,308 records, used for an earlier first run). Both are synthetic conversational datasets I generated from the regulatory source documents I collected. No third-party dataset was used.

On field layout: on September 21, 2026 the public adtc-profiler (commit 12be4f3) rejected the template's root `provenance` object with "Additional properties are not allowed", but accepted `model.base_model_commit_sha`. So that is the only provenance field in `metadata.json`, and the rest is stated here.

### Repository state

This report and the submission reflect git commit `1eddb722fa5f3afd9a2c9230046638201a00c5e9` on the `main` branch, the last commit that changed code or the model. Later commits change only documentation, `download_model.sh`, `metadata.json` and the `provenance/` folder. The profiler records this repository's own commit automatically in the `reproducibility` object of its output report, so that value is not in `metadata.json`.

### Base model

[Qwen/Qwen2.5-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct), loaded with `transformers.AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")` at training time, with no pinned revision. At that time `main` pointed to commit `989aa7980e4cf806f80c7fef2b1adb7bc71aa306` (2024-09-25), the repository's most recent commit, which predates all my training runs.

### Fine-tuning

I trained two LoRA runs with the same configuration: rank 16, `lora_alpha=32`, `lora_dropout=0.05`, `bias="none"`, target modules `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj` (18,464,768 trainable parameters), TRL's `SFTTrainer`, 2 epochs, batch size 4 with gradient accumulation 4, learning rate 2e-4 with a cosine schedule and 3% warmup, on a Colab T4.

| | First run | Second run (submitted) |
|---|---|---|
| Dataset | `training_data_v4_merged.jsonl`, 3,308 records | `training_data_v5.jsonl`, 3,610 records, 3,429 used for training |
| Steps | 394 | 430 |
| Mean training loss over the run | 1.3941 (last logged step: 1.2827) | 1.3378 (last logged step: 1.2107) |
| Adapter | fp16, 36,981,856 bytes | fp32, 73,911,112 bytes |
| Files | `provenance/original-run/` | `provenance/` |

The two runs used different data, so the loss values are not a like-for-like comparison. The second dataset is the first plus 302 more verified examples, covering the topics added after the first run and worked NSSF, PAYE, Housing Levy and Turnover Tax calculations at a range of salaries and turnovers. Generation scripts are in `future-training-data/generation-scripts/`. The runs differ only in their training data (which also changes the step count) and in the saved precision of the adapter, fp16 for the first run and fp32 for the second. Both builds carry the same fact digest (v9) in the chat template, and the application is independent of either model file, so the submitted file, the second run plus digest v9, contains every improvement made to the weights and the digest.

Before the second run succeeded, my first retraining attempts failed. The adapters had NaN weights and quantization stopped with `ggml_validate_row_data: found nan value` at `blk.0.attn_k.weight`. A run at a lower learning rate failed the same way, which ruled out the learning rate. I traced the cause to training in unmixed fp16, after a `bitsandbytes` incompatibility forced me to drop the numerical-stability setup of the original run. The successful run saved its adapter in fp32.

### Merge and quantization

The adapter was merged into the base model with `peft.PeftModel.from_pretrained()` and `merge_and_unload()`, converted to GGUF with llama.cpp's `convert_hf_to_gguf.py`, and quantized to Q4_K_M with `llama-quantize`. The notebook `provenance/My_Offline_AI_advicer_for_kenyan_msmes.ipynb` is included, and there is a Colab link: [colab.research.google.com/drive/1jpcZW0uXTLsfxPQCT2AYnKfoLRiyrdIV](https://colab.research.google.com/drive/1jpcZW0uXTLsfxPQCT2AYnKfoLRiyrdIV?usp=sharing). The notebook in the repository keeps the cell outputs of the first run (`global_step=394`). The log of the submitted run (`global_step=430`) is in `provenance/trainer_state.json` and `provenance/training_log.txt`.

After quantization I wrote the fact digest into the chat template with `gguf_new_metadata.py`. This changes metadata only, not the weights, so the same digest could be applied to the new file without changes. On September 18 I extended it by ten facts (Corporation Tax, Withholding Tax, Capital Gains Tax, WIBA, Excise Duty, Stamp Duty, Rental Income Tax, the Turnover Tax deduction rule, Digital Service Tax and the NITA levy). Each came from a base-model comparison that found wrong answers, and each was checked against KRA's published guidance first. Two facts (Stamp Duty and Rental Income) needed a second patch that named the wrong answer explicitly ("this rate applies to X, not Y"). For NITA, sources disagree on the current levy (KES 50 a month under the 2007 rate, or KES 600 a year after a 2020 amendment that a 2022 Act may have reversed), so the digest tells the model to say the rate has changed and to check with NITA or KRA.

The provenance folder holds `adapter_model.safetensors` and `adapter_config.json` for the submitted run, `trainer_state.json`, `training_log.txt`, `dataset_info.md`, `merge_and_quantization.md`, the notebook (whose cell outputs are from the first run), and `original-run/` for the first run.

### Checksums

    Submitted model file (v6 weights + digest v9):
      e88ec13968800a5e193974a6f132ab4e47658f61474063d7f2f8f3f56b34fca2
    provenance/adapter_model.safetensors (submitted run):
      0bf2d91bcf34099c02bc68e46ad60e19d6789f02f2464e59e66ec7b7f7407bb1
    future-training-data/training_data_v5.jsonl:
      3b88c7819410b1e6ddca771f4c0c43497450999fdc7b2acbaa0d2925e09840a2
    provenance/original-run/adapter_model.safetensors (first run):
      962a625b15ef4a7b8c67a38982dcb395b065b87cba1604170597a751704ec623
    provenance/original-run/training_data_v4_merged.jsonl:
      f238a4290e0d5a173147c20a52a503cd718149489693c995c245ec99bde016b8
    Earlier build, not submitted (first-run weights + digest v9):
      9db039ebc56c279555fa4e09e77f0be5ed82328ed3e6e8fe4e19621c13792ae5

### Pinned download and hand check

`download_model.sh` pins the file to Hugging Face commit `c73de544d83d85040cd3984fd180c718725200e3`. The template's download script does not check hashes, so after running it, `sha256sum model/msme-qwen2.5-1.5b-Q4_K_M.gguf` should print `e88ec13968800a5e193974a6f132ab4e47658f61474063d7f2f8f3f56b34fca2`.

### Before/after comparison for the submitted file

These are the two test prompts in `metadata.json`: annual leave (`tp_001`) and turnover tax rate (`tp_002`). Each ran once at temperature 0 (context 2048) through llama-server on the unmodified Qwen2.5-1.5B-Instruct Q4_K_M file and on the submitted file, with no retrieval, verified answers or system prompt. The full outputs are in `provenance/before_after_outputs.md`. The base file has the stock chat template and the submitted file carries the digest, so the difference shows the fine-tuned weights and the digest together. I did not run the fine-tuned weights without the digest.

**"How many days of annual leave is an employee entitled to in Kenya?"** The base model says 20 days and calls it "a common practice across many countries, including Kenya", which is wrong for Kenya. The submitted model says a minimum of 21 working days per year, which is right (Employment Act, section 28: 21 working days for every 12 months of service). It also says there is "no lower limit set by law", that the entitlement applies "regardless of the employee's length of service or salary level", and that the calculation is left to "employment regulations rather than fixed statutory rules". These statements are wrong or misleading: leave accrues over 12 months of service and the Act sets the number.

**"What is the turnover tax rate for small businesses in Kenya?"** The base model gives no rate ("As an AI developed by Alibaba Cloud, I don't have real-time data...") and refers the user to the tax authority. The submitted model gives 1.5% of gross sales with no expense deductions and a correct worked example (KES 2 million of sales gives KES 30,000). I found no wrong figure in this run. It does not give the eligibility range (turnover above KES 1,000,000 and up to KES 25,000,000), and it calls the tax "a separate tax from income tax", which is loose: Turnover Tax is a final tax on turnover that replaces income tax for businesses in the regime.

In both cases the submitted file answers where the base model is wrong or declines. For annual leave it adds wrong detail to a right number, and the turnover tax answer is correct as far as it goes.

### Earlier prompt pair (NSSF and VAT)

Before the current pair I used the NSSF prompt and "What is the VAT rate?", run the same way (the outputs are also in `provenance/before_after_outputs.md`).

- **"What are the NSSF contribution rates for an employee earning KSh 30,000 per month?"** The base model gave no figure for KSh 30,000 and listed three invented rates (a "Basic Contribution Rate", a "Contributory Pension Rate" and a "Contributory Provident Fund Rate"), each "typically around 10%". The submitted model gave 6% and KES 1,800 for each side, which is correct, but a combined total of KES 3,420 (it should be 3,600) and said no Tier I or Tier II applies (both do, 540 plus 1,260 per side). An earlier temperature-0 run of the same file gave 1,800 per side and 3,600 in total, so temperature-0 output is not always reproducible on my setup.
- **"What is the VAT rate?"** The base model did not mention Kenya and listed rates for other countries (United States 0%, European Union 21%, China 13%; the EU has no single rate). The submitted model answered for Kenya with the correct 16%, but said it applies "on all supplies and services" (some supplies are zero-rated or exempt) and "to top-up an existing KRA PIN account", which is meaningless.

### Earlier examples (first run, application layers off)

- NSSF at KSh 30,000: the base model invented a "1.5% to 2.5%" rate and an "Additional Contribution Rate"; the fine-tuned model gave 6% plus 6%, KSh 1,800 each.
- "What is Turnover Tax in Kenya and who qualifies to pay it?": the base model confused it with VAT, gave a "KES 100,000" threshold and an "18% progressive" rate, and invented a "Goods and Services Tax". The fine-tuned model used Kenyan terminology and a real figure (KES 5,000,000) but still mixed up the Turnover Tax and VAT thresholds. This is the reason Turnover Tax has a verified answer.
- "Kiwango cha VAT ni kiasi gani nchini Kenya?": the base model produced repetitive nonsense ("Tafadhali na tafadhali... Taabulaji na tafadhali") and never gave a rate. The first-run model answered "Nchi VAT ni 16% p.a.", which has the right rate in imperfect Kiswahili. This shows an English-trained fact surfacing in Kiswahili, not Kiswahili ability. The submitted weights answer this question differently on the raw file (in English, opening with the registration threshold).

## Constraints

### Hardware and connectivity

The target is the ADTC Standard Laptop (Intel i5 10th-12th generation or Ryzen 5, 8 GB DDR4, integrated graphics). I developed and tested on a personal laptop (Intel i7-1065G7, 14.7 GB RAM), which is more powerful. Nothing needs the network at run time: inference, retrieval and generation all happen locally through llama.cpp and a local Flask proxy.

### Data extraction

96 of the 323 source documents are PDFs. My first indexing pipeline decoded PDF bytes as plain text and produced about 354,000 mostly meaningless chunks. I rewrote extraction with pypdf and detected PDFs by content and not by file extension. That exposed five source files corrupted at the source (a failed scrape, or raw PDF bytes saved as `.txt`) and three scanned PDFs without a text layer, which now go through OCR with pytesseract. All 323 documents now index without extraction failures, giving 18,307 chunks. A later change to the index build (commit `a00effc`) drops chunks that are under half alphanumeric or have fewer than 100 alphanumeric characters, and the application's current index loads 15,775 chunks.

### Context window

The application's system prompt (about 8,400 characters of anti-fabrication rules) plus retrieved text could exceed the original 2,048-token context, and requests then failed with a generic error instead of an answer. Server logs showed this had been failing an unknown share of queries. I raised the window to 4,096 tokens, and to 8,192 (`start.sh`) after later additions to the prompt caused it again. This setting does not affect the profiler's memory measurement, which runs `llama-bench` separately.

In early tests, two of five automated prompts repeated the same line 20-36 times through the application. After the context fix I found no repetition on replays. Later tests of the submitted file directly (2,048 and 8,192 context, several temperatures) showed no looping either, so I cannot say whether the early loops came from the context limit or from the earlier model file.

### Reliability outside the verified topics

The fine-tuned model can state wrong specifics with confidence: wrong institution names, invented URLs, made-up phone numbers and USSD steps, invented business-size categories and invented legal citations (for example a non-existent "Article 20 of County Government Act No. 13", or an insurance question sent to KRA instead of the insurance regulator, IRA). I hardened the application's system prompt against these, which helped in most cases, but the tendency remains outside the verified topics. It did not depend on temperature: at 0.3 I found the same or more fabrication than at my production default of 0.6.

Even when retrieval fetched the right material, the model sometimes mixed up related facts. Asked for the late-payment penalty on PAYE, it gave the late-filing figure. I did not check whether the retrieved text contained the right number.

### How the two evaluation paths see the system

The profiler's accuracy step (`accuracy.py`) loads the GGUF with `llama-cpp-python` at a 2,048-token context and temperature 0, and scores raw log-likelihood or raw completions. It never applies the chat template. On that step only the fine-tuned weights count: the digest in the template cannot affect it, and neither can any application layer. I had assumed the digest protected this step, and reading the scoring code showed it does not.

For questions answered in chat form, what applies depends on how the file is run. The submission template describes the file being downloaded and run through llama.cpp, and it does not mention the application, so I treat the GGUF as the submission and the application as an optional extra. If a harness applies the chat template the digest is in play, and if it sends bare text only the weights are. I tested the file both ways. The profiler runs I saved for the submitted builds skipped the accuracy step, so I have no profiler accuracy figure for the final file.

## Benchmarks

All measurements are from my development laptop (Intel i7-1065G7 at 1.30 GHz, 14.7 GB RAM, Ubuntu, CPU-only inference) unless noted. Results on other hardware, including the evaluation machine, may differ.

### Throughput and memory

Generation speed is 16-18 tokens per second in my saved profiler runs. The latest three runs on a clean clone of the final submission gave 17.65, 17.90 and 17.91, above the 15.0 reference. Peak memory for the model file alone is about 1,695 MB, which is roughly 76% efficiency against the 7 GB ceiling by the profiler's formula. The full application (model server plus retrieval proxy) uses about 3.3 GB combined. Both are under 7 GB, but they measure different things.

### Temperature

Early on, my own sustained-load test plateaued at 77 C, while the profiler's benchmark measured a peak of 98-99 C and flagged throttling. I traced the difference to turbo boost: the profiler's workload is a burst of prompt processing, heavier than my manual tests, and it triggers a heat spike that a thin laptop chassis cannot shed quickly. With turbo boost disabled (`echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo`) the peak fell from 96-100 C to 59-61 C with no throttling and no measurable change in generation speed (16.03 against 16.08 tokens per second in matched tests, and 16.12 with `throttled: false` in a profiler run).

The competition organizers later told me that their tooling does not enable, disable or manage turbo boost, the CPU governor or any power setting, and that the profiler only reads temperature during the run. So the 59-61 C results come from a setting the evaluation will not apply, and I do not claim the submission stays under 85 C on default settings. With turbo boost at its default, my saved profiler runs of the submitted builds (`submission_v9.json`, `submission_v6_v9.json`) both peaked at 98 C, and a run limited to two threads peaked at 99 C, so thread count does not help. Three consecutive runs on a clean clone of the final submission peaked at 98, 86 and 95 C. All are at or above the 85 C threshold and were flagged as throttled, and the spread shows the reading depends on the machine's thermal state.

The profiler's documentation says audit mode runs in cloud VMs, where temperature sensors are often unavailable, but the submission rules refer to a standard laptop profile. I cannot check which applies, so I do not rely on either. Whether the thermal penalty applies depends on the evaluation hardware.

### First-token latency

With turbo boost enabled, first-token latency averages about 3.6 seconds. With it disabled it roughly doubles to 7.5-7.8 seconds, because prompt processing is compute-bound. This held on an idle machine, so background load was not the cause. Generation speed is unaffected either way.

I considered shortening the application's system prompt to reduce prefill time and decided against it. Nearly every rule in it corresponds to a specific fabrication I had observed, and I could not re-test every earlier case in the time available. I prefer to widen the set of verified answers, which removes those questions from the slow generation path altogether.

### Model file, corpus and application accuracy

The model file has 1,543,714,304 parameters, matching the 1.5B declared in `metadata.json`. The retrieval corpus is described under Constraints.

I also built a 30-question evaluation across the nine knowledge-base domains, scored on keyword coverage, relevance, depth and Kenya-specificity, and ran it against the deployed application. The first run scored 38.7%, because of two bugs: the context-window failure above, and a scoring script inherited from an earlier prototype that was calling a cloud-hosted model, not the on-device system. After fixing both and expanding the verified answers, three full runs scored 88.7%, 90.0% and 89.3%, and later runs 92% to 97.3%. The variance comes from the few topics that still go through generation. Every topic I fixed specifically scored 5/5 in repeated runs.

This figure measures the application and my own question set. It says little about the model file itself: the file gets the two test prompts' headline figures right but answers several topics wrongly, as the next section shows.

## Testing the Submitted Model

I ran a fixed set of 17 questions, five automated-style prompts and twelve conversational questions (follow-ups replayed as multi-turn chains), against the submitted file (`e88ec139...`) directly through llama-server, and separately through the application.

### The model file directly

- **Repetition.** No repetition loops in 17 replayed prompts (context 8192, temperature 0.3), and none in a greedy stress test (temperature 0, context 2048, 900-token cap) over 16 prompts, all of which stopped normally. The earlier first-run weights with the same digest repeated a line up to 46 times on 2 of the 16 and hit the token cap on 3. This is one run per prompt, so it is a stress check and not a loop rate.
- **Wrong answers.** Payroll obligations were answered with withholding-tax rates (5% and 20%) instead of the PAYE bands, and no deadline. SHIF got an invented salary threshold. The sole-proprietor-to-company question got an invented iTax menu step. The business-registration prompt usually opened with a KRA PIN or NITA and not business-name registration, and named the Business Registration Service or eCitizen in only 1 of 3 runs. Kiswahili questions are covered in their own section.
- **Not reproducible at temperature 0.** The same file, prompt and setting gave a combined NSSF total of KES 3,600 in one run and KES 3,420 in another.

### The application

Through the application, several of these questions first failed when they fell through to free generation. The payroll question failed in 6 of 6 runs (3 through the application, 3 on the raw model) with invented thresholds and wrong remittance details. Two follow-ups ("Are those all the regulations for this category of business?" and "is there any software that will help make me compliant") returned answers about unrelated retrieved documents in 0 of 3 runs each. A barber question chain produced a wrong capital-gains claim and an invented URL.

I changed only `rag_server.py`. Payroll and employer-obligation phrasings now route to the verified employee-compliance answer. Follow-up questions ("those", "they", "this category") are searched together with the previous question. I added five verified answers, each written only from facts already in my verified entries. I added the 16% VAT rate to the verified VAT answers in both languages. The employee-compliance answer now says NSSF and PAYE are due by the 9th of the following month, the Housing Levy by the 9th working day after month end (KRA's own wording), and leaves the SHIF date to the Social Health Authority. It also says contracts and particulars must be kept for five years after employment ends, replacing an earlier line that wrongly called retention county-specific. After these changes the questions are answered from verified text with no model call, which I confirmed in the server log. This applies only when the application is used.

### How I chose the two test prompts

My first `tp_002` was "What are the basic steps to register a small business in Kenya?". The application answers it from a verified answer, but on the raw file it was unreliable, because the digest has no business-name registration facts: it named the Business Registration Service or eCitizen in only 1 of 3 runs, and two rewordings did no better (0 of 3 each). One rewording ("How can I register for my small business in Kenya") at temperature 0 made the model decline ("the material I have available doesn't contain specific registration requirements"), the same deferral I had worked to remove in the first training run.

I then tested nine candidate questions on the submitted file, four runs each (temperature 0, 0.3, 0.3 and 0.8). Eight gave the expected figure in all four runs. I kept the NSSF prompt and used "What is the VAT rate?". Looking more closely, both were weaker than the count suggested. On the NSSF prompt the per-side figure of KES 1,800 was correct in 9 of the 11 runs I could check, but the combined total, the tiers or the remittance details were wrong in many (remittance was usually given as the 9th working day via iTax, when NSSF is due by the 9th of the following month through its own portal). On the VAT prompt 16% appeared in all 17 runs across three tests, but the text around it often included wrong claims: "on all supplies and services", VAT "applied to gross income", and in one run invented food and education rates.

I then tested five candidates on both the model file and the application: annual leave, turnover tax rate, PAYE bands, VAT rate and the NSSF prompt (with a stricter check that also required the combined total of KES 3,600). Annual leave and turnover tax were clean in 4 of 4 raw runs and had a correct verified answer in the application. PAYE bands were clean in 2 of 4 raw runs, and the application did not use its verified answer because "PAYE tax bands" matched none of its keywords. VAT rate was clean in 1 of 4 raw runs and NSSF in 0 of 4. I ran the two clean ones eight more times each on the raw file (temperature 0 once, 0.3 four times, 0.8 three times) and read every answer.

- **Annual leave:** the figure of 21 working days was right in 8 of 8 runs, and 7 of 8 answers also contained a wrong or misleading statement. Examples are an invented accrual rule ("21.5 days" in the "21st month"), "63 working days" for three years of service, NSSF Tier I and Tier II figures inside a leave answer, and "regardless of length of service" (leave accrues after 12 months of service).
- **Turnover tax:** 1.5% of gross sales with no expense deductions was right in 8 of 8 runs, and 4 of 8 answers also contained a wrong or odd statement, such as a tax of KES 0.3 million on KES 2 million of sales (it should be KES 30,000) or PAYE and NSSF mixed into the answer. No run gave the eligibility range of KES 1,000,000 to 25,000,000.

I changed `tp_001` to "How many days of annual leave is an employee entitled to in Kenya?" and `tp_002` to "What is the turnover tax rate for small businesses in Kenya?". Both prompts were therefore chosen after testing candidates on the submitted file. They are topics the digest states and the application answers from a verified entry, so they show the file at its best. They do not show how it handles registration, payroll, SHIF or company-registration questions, which it answered wrongly or inconsistently in my tests. The two hidden prompts may fall in that area.


## Kiswahili

`metadata.json` lists Kiswahili in `language_scope`. Kiswahili support is partial, and it is different in the two parts of the system.

**Model file (temperature 0, context 2048, no application).** I asked eight Kiswahili questions (VAT rate, NSSF rate, business registration, Turnover Tax, VAT registration timing, first-employee obligations, SHIF, PAYE bands). Six of the eight came back in English, one was a two-token non-answer ("Kes 98,624.") and one was garbled Kiswahili with invented figures. Turnover Tax was right at 1.5%. The VAT answer gave 16% and the KES 5,000,000 threshold and then applied them to an invented turnover of KES 2.8 million, which contradicts the threshold. NSSF got an invented salary and tier boundary, SHIF got "KES 25,000 per month" instead of 2.75% of gross pay, and PAYE got a wrong description of the 25% band. The training data and retrieval corpus are English-only, and I could not source enough Kiswahili regulatory material to change that, so I do not claim the file answers Kiswahili questions reliably.

**Application.** All eight questions are answered from verified text with no model call: seven in Kiswahili and one (first-employee obligations) in English, because that verified answer has no Kiswahili version. Before the fixes, the VAT rate went to free generation with a wrong base ("16% of annual taxable income"), one question returned English because the language detector missed "lini" and "ninapaswa", and the first-employee question produced invented words. Three changes fixed those: the 16% rate in the verified VAT answers, more VAT-rate keywords, and a longer Kiswahili word list.

Language detection has had one more bug worth recording. The detector first matched short Swahili words as substrings, so "Kenya" (which contains "ya") counted as Kiswahili. That went unnoticed while detection was switched off, and once I turned it on it injected a "translate from Kiswahili" instruction into an English conversation. Word-boundary matching fixed it, and I widened the word list from 16 to 30 words and later added more.

An early attempt at Kiswahili generation, directly or by translating an English answer, produced repetitive and ungrammatical text whatever the settings, so the generative path stays English-only. The verified answers are fixed strings, so they carry no fluency risk.

**Status.** In the application, Kiswahili works for the verified topics, and the quality comes from those answers, not from the model. In the model file, Kiswahili is future work. I did not have time before the submission deadline to build a Kiswahili training set, retrain and verify a new file. A new model file changes its hash and means re-uploading it and updating the download script, provenance and benchmarks. I chose not to put the verified submission at risk. I list Kiswahili in `language_scope` for the application's support and describe its limits here so it is not read as a claim about the model file.

Next steps: build a Kiswahili training set from verified Kenyan sources with native-speaker review, retrain and test on Kiswahili questions including these eight, and add Kiswahili versions of the six English-only verified answers.

## Development Notes

### Fixes that break other answers

Improving a 1.5B model with a fact digest and fine-tuning was a trade-off exercise and took a large share of my time. A version that fixed one problem often introduced another, and a question one version answered correctly was answered wrongly by a later one. Measured examples, on the raw file:

- **A larger digest.** On the same v6 weights, digest v12 (which added SHIF, the Housing Levy, eTIMS and sole-proprietorship facts) fixed the SHIF answer (2.75% of gross pay, instead of an invented threshold). But the business-registration prompt started repeating the same line, the payroll answer contained invented arithmetic, an unrelated barber question was answered with rental-income tax rules, and SHIF was described as employer-matched, which my verified facts say is wrong. I kept digest v9.
- **Different weights.** Under greedy decoding, the setting the profiler's accuracy step uses, the first-run weights looped on 2 of 16 prompts and hit the token limit on 3; the submitted weights did neither. But on the registration prompt the first-run weights more often started with the business-name step: the opening step was something else in 3 of 20 runs, against 15 of 20 for the submitted weights. Neither set was better on every prompt. I submitted the second run for its stability.

Every candidate therefore needs a full re-test, and each new model file needs a new hash, a re-upload and a re-check of the whole download chain. That cost, and the deadline, is why I stopped at this version even though it still answers several questions wrongly.

Next: turn my test scripts (a 16-prompt greedy stress test and a figure-checking candidate test) into a regression suite that a new file must pass before it is published, add digest facts one topic at a time and re-run it after each, and improve the fine-tuning data, including Kiswahili, testing on held-out questions and not only on the ones I used while developing.

### Other engineering fixes

- **Keyword routing.** More specific topics have to be checked before general ones. Four cases were fixed by reordering: the generic `nssf` keyword taking NSSF-registration questions, the generic `loan` keyword taking Hustler Fund business questions, `leave` taking maternity-leave questions, and `license` taking food-business questions.
- **Fabricated details found in testing:** a made-up minimum share capital (my verified fact is that no minimum exists), a made-up program name for the Women Enterprise Fund, and the county-permit citation mentioned above. Each was replaced with a verified answer.
- **Outdated fact:** an employee-compliance answer named NHIF, which SHIF replaced in October 2024.
- **Duplicate entry:** a repeated `probation_period` entry in the Kiswahili answers (harmless, since Python used the later one).

## Limitations

- The model file answers several topics wrongly (payroll obligations, SHIF, company-registration steps, the Turnover Tax range) and often adds wrong details around correct figures. The verified answers and retrieval that fix most of these live in the optional application. A direct load of the file does not use them.
- Kiswahili works only through the application's verified answers. Six of them are English-only.
- Questions that match no verified topic go to the 1.5B model, which can produce inaccurate steps and can refer to "source material" the user never provided.
- Output at temperature 0 is not exactly reproducible on my setup.
- My accuracy figures for the application come from my own question sets, which I also used while fixing problems, so they are optimistic.
- Whether the thermal penalty applies depends on the evaluation hardware. On my laptop with default settings, the profiler reads 86-99 C and flags throttling.

## What I Learned

- **Test behaviour, not just loss.** A training loss of 1.39 looked fine, but the first model had learned to hedge and defer instead of answering. Only real questions showed that.
- **Fabrication is a system problem.** Stricter instructions reduced it and lower temperature did not. The only reliable fix for high-stakes facts was to take generation out of the loop for those questions.
- **Infrastructure bugs hide each other.** The PDF extraction problem masked everything after it, and a context-window crash meant my early accuracy numbers reflected a bug and not the model.
- **Check that a safeguard reaches what it protects.** I assumed the chat-template digest helped an accuracy step that never uses the template.
- **Test the path that gets evaluated.** The application fixed most of my test questions, but the profiler loads the file directly. Testing both, at the profiler's decoding settings, exposed failures the application had hidden.
- **Offline constraints help.** TF-IDF over embeddings, verified answers over generation and the quantization target all followed from the memory and connectivity limits, and they made the system simpler and clearer about what it can and cannot do.

## Performance Summary

| Metric | Result | Reference |
|---|---|---|
| Generation speed (profiler, CPU only) | 16-18 tokens/s in saved runs; latest three 17.65, 17.90, 17.91 | 15.0 |
| First-token latency (profiler, default settings) | about 3.6 s | none |
| Peak memory, model file (profiler) | about 1,695 MB (about 76% efficiency) | 7 GB limit |
| Memory, full application | about 3.3 GB | 7 GB limit |
| Model file | 986,062,592 bytes (about 940 MiB) | none |
| Parameters | 1,543,714,304 | 1.5B declared |
| CPU temperature, default settings | 86-98 C in three runs, flagged throttled | 85 C |
| CPU temperature, turbo boost disabled | 59-61 C, not throttled (a setting the evaluation does not apply) | 85 C |
| Annual leave test prompt (`tp_001`), 21 days, model file | figure right in 8 of 8 runs; wrong or misleading detail in 7 of 8 | none |
| Turnover tax test prompt (`tp_002`), 1.5%, model file | figure right in 8 of 8 runs; wrong or odd detail in 4 of 8 | none |
| Verified answers in the application | more than 40 topics, most in English and Kiswahili | none |
| Retrieval corpus | 18,307 chunks from 323 documents; 15,775 in the current index | none |
| Self-measured accuracy, application, 30-question set | 92-97.3%, not a measure of the model file | none |

## Repository Organization

`rag_server.py`, `build_index.py` and `start.sh` are the application. `metadata.json`, `download_model.sh` and this report are the submission files. `provenance/` holds the training evidence for the submitted weights (with the first run in `original-run/`), and `future-training-data/` holds the dataset and its generation scripts. The `dev-tools/` folder contains the patch scripts behind each fix in this report, roughly in the order I wrote them, and the `benchmark-evidence/` folder holds raw profiler output referenced above, so each fix can be inspected and not only described.
