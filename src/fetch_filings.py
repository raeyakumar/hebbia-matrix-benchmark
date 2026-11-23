"""Download the exact 10-Ks used in the study from SEC EDGAR and verify their content.

The documents are pinned by the URLs in data/filings.csv, which is frozen and only read here.
SEC's server adds one script tag, with a changing address, just before </body>. The check removes
that tag (and nothing else) and compares the SHA-256 of the remaining bytes with
data/filings_content_sha256.csv, so any change to the filing itself is still rejected.

Usage: python fetch_filings.py [TICKER ...]
       python fetch_filings.py --write-baseline   (only from files that match filings.csv exactly)
"""
import csv
import hashlib
import re
import sys
import time

import requests

from config import DATA, RAW, SEC_USER_AGENT

HEAD = {"User-Agent": SEC_USER_AGENT, "Accept-Encoding": "gzip, deflate"}
FILINGS = DATA / "filings.csv"
BASELINE = DATA / "filings_content_sha256.csv"

# Only an empty, same-site script that is the last thing before the closing tags.
SEC_SCRIPT_RE = re.compile(
    rb'<script type="text/javascript" +src="/[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*"></script>'
    rb'(?=</body>\s*</html>\s*\Z)')


def content_sha256(blob):
    """SHA-256 of the filing with SEC's trailing script tag (at most one) removed."""
    return hashlib.sha256(SEC_SCRIPT_RE.sub(b"", blob, count=1)).hexdigest()


def read_filings():
    with FILINGS.open() as fh:
        return list(csv.DictReader(fh))


def read_baseline():
    with BASELINE.open() as fh:
        return {r["ticker"]: r["content_sha256"] for r in csv.DictReader(fh)}


def write_baseline():
    rows = []
    for r in read_filings():
        blob = (RAW / f"{r['ticker']}.htm").read_bytes()
        if hashlib.sha256(blob).hexdigest() != r["sha256"]:
            sys.exit(f"{r['ticker']}: not the original download; baseline not written")
        if len(SEC_SCRIPT_RE.findall(blob)) != 1:
            sys.exit(f"{r['ticker']}: expected exactly one SEC script tag; baseline not written")
        rows.append({"ticker": r["ticker"], "content_sha256": content_sha256(blob)})
    with BASELINE.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["ticker", "content_sha256"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main(only=None):
    baseline = read_baseline()
    filings = [r for r in read_filings() if not only or r["ticker"] in only]
    if not filings or (only and only - {r["ticker"] for r in filings}):
        sys.exit("unknown ticker")
    for r in filings:
        ticker, path = r["ticker"], RAW / f"{r['ticker']}.htm"
        fresh = not path.exists()
        if fresh:
            time.sleep(0.5)  # SEC fair access
            resp = requests.get(r["url"], headers=HEAD, timeout=60)
            resp.raise_for_status()
            blob = resp.content
        else:
            blob = path.read_bytes()
        if content_sha256(blob) != baseline[ticker]:
            sys.exit(f"{ticker}: CONTENT MISMATCH - the filing differs from the one used in the study"
                     + (" (download not saved)" if fresh else f" ({path})"))
        if fresh:
            RAW.mkdir(parents=True, exist_ok=True)
            path.write_bytes(blob)
        exact = hashlib.sha256(blob).hexdigest() == r["sha256"]
        print(f"{ticker}: content verified ({'identical bytes' if exact else 'only the SEC script tag differs'})")


if __name__ == "__main__":
    args = set(sys.argv[1:])
    write_baseline() if args == {"--write-baseline"} else main(args or None)
