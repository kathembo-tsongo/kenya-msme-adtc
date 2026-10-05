"""Pull the phone's test log (files/rafiki_log.jsonl) and turn it into a CSV.

Run from the kenya-msme-adtc folder, with the phone connected:
    python3 pull_phone_log.py            # saves phone_logs/rafiki_log_<date-time>.jsonl and .csv, prints a summary
    python3 pull_phone_log.py --clear    # same, then empties the log on the phone (start a fresh test session)
    python3 pull_phone_log.py --file ~/Downloads/rafiki_log_P01_20261105-1400.txt
                                         # convert a log an operator exported from the app (WhatsApp, Bluetooth ...)
phone_logs/ holds test data: keep it out of git (it is added to .gitignore here if missing).
"""
import argparse
import csv
import datetime as dt
import json
import os
import subprocess
from collections import Counter

PKG = "com.example.llama.aichat"
REMOTE = "files/rafiki_log.jsonl"
FIELDS = ["time", "participant", "question", "lang", "route", "topic", "suggest", "confidence", "sources",
          "model", "ms", "pack", "app", "answer"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clear", action="store_true", help="empty the phone's log after pulling")
    ap.add_argument("--file", help="convert an exported log file instead of pulling over adb")
    args = ap.parse_args()

    if args.file:
        text = open(os.path.expanduser(args.file), encoding="utf-8", errors="replace").read()
        args.clear = False
    else:
        raw = subprocess.run(["adb", "exec-out", "run-as", PKG, "cat", REMOTE], capture_output=True)
        text = raw.stdout.decode("utf-8", errors="replace")
        if raw.returncode != 0 or "No such file" in text:
            print("No log on the phone yet (ask a question in the app first), or the phone isn't connected.")
            return
    rows = [json.loads(l) for l in text.splitlines() if l.strip().startswith("{")]
    if not rows:
        print("The log is empty.")
        return

    os.makedirs("phone_logs", exist_ok=True)
    gi = open(".gitignore").read() if os.path.exists(".gitignore") else ""
    if "phone_logs/" not in gi:
        open(".gitignore", "a").write("\nphone_logs/\n")
        print("Added phone_logs/ to .gitignore")
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M")
    base = (f"phone_logs/{os.path.splitext(os.path.basename(args.file))[0]}" if args.file
            else f"phone_logs/rafiki_log_{stamp}")
    open(base + ".jsonl", "w", encoding="utf-8").write(text)
    with open(base + ".csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(f"{len(rows)} questions -> {base}.csv")
    print("Routes:   " + ", ".join(f"{k} {v}" for k, v in Counter(r.get("route", "?") for r in rows).most_common()))
    print("Language: " + ", ".join(f"{k} {v}" for k, v in Counter(r.get("lang", "?") for r in rows).most_common()))
    model = [r["ms"] for r in rows if r.get("model") == "yes"]
    instant = [r["ms"] for r in rows if r.get("model") != "yes"]
    if model:
        model.sort()
        print(f"Model answers: {len(model)}, median {model[len(model)//2]/1000:.1f} s, slowest {model[-1]/1000:.1f} s")
    if instant:
        instant.sort()
        print(f"Instant answers: {len(instant)}, median {instant[len(instant)//2]} ms")

    if args.clear:
        subprocess.run(["adb", "shell", "run-as", PKG, "rm", REMOTE])
        print("Cleared the log on the phone.")


if __name__ == "__main__":
    main()
