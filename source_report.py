"""List verified answers by provenance: no source recorded, or checked too long ago.

Run from the kenya-msme-adtc folder:
    python3 source_report.py                       # uses rafiki_pack.db, flags checks older than 180 days
    python3 source_report.py --db rafiki_pack_new.db --max-age 90
"""
import argparse
import datetime as dt
import sqlite3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="rafiki_pack.db")
    ap.add_argument("--max-age", type=int, default=180, help="days after which a check counts as overdue")
    args = ap.parse_args()

    db = sqlite3.connect(args.db)
    topics = [t for (t,) in db.execute("SELECT topic FROM canned ORDER BY topic")]
    try:
        src = {t: (s, u, c) for t, s, u, c in db.execute("SELECT topic, source, url, checked FROM canned_sources")}
    except sqlite3.OperationalError:
        print(f"{args.db} has no canned_sources table -- rebuild the pack with the patched build_pack.py.")
        return

    today = dt.date.today()
    sourced, overdue, missing = [], [], []
    for t in topics:
        if t not in src:
            missing.append(t)
            continue
        name, url, checked = src[t]
        age = (today - dt.date.fromisoformat(checked)).days
        (overdue if age > args.max_age else sourced).append((t, name, checked, age))
    orphans = sorted(set(src) - set(topics))

    print(f"Verified answers: {len(topics)}  |  sourced and current: {len(sourced)}  |  "
          f"overdue (> {args.max_age} days): {len(overdue)}  |  no source: {len(missing)}\n")
    if overdue:
        print("OVERDUE -- recheck against the source:")
        for t, name, checked, age in sorted(overdue, key=lambda x: -x[3]):
            print(f"  {t:32} {name:40} checked {checked} ({age} days ago)")
        print()
    if missing:
        print("NO SOURCE -- find an official source, or remove the figures:")
        for t in missing:
            print(f"  {t}")
        print()
    if orphans:
        print("SOURCE WITHOUT ANSWER -- topic renamed or removed? Fix CANNED_SOURCES:")
        for t in orphans:
            print(f"  {t}")


if __name__ == "__main__":
    main()
