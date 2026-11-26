#!/usr/bin/env python3
"""
pull_phone_eval.py -- copy the phone's evaluation run (files/rafiki_eval.jsonl) to eval/phone_runs/.

    python3 eval/pull_phone_eval.py                                  # over adb (phone connected)
    python3 eval/pull_phone_eval.py --file ~/Downloads/rafiki_eval_<run>.txt   # a run exported from the app

Then score it:  python3 eval/score_phone_eval.py eval/phone_runs/<file>.jsonl
"""
import argparse
import json
import os
import subprocess

PKG = "com.example.llama.aichat"
REMOTE = "files/rafiki_eval.jsonl"
HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="an exported run instead of adb")
    a = ap.parse_args()
    if a.file:
        text = open(os.path.expanduser(a.file), encoding="utf-8", errors="replace").read()
    else:
        raw = subprocess.run(["adb", "exec-out", "run-as", PKG, "cat", REMOTE], capture_output=True)
        text = raw.stdout.decode("utf-8", errors="replace")
        if raw.returncode != 0 or "No such file" in text:
            raise SystemExit("No evaluation run on the phone yet, or the phone isn't connected.")
    rows = [json.loads(l) for l in text.splitlines() if l.strip().startswith("{")]
    if not rows:
        raise SystemExit("The run is empty.")
    run = rows[0].get("run", "run")
    os.makedirs(os.path.join(HERE, "phone_runs"), exist_ok=True)
    out = os.path.join(HERE, "phone_runs", f"rafiki_eval_{run}.jsonl")
    open(out, "w", encoding="utf-8").write(text)
    passes = sorted({r.get("pass") for r in rows})
    print(f"{len(rows)} answers, passes {passes}, device {rows[0].get('device', '?')} -> {os.path.relpath(out)}")
    print(f"Score it:  python3 eval/score_phone_eval.py {os.path.relpath(out)}")


if __name__ == "__main__":
    main()
