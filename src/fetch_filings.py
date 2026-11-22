"""Download the most recent 10-K for each company from SEC EDGAR and record provenance.

Writes data/raw/<TICKER>.htm (git-ignored) and data/filings.csv (committed).
Re-running verifies the SHA-256 of an existing download against filings.csv.
"""
import csv
import hashlib
import sys
import time

import requests

from config import COMPANIES, DATA, RAW, SEC_USER_AGENT

HEAD = {"User-Agent": SEC_USER_AGENT, "Accept-Encoding": "gzip, deflate"}
FIELDS = ["company", "ticker", "cik", "form", "accession", "filing_date",
          "fiscal_year_end", "url", "index_url", "sha256", "bytes"]


def latest_10k(cik):
    r = requests.get(f"https://data.sec.gov/submissions/CIK{cik}.json", headers=HEAD, timeout=30)
    r.raise_for_status()
    rec = r.json()["filings"]["recent"]
    for i, form in enumerate(rec["form"]):
        if form == "10-K":
            return {k: rec[k][i] for k in ("accessionNumber", "filingDate", "reportDate", "primaryDocument")}
    raise RuntimeError(f"no 10-K for {cik}")


def main(only=None):
    RAW.mkdir(parents=True, exist_ok=True)
    out = DATA / "filings.csv"
    existing = {}
    if out.exists():
        existing = {r["ticker"]: r for r in csv.DictReader(out.open())}
    rows = []
    for name, (ticker, cik) in COMPANIES.items():
        if only and ticker not in only:
            if ticker in existing:
                rows.append(existing[ticker])
            continue
        f = latest_10k(cik)
        acc = f["accessionNumber"]
        cik_int = str(int(cik))
        folder = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc.replace('-', '')}"
        url = f"{folder}/{f['primaryDocument']}"
        path = RAW / f"{ticker}.htm"
        if not path.exists():
            time.sleep(0.5)  # SEC fair-access: stay well under 10 req/s
            r = requests.get(url, headers=HEAD, timeout=60)
            r.raise_for_status()
            path.write_bytes(r.content)
        blob = path.read_bytes()
        sha = hashlib.sha256(blob).hexdigest()
        if ticker in existing and existing[ticker]["sha256"] != sha:
            sys.exit(f"SHA mismatch for {ticker}: filing changed or download corrupted")
        rows.append({
            "company": name, "ticker": ticker, "cik": cik, "form": "10-K", "accession": acc,
            "filing_date": f["filingDate"], "fiscal_year_end": f["reportDate"], "url": url,
            "index_url": f"{folder}/{acc}-index.htm", "sha256": sha, "bytes": len(blob),
        })
        print(f"{ticker}: {f['filingDate']} FYE {f['reportDate']} {len(blob):,} bytes")
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
