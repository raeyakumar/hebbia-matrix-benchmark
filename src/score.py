"""Score a run directory: normalize answers, check citations, build paired results.

Three separate checks per (method, question, company) row:
  correct     - answer matches the answer key (value converted to base units, or a
                correct abstention when the key says the evidence is insufficient)
  quote_ok    - the quote appears verbatim (whitespace/case-normalized) in the cited excerpt.
                This ONLY says the text exists; it says nothing about support.
  support_ok  - the quote actually supports the claim: cited excerpt belongs to the row's
                company, the claimed value (in the claimed unit) appears in the quote at the
                excerpt's scale, and the period is consistent (table column mapped to its
                year header, or the year stated in a prose quote). 'unclear' when the period
                cannot be checked automatically -> listed for human review.
  verified    - correct AND quote_ok AND support_ok   (for correct abstentions: verified = correct)

Usage: python score.py results/pilot [--key benchmark/answer_key_practice.csv]
"""
import argparse
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict

from config import BENCH, COMPANIES, ROOT, TICKER_TO_NAME

NUM_RE = re.compile(r"\(?-?\$?\s?(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\)?\s*(%|percent|thousand|million|billion|trillion)?", re.I)
SCALE_WORDS = {"thousand": 1e3, "thousands": 1e3, "million": 1e6, "millions": 1e6, "billion": 1e9,
               "billions": 1e9, "trillion": 1e12, "trillions": 1e12}
UNIT_LINE_RE = re.compile(r"\((?:in|dollars in|amounts in)\s+(thousands|millions|billions)", re.I)
YEAR_RE = re.compile(r"\b(20\d\d)\b")


