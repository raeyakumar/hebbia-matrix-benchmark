"""Estimate API cost of a planned run from dry-run prompts (no API calls).

Input tokens ~= characters / 3.07 (measured on the pilot: 5,274 tokens for 16.2k chars);
output ~= 180 tokens per JSON row + 20 per call (pilot: 160/row; thinking "low" used 0).
Usage: python estimate_cost.py results/final_dryrun/dry_run_prompts.jsonl
"""
import json
import sys

from config import PRICING
from prompts import SYSTEM_INSTRUCTION


def main(path):
    calls = [json.loads(l) for l in open(path)]
    total = {}
    for m in ("A", "B"):
        cs = [c for c in calls if c["method"] == m]
        tin = sum(len(c["prompt"]) + len(SYSTEM_INSTRUCTION) for c in cs) / 3.07
        tout = sum(len(c["tickers"]) for c in cs) * 180 + len(cs) * 20
        for model, p in PRICING.items():
            usd = (tin * p["input"] + tout * p["output"]) / 1e6
            total.setdefault(model, 0)
            total[model] += usd
            print(f"Method {m}: {len(cs):3d} calls ~{tin/1e3:6.0f}k in ~{tout/1e3:5.1f}k out  {model:24s} ${usd:.3f}")
    for model, usd in total.items():
        print(f"TOTAL {model}: ${usd:.3f}")


if __name__ == "__main__":
    main(sys.argv[1])
