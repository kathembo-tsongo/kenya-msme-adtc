#!/usr/bin/env python3
"""
make_eval_assets.py -- write the phone's evaluation question list (assets/eval_questions.tsv)
from eval/test_set.csv: one line per question, "id<TAB>lang<TAB>question", English then Kiswahili.

    python3 eval/make_eval_assets.py
    python3 eval/make_eval_assets.py --app ../rafiki-wa-biashara-mobile/llama.cpp/examples/llama.android/app

Only test-set questions go into the app (no participant data). Rebuild and install the app afterwards.
"""
import argparse
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "..", "..", "rafiki-wa-biashara-mobile", "llama.cpp", "examples", "llama.android", "app")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tests", default=os.path.join(HERE, "test_set.csv"))
    ap.add_argument("--app", default=APP, help="the Android app folder (contains src/main/assets)")
    a = ap.parse_args()
    out = os.path.join(a.app, "src", "main", "assets", "eval_questions.tsv")
    if not os.path.isdir(os.path.dirname(out)):
        raise SystemExit(f"Not found: {os.path.dirname(out)} -- pass --app with the app folder.")
    n = 0
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("id\tlang\tquestion\n")
        for row in csv.DictReader(open(a.tests, encoding="utf-8")):
            for lang in ("en", "sw"):
                q = " ".join(row[f"question_{lang}"].split())
                if q:
                    f.write(f"{row['id']}\t{lang}\t{q}\n")
                    n += 1
    print(f"Wrote {n} questions to {os.path.normpath(out)}")


if __name__ == "__main__":
    main()
