# Dataset information

## Used for the submitted weights (v6 run, 430 steps)
- **Name:** training_data_v5.jsonl (stored at `future-training-data/training_data_v5.jsonl`; the folder name is historical -- this is the dataset the submitted weights were trained on)
- **Source:** synthetic conversational question-answer examples about Kenyan MSME tax, registration, financing and social security, produced from verified Kenyan regulatory and financing documents; generation scripts are in `future-training-data/generation-scripts/`
- **Records:** 3610
- **sha256:** 3b88c7819410b1e6ddca771f4c0c43497450999fdc7b2acbaa0d2925e09840a2

## Used for the earlier first run (not the submitted weights)
- **Name:** training_data_v4_merged.jsonl (`provenance/original-run/`)
- **Records:** 3308
- **sha256:** f238a4290e0d5a173147c20a52a503cd718149489693c995c245ec99bde016b8

## Adapters
- Submitted (fp32, checkpoint-430): `provenance/adapter_model.safetensors`, sha256 0bf2d91bcf34099c02bc68e46ad60e19d6789f02f2464e59e66ec7b7f7407bb1
- First run (fp16): `provenance/original-run/adapter_model.safetensors`, sha256 962a625b15ef4a7b8c67a38982dcb395b065b87cba1604170597a751704ec623
