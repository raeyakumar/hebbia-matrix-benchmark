"""Write benchmark/FREEZE.json: SHA-256 of every file that determines model inputs or scoring.
Usage: python freeze.py            (write)   |   python freeze.py --check   (verify nothing changed)
"""
import hashlib
import json
import sys

from config import BENCH, DATA, ROOT

FILES = (["src/config.py", "src/prompts.py", "src/run_benchmark.py", "src/score.py", "src/select_evidence.py",
          "src/extract.py", "benchmark/questions.json", "benchmark/answer_key.csv", "data/filings.csv",
          "results/final_dryrun/dry_run_prompts.jsonl"]
         + sorted(str(p.relative_to(ROOT)) for p in (BENCH / "evidence").glob("*.json"))
         + sorted(str(p.relative_to(ROOT)) for p in (DATA / "chunks").glob("*.jsonl")))


def digest():
    return {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in FILES}


if __name__ == "__main__":
    path = BENCH / "FREEZE.json"
    if "--check" in sys.argv:
        frozen = json.load(path.open())["sha256"]
        changed = [f for f, h in digest().items() if frozen.get(f) != h]
        print("frozen files unchanged" if not changed else f"CHANGED since freeze: {changed}")
        sys.exit(1 if changed else 0)
    from config import GENERATION, MODEL, THINKING_LEVEL
    json.dump({"frozen_on": "2026-11-22", "model": MODEL, "generation": GENERATION, "thinking_level": THINKING_LEVEL,
               "sha256": digest()}, path.open("w"), indent=1)
    print(f"wrote {path.name} ({len(FILES)} files)")