def norm(s):
    s = unicodedata.normalize("NFKC", s or "")
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("—", "-").replace("–", "-").replace("\xa0", " ")
    s = re.sub(r"\s*\|\s*", " | ", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def unit_scale(unit):
    """('percent'|'amount', multiplier) from a unit string like 'USD millions'."""
    u = (unit or "").lower()
    if "percent" in u or "%" in u:
        return "percent", 1.0
    for w, m in SCALE_WORDS.items():
        if re.search(rf"\b{w}\b", u):
            return "amount", m
    return "amount", 1.0


def base_value(value, unit):
    """Magnitude in base units. Signs are dropped: no expected answer in this benchmark is negative,
    and filings show outflows such as capex in parentheses."""
    if value is None:
        return None
    kind, m = unit_scale(unit)
    return kind, abs(float(value)) * m


def close(a, b, tol):
    if a is None or b is None:
        return False
    if b == 0:
        return abs(a) < 1e-9
    return abs(a - b) <= tol * abs(b)


def company_to_ticker(name):
    n = (name or "").lower()
    for comp, (t, _) in COMPANIES.items():
        if comp.lower() in n or t.lower() == n.strip():
            return t
    if "google" in n:
        return "GOOGL"
    return None


# ---------- support checks ----------

def numbers_in(text):
    out = []
    for m in NUM_RE.finditer(text):
        raw = m.group(1).replace(",", "")
        try:
            v = float(raw)
        except ValueError:
            continue
        out.append((v, (m.group(2) or "").lower(), m.start()))
    return out


def chunk_scales(chunk_text):
    """All scales named in the excerpt's unit lines, e.g. Apple's '(In millions, except number of
    shares, which are reflected in thousands...)' -> {1e6, 1e3}."""
    scales = set()
    for line in chunk_text.split("\n"):
        if UNIT_LINE_RE.search(line):
            for w in re.findall(r"thousands|millions|billions", line, re.I):
                scales.add(SCALE_WORDS[w.lower()])
    return scales


ZERO_RE = re.compile(r"\b(no|none|not any|zero|nil)\b.{0,80}\b(borrow|repurchas|amounts?|outstanding)"
                     r"|\b(borrow|repurchas)\w*.{0,40}\b(none|zero|nil)\b", re.I)


def value_in_quote(quote, chunk_text, claim_kind, claim_base, tol):
    cscales = sorted(chunk_scales(chunk_text))
    if claim_kind == "amount" and claim_base == 0:
        return [(0.0, 0)] if ZERO_RE.search(quote) else []
    hits = []
    for v, word, start in numbers_in(quote):
        if claim_kind == "percent":
            if close(v, claim_base, tol):
                hits.append((v, start))
            continue
        scales = [SCALE_WORDS[word]] if word in SCALE_WORDS else cscales + [1.0]
        if any(close(v * s, claim_base, tol) for s in scales):
            hits.append((v, start))
    return hits


def derived_from_excerpt(chunk_text, claim_base, tol):
    """True if the claim equals the sum of two amounts stated in the excerpt (e.g. $14.0B + $100B)."""
    vals = []
    for v, word, _ in numbers_in(chunk_text):
        if word in SCALE_WORDS:
            vals.append(v * SCALE_WORDS[word])
    vals = sorted(set(vals))
    return any(close(a + b, claim_base, tol) for i, a in enumerate(vals) for b in vals[i + 1:])


def period_check(quote, chunk_text, hit_value, expected_year):
    """'ok' / 'wrong' / 'unclear'. Table rows: map the cell to its year column."""
    if not expected_year:
        return "unclear"
    nq = norm(quote)
    if " | " in nq:
        lines = [norm(l) for l in chunk_text.split("\n")]
        row_idx = next((i for i, l in enumerate(lines) if nq in l or l in nq and len(l) > 10), None)
        cells = [c for c in nq.split(" | ")[1:]]
        num_cells = [c for c in cells if re.search(r"\d", c) and not c.endswith("%")]
        if row_idx is not None:
            for j in range(row_idx - 1, max(row_idx - 40, -1), -1):
                years = YEAR_RE.findall(lines[j])
                if len(years) >= 2 and len(lines[j]) < 120:  # long rows that merely mention years are not headers
                    # drop duplicate year mentions from long date headers ("Sept 26, 2026 | Sept 27, 2025")
                    if len(years) == len(num_cells):
                        for c, y in zip(num_cells, years):
                            if numbers_in(c) and abs(numbers_in(c)[0][0] - hit_value) < 1e-6:
                                return "ok" if y == expected_year else "wrong"
                    break
            # columns are not years (e.g. share classes): use a single-year label above the row
            for j in range(row_idx - 1, max(row_idx - 40, -1), -1):
                years = set(YEAR_RE.findall(lines[j]))
                if len(years) == 1 and " | " not in lines[j]:
                    return "ok" if expected_year in years else "wrong"
                if len(years) >= 2:
                    break
        qy = set(YEAR_RE.findall(nq))
        if qy:  # a labeled row such as "... as of June 30, 2025 | $2,118,061,430,046"
            return "ok" if expected_year in qy else "wrong"
        return "unclear"
    years = YEAR_RE.findall(quote)
    if expected_year in years:
        return "ok"
    if years:
        return "wrong" if expected_year not in years else "ok"
    return "unclear"


# ---------- main ----------

def load_key(path):
    key = {}
    for r in csv.DictReader(open(path)):
        key[(r["question_id"], r["ticker"])] = r
    return key


def load_evidence(qid):
    ev = json.load((BENCH / "evidence" / f"{qid}.json").open())
    return {c["id"]: c for cs in ev["companies"].values() for c in cs}, ev


def latest_calls(run_dir):
    calls, all_calls = {}, []
    for l in open(run_dir / "calls.jsonl"):
        r = json.loads(l)
        all_calls.append(r)
        calls[(r["method"], r["question_id"], ",".join(r["tickers"]))] = r
    return calls, all_calls


def score_row(method, qid, ticker, row, call, key_row, ev_chunks, overrides):
    k = key_row
    tol = float(k.get("tolerance_rel") or 0.001)
    expect_abstain = k["expect_abstain"].strip().lower() in {"1", "true", "yes"}
    out = {"method": method, "question_id": qid, "ticker": ticker, "company": TICKER_TO_NAME[ticker],
           "call_error": call.get("error") or "", "status": "", "answer": "", "value": "", "unit": "",
           "period": "", "excerpt_id": "", "quote": "",
           "expected_answer": k["expected_answer"], "expect_abstain": expect_abstain}
    if call.get("error") or row is None:
        out.update(status="error" if call.get("error") else "missing_row", correct=False, quote_ok=False,
                   support="n/a", support_ok=False, verified=False, abstained=False, needs_human="")
        return out
    out.update({f: row.get(f) if row.get(f) is not None else "" for f in
                ("status", "answer", "value", "unit", "period", "excerpt_id", "quote")})
    abstained = row.get("status") == "insufficient_evidence" or row.get("value") is None
    out["abstained"] = abstained

    # correctness
    if expect_abstain:
        correct = abstained
    elif abstained:
        correct = False
    else:
        claim = base_value(row["value"], row.get("unit"))
        accepted = [(k["expected_value"], k["unit"])] + [
            tuple(a.split("@")) for a in (k.get("accepted_alternates") or "").split(";") if "@" in a]
        correct = any(claim and claim[0] == unit_scale(u)[0] and close(claim[1], base_value(float(v), u)[1], tol)
                      for v, u in accepted if v not in ("", None))
    out["correct"] = correct

    # quote + support
    if abstained:
        out.update(quote_ok="", support="n/a", support_ok=False, verified=correct and abstained, needs_human="")
        return out
    cid = row.get("excerpt_id", "")
    chunk = ev_chunks.get(cid)
    quote = row.get("quote") or ""
    out["quote_ok"] = bool(chunk) and len(norm(quote)) >= 8 and norm(quote) in norm(chunk["text"])
    out["quote_in_other_excerpt"] = (not out["quote_ok"]) and any(
        norm(quote) in norm(c["text"]) for c in ev_chunks.values()) if quote else False
    reasons = []
    company_ok = bool(chunk) and chunk["ticker"] == ticker
    if not company_ok:
        reasons.append("cited excerpt not this company's" if chunk else "cited excerpt id not in evidence")
    claim = base_value(row["value"], row.get("unit"))
    hits = value_in_quote(quote, chunk["text"], claim[0], claim[1], tol) if (chunk and out["quote_ok"]) else []
    neighbor_unit = False
    if out["quote_ok"] and not hits and chunk:
        # unit line may sit in an earlier excerpt of the same section that the model also received
        same = sorted(cid2 for cid2, c2 in ev_chunks.items()
                      if c2["ticker"] == ticker and c2["heading"] == chunk["heading"] and cid2 < cid)
        ctx = "\n".join(ev_chunks[c2]["text"] for c2 in same[-4:])
        if ctx and value_in_quote(quote, ctx + "\n" + chunk["text"], claim[0], claim[1], tol):
            neighbor_unit = True
    derived = bool(out["quote_ok"] and not hits and chunk and derived_from_excerpt(chunk["text"], claim[1], tol))
    if neighbor_unit:
        reasons.append("unit stated only in an earlier excerpt of the same section (needs human check)")
    elif out["quote_ok"] and not hits:
        reasons.append("claimed value is a sum of excerpt figures (needs human check)" if derived
                       else "claimed value/unit not in quote")
    period = "n/a"
    if out["quote_ok"] and hits:
        period = period_check(quote, chunk["text"], hits[0][0], k.get("period_year", "").strip())
        if period == "wrong":
            reasons.append("quote's value is for a different period")
    if not out["quote_ok"]:
        support = "fail"
        reasons.insert(0, "quote not verbatim in cited excerpt")
    elif (derived or neighbor_unit) and company_ok:
        support = "unclear"
    elif not company_ok or not hits or period == "wrong":
        support = "fail"
    elif period == "unclear":
        support = "unclear"
    else:
        support = "pass"
    ov = overrides.get((method, qid, ticker))
    if ov and support == "unclear":
        support = ov["support"]
        reasons.append(f"human override: {ov.get('note', '')}")
    out["period_check"] = period
    out["support"] = support
    out["support_ok"] = support == "pass"
    out["support_reasons"] = "; ".join(reasons)
    out["needs_human"] = "yes" if support == "unclear" else ""
    out["verified"] = bool(correct and out["quote_ok"] and out["support_ok"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--key", default="benchmark/answer_key.csv")
    a = ap.parse_args()
    run_dir = ROOT / a.run_dir
    key = load_key(ROOT / a.key)
    qmeta = {q["id"]: q for q in json.load((BENCH / "questions.json").open())}
    ov_path = run_dir / "support_overrides.csv"
    overrides = {(r["method"], r["question_id"], r["ticker"]): r for r in csv.DictReader(open(ov_path))} \
        if ov_path.exists() else {}
    calls, all_calls = latest_calls(run_dir)
    manifest = json.load(open(run_dir / "manifest.json"))
    tickers = manifest["tickers"]
    qids = sorted({c["question_id"] for c in calls.values()}, key=lambda x: (x[0], int(x[1:])))

    rows = []
    for qid in qids:
        ev_chunks, _ = load_evidence(qid)
        for method in ("A", "B"):
            for t in tickers:
                ck = (method, qid, ",".join(tickers) if method == "A" else t)
                call = calls.get(ck)
                if call is None:
                    continue
                picked = None
                for r in ((call.get("parsed") or {}).get("rows") or []):
                    if company_to_ticker(r.get("company")) == t:
                        picked = r
                        break
                rows.append(score_row(method, qid, t, picked, call, key[(qid, t)], ev_chunks, overrides))
    for r in rows:
        q = qmeta[r["question_id"]]
        r["tricky"] = q.get("tricky", False)
        r["tricky_type"] = q.get("tricky_type", "")

    cols = ["method", "question_id", "ticker", "company", "tricky", "tricky_type", "status", "answer", "value",
            "unit", "period", "excerpt_id", "quote", "expected_answer", "expect_abstain", "abstained", "correct",
            "quote_ok", "quote_in_other_excerpt", "period_check", "support", "support_ok", "support_reasons",
            "verified", "needs_human", "call_error"]
    with open(run_dir / "scored_rows.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    # paired table over (question, company) units
    by = defaultdict(dict)
    for r in rows:
        by[(r["question_id"], r["ticker"])][r["method"]] = r

    def paired(metric, subset=None):
        c = Counter()
        for (qid, t), d in by.items():
            if "A" not in d or "B" not in d:
                continue
            if subset is not None and not subset(qid):
                continue
            a, b = bool(d["A"][metric]), bool(d["B"][metric])
            c[{(True, True): "both", (True, False): "only_A", (False, True): "only_B",
               (False, False): "neither"}[(a, b)]] += 1
        return dict(c)

    def mstats(method, subset=None):
        rs = [r for r in rows if r["method"] == method and (subset is None or subset(r["question_id"]))]
        n = len(rs)
        return {"n": n, **{m: sum(bool(r[m]) for r in rs) for m in ("correct", "quote_ok", "support_ok", "verified", "abstained")},
                "errors": sum(r["status"] in ("error", "missing_row") for r in rs),
                "needs_human": sum(r.get("needs_human") == "yes" for r in rs)}

    def agg(records):
        u = defaultdict(lambda: Counter())
        for c in records:
            us = c.get("usage") or {}
            m = c["method"]
            u[m]["calls"] += 1
            u[m]["errored_calls"] += bool(c.get("error"))
            u[m]["prompt_tokens"] += us.get("prompt_token_count") or 0
            u[m]["output_tokens"] += (us.get("candidates_token_count") or 0) + (us.get("thoughts_token_count") or 0)
            u[m]["thinking_tokens"] += us.get("thoughts_token_count") or 0
            u[m]["latency_s"] += c.get("latency_s") or 0
            u[m]["cost_usd_est"] += c.get("cost_usd_est") or 0
        return {m: {k: (round(v, 6) if isinstance(v, float) else v) for k, v in d.items()} for m, d in u.items()}

    # "scored": the one record per call that was scored (what each method costs when the API is healthy).
    # "all_records": every logged request including failed ones (outage waits, quota errors, retries).
    usage = agg(calls.values())
    usage_all = agg(all_calls)
    tricky = lambda q: qmeta[q].get("tricky", False)
    nontricky = lambda q: not qmeta[q].get("tricky", False)
    summary = {
        "run": a.run_dir, "model": manifest["model"], "units": len(by),
        "methods": {m: mstats(m) for m in ("A", "B")},
        "methods_tricky": {m: mstats(m, tricky) for m in ("A", "B")},
        "methods_nontricky": {m: mstats(m, nontricky) for m in ("A", "B")},
        "paired_verified": paired("verified"), "paired_correct": paired("correct"),
        "paired_verified_tricky": paired("verified", tricky),
        "paired_verified_nontricky": paired("verified", nontricky),
        "usage": usage,
        "usage_all_records": usage_all,
        "usage_note": "usage = scored records only; usage_all_records adds failed/retried requests. "
                      "Costs are estimates: API token counts x configured per-token prices.",
    }
    va, vb = summary["methods"]["A"]["verified"], summary["methods"]["B"]["verified"]
    ca, cb = usage.get("A", {}).get("cost_usd_est", 0), usage.get("B", {}).get("cost_usd_est", 0)
    if va != vb:
        more, less = ("B", "A") if vb > va else ("A", "B")
        dv, dc = abs(vb - va), (cb - ca) if more == "B" else (ca - cb)
        summary["cost_per_additional_verified_answer"] = {
            "method_with_more_verified": more, "additional_verified": dv, "additional_cost_usd_est": round(dc, 6),
            "usd_per_additional_verified": round(dc / dv, 6),
            "note": "estimated: token counts from API usage metadata x configured per-token prices"}
    else:
        summary["cost_per_additional_verified_answer"] = None
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
