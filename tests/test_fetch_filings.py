"""Offline tests of the SEC download check (no network; files are written to a temp folder).

Run: .venv/bin/python tests/test_fetch_filings.py
The real-filing cases need data/raw/ (run src/fetch_filings.py first) and are skipped without it.
"""
import csv
import hashlib
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import fetch_filings as f  # noqa: E402

TAG = b'<script type="text/javascript"  src="/AbC/d-1/e_2"></script>'
NEW = b'<script type="text/javascript"  src="/zz9/Y/x"></script>'
PAGE = (b"<html><body><table><tr><td>Total net sales</td><td>478,834</td></tr></table>" + TAG + b"</body></html>\n")


def variants(page, old_tag, number, changed):
    """(name, bytes, should_be_accepted)"""
    yield "unchanged", page, True
    yield "script address changed", page.replace(old_tag, NEW), True
    yield "script tag absent", page.replace(old_tag, b""), True
    assert page.count(number) >= 1
    yield "table number changed", page.replace(number, changed, 1), False
    yield "table number and script changed", page.replace(number, changed, 1).replace(old_tag, NEW), False
    yield "text added inside the script", page.replace(old_tag, NEW.replace(b"></", b">var x=1</")), False
    yield "script from another site", page.replace(old_tag, NEW.replace(b'"/zz9', b'"//evil.example')), False
    yield "script with extra attribute", page.replace(old_tag, NEW.replace(b' src', b' id="a" src')), False
    yield "second script added", page.replace(old_tag, NEW + NEW), False
    yield "script moved into the filing", page.replace(old_tag, b"").replace(b"<body", NEW + b"<body", 1), False
    yield "text added at the end", page.replace(b"</body>", b"<p>x</p></body>"), False
    yield "content after closing tag", page + b"<p>x</p>", False
    yield "truncated", page[:len(page) // 2], False
    yield "one space added", page.replace(number, number + b" ", 1), False


def check(label, page, tag, number, changed):
    base = f.content_sha256(page)
    for name, blob, ok in variants(page, tag, number, changed):
        assert (f.content_sha256(blob) == base) is ok, (label, name)


def test_synthetic():
    check("synthetic", PAGE, TAG, b"478,834", b"478,835")


def test_every_real_filing():
    # a figure from a financial table in each filing (total assets)
    nums = {"AAPL": b"404,548", "MSFT": b"758,376", "GOOGL": b"595,281", "META": b"366,021", "AMZN": b"818,042"}
    base, n = f.read_baseline(), 0
    for t, num in nums.items():
        p = f.RAW / f"{t}.htm"
        if not p.exists():
            continue
        page = p.read_bytes()
        assert f.content_sha256(page) == base[t]
        check(t, page, f.SEC_SCRIPT_RE.search(page).group(0), num, num[:-1] + (b"0" if num[-1:] != b"0" else b"1"))
        n += 1
    print(f"real filings tested: {n}")


def test_command_end_to_end():
    """main(): accepts and saves a script-only change; rejects and does not save a changed table number."""
    class Resp:
        def __init__(self, c): self.content = c
        def raise_for_status(self): pass
    saved = (f.RAW, f.FILINGS, f.BASELINE, f.requests.get)
    try:
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            f.RAW, f.FILINGS, f.BASELINE = d / "raw", d / "filings.csv", d / "base.csv"
            with f.FILINGS.open("w", newline="") as fh:
                w = csv.writer(fh)
                w.writerows([["ticker", "url", "sha256"], ["T", "https://pinned.example/t.htm", hashlib.sha256(PAGE).hexdigest()]])
            f.BASELINE.write_text(f"ticker,content_sha256\nT,{f.content_sha256(PAGE)}\n")
            before = f.FILINGS.read_bytes()

            def serve(blob):
                def get(url, **kw):
                    assert url == "https://pinned.example/t.htm"
                    return Resp(blob)
                f.requests.get = get

            def rejected():
                try:
                    f.main()
                except SystemExit as e:
                    assert "CONTENT MISMATCH" in str(e)
                    return True
                return False

            bad = PAGE.replace(b"478,834", b"478,835").replace(TAG, NEW)
            serve(bad)
            assert rejected() and not (f.RAW / "T.htm").exists()
            serve(PAGE.replace(TAG, NEW))
            f.main()
            assert (f.RAW / "T.htm").exists()
            (f.RAW / "T.htm").write_bytes(bad)   # a saved file that was later altered
            assert rejected()
            assert f.FILINGS.read_bytes() == before
    finally:
        f.RAW, f.FILINGS, f.BASELINE, f.requests.get = saved


if __name__ == "__main__":
    test_synthetic()
    test_every_real_filing()
    test_command_end_to_end()
    print("all download-check tests passed")
