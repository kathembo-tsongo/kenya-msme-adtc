
import subprocess, sys, time, argparse
from pathlib import Path

SCRAPERS = [
    {"kb":1,"script":"scrape_kb1_legal_regulatory.py","label":"Legal & Regulatory"},
    {"kb":2,"script":"scrape_kb2_tax_kra.py","label":"Tax & KRA"},
    {"kb":3,"script":"scrape_kb3_financing_credit.py","label":"Financing & Credit"},
    {"kb":4,"script":"scrape_kb4_social_security.py","label":"Social Security"},
    {"kb":5,"script":"scrape_kb5_digital_trade.py","label":"Digital & Trade"},
    {"kb":6,"script":"scrape_kb6_county_geospatial.py","label":"County & Geospatial"},
    {"kb":7,"script":"scrape_kb7_culture_context.py","label":"Culture & Context"},
    {"kb":8,"script":"scrape_kb8_national_policy_strategy.py","label":"National Policy & Strategy"},
]
KB_DIRS = {1:"documents/kb1_legal_regulatory",2:"documents/kb2_tax_kra",3:"documents/kb3_financing_credit",4:"documents/kb4_social_security",5:"documents/kb5_digital_trade",6:"documents/kb6_county_geospatial",7:"documents/kb7_culture_context",8:"documents/kb8_national_policy_strategy"}

def count_files(n):
    d = Path(KB_DIRS[n])
    if not d.exists(): return 0,0
    return len(list(d.glob("*.txt"))),len(list(d.glob("*.pdf")))

def run(s,dry=False):
    kb,script,label = s["kb"],s["script"],s["label"]
    print(f"\n{'='*50}\n  KB{kb} - {label}\n{'='*50}")
    if dry: print(f"  [DRY] {script}"); return True
    if not Path(script).exists(): print(f"  [ERR] Not found: {script}"); return False
    t = time.time()
    r = subprocess.run([sys.executable,script])
    txt,pdf = count_files(kb)
    print(f"  {'OK' if r.returncode==0 else 'FAILED'} | {txt} txt {pdf} pdf | {time.time()-t:.0f}s")
    return r.returncode==0

if __name__=="__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--kb",nargs="*",type=int)
    p.add_argument("--dry-run",action="store_true")
    a = p.parse_args()
    sel = [s for s in SCRAPERS if a.kb is None or s["kb"] in a.kb]
    print(f"\nKenya MSME Advisor - Running {len(sel)} scrapers")
    results = [run(s,dry=a.dry_run) for s in sel]
    if not a.dry_run:
        print("\n--- FINAL REPORT ---")
        for s in SCRAPERS:
            t,p2 = count_files(s["kb"])
            print(f"  KB{s['kb']} {s['label']:<30} {t:>3} txt {p2:>3} pdf")
    failed = [s for s,ok in zip(sel,results) if not ok]
    if failed: [print(f"  FAILED: KB{s['kb']}") for s in failed]; sys.exit(1)
    else: print("  All scrapers completed.")
