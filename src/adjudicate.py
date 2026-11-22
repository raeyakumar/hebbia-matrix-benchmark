"""Post-run adjudication tiers, computed WITHOUT modifying the frozen scorer.

tier1_frozen      : scored_rows.csv exactly as the frozen src/score.py produced it
tier2_support     : + support verdicts re-judged from the excerpts (results/<run>/adjudication.csv, field=support)
tier3_key_fix     : + post-hoc correction of answer-key defects (field=correct)
Tier 2/3 judgments are an AI-assisted review (results/<run>/citation_review.md), not independent human
verification. Tier 1 (frozen) is the main result. A support verdict of "inconclusive" is NOT counted as verified.

Usage: python adjudicate.py results/final
"""
import csv
import json
import sys
from collections import Counter

from config import BENCH, ROOT


def tiers(run):
    rows = list(csv.DictReader(open(run / "scored_rows.csv")))
    adj = list(csv.DictReader(open(run / "adjudication.csv")))
    qmeta = {q["id"]: q for q in json.load((BENCH / "questions.json").open())}
    out = {}
    for tier, fields in (("tier1_frozen", set()), ("tier2_support", {"support"}), ("tier3_key_fix", {"support", "correct"})):
        res = []
        for r in rows:
            r = dict(r)
            for a in adj:
                if (a["method"], a["question_id"], a["ticker"]) == (r["method"], r["question_id"], r["ticker"]) \
                        and a["field"] in fields and a["adjudicated_value"] != "(unchanged)":
                    if a["field"] == "support":
                        r["support_ok"] = str(a["adjudicated_value"] == "pass")
                    else:
                        r["correct"] = a["adjudicated_value"]
            if r["abstained"] == "True":
                r["verified"] = r["correct"]
            else:
                r["verified"] = str(r["correct"] == "True" and r["quote_ok"] == "True" and r["support_ok"] == "True")
            res.append(r)
        out[tier] = res
    return out, qmeta


def paired(rows, subset=lambda q: True):
    by = {}
    for r in rows:
        if subset(r["question_id"]):
            by.setdefault((r["question_id"], r["ticker"]), {})[r["method"]] = r["verified"] == "True"
    c = Counter({"both": 0, "only_A": 0, "only_B": 0, "neither": 0})
    for d in by.values():
        c[{(True, True): "both", (True, False): "only_A", (False, True): "only_B", (False, False): "neither"}[(d["A"], d["B"])]] += 1
    return dict(c)


def main(run):
    run = ROOT / run
    t, qmeta = tiers(run)
    tricky = lambda q: qmeta[q].get("tricky", False)
    summary = {}
    for name, rows in t.items():
        summary[name] = {
            "verified": {m: sum(r["verified"] == "True" for r in rows if r["method"] == m) for m in "AB"},
            "correct": {m: sum(r["correct"] == "True" for r in rows if r["method"] == m) for m in "AB"},
            "paired_verified_all": paired(rows),
            "paired_verified_tricky": paired(rows, tricky),
            "paired_verified_nontricky": paired(rows, lambda q: not tricky(q)),
        }
    (run / "adjudicated_summary.json").write_text(json.dumps(summary, indent=1))
    # one results CSV: every cell, both methods side by side, all tiers
    by = {}
    for name, rows in t.items():
        for r in rows:
            k = (r["question_id"], r["ticker"])
            d = by.setdefault(k, {"question_id": k[0], "company": r["company"], "tricky_type": r["tricky_type"] or "",
                                  "expected_answer": r["expected_answer"]})
            m = r["method"]
            if name == "tier1_frozen":
                d.update({f"{m}_status": r["status"], f"{m}_value": r["value"], f"{m}_unit": r["unit"],
                          f"{m}_period": r["period"], f"{m}_excerpt_id": r["excerpt_id"], f"{m}_quote": r["quote"],
                          f"{m}_correct": r["correct"], f"{m}_quote_ok": r["quote_ok"], f"{m}_support": r["support"]})
            d[f"{m}_verified_{name}"] = r["verified"]
    keys = sorted(by, key=lambda k: (k[0][0] != "F", int(k[0][1:]), k[1]))
    cols = list(by[keys[0]].keys())
    with open(ROOT / "results" / "results_final.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(by[k] for k in keys)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
