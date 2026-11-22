"""Run Method A (all companies, one call) and Method B (one company per call).

Usage:
  python run_benchmark.py --set practice --tickers AAPL,MSFT --out results/pilot
  python run_benchmark.py --set final --out results/final
  python run_benchmark.py ... --dry-run      # build prompts + token estimate, no API calls

Every call -- successful or not -- is appended to <out>/calls.jsonl with the exact prompt
hash, raw response text, parsed rows, token usage, latency and error (if any).
A call that still fails after retries is preserved as an error record, not dropped.
"""
import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone

import requests

from config import BENCH, COMPANIES, GENERATION, MODEL, PRICING, ROOT, THINKING_LEVEL, TICKER_TO_NAME, gemini_key
from prompts import RESPONSE_SCHEMA, SYSTEM_INSTRUCTION, Answer, build_prompt, prompt_hash

MAX_ATTEMPTS = 6
BACKOFF_S = [10, 20, 40, 60, 90]  # capacity 503s/429s: ~3.7 min total before giving up
RETRYABLE = {429, 500, 502, 503, 504}
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def request_body(prompt):
    """The exact JSON sent to the API (saved alongside results for auditability)."""
    return {
        "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {**GENERATION, "responseMimeType": "application/json",
                             "responseJsonSchema": RESPONSE_SCHEMA,
                             "thinkingConfig": {"thinkingLevel": THINKING_LEVEL}},
    }


def cost(usage):
    p = PRICING.get(MODEL)
    if not p or not usage:
        return None
    out_tokens = (usage.get("candidates_token_count") or 0) + (usage.get("thoughts_token_count") or 0)
    return round(((usage.get("prompt_token_count") or 0) * p["input"] + out_tokens * p["output"]) / 1e6, 6)


def call(session, prompt):
    rec = {"attempts": [], "response_text": None, "parsed": None, "usage": None, "error": None}
    url = ENDPOINT.format(model=MODEL)
    body = request_body(prompt)
    for attempt in range(1, MAX_ATTEMPTS + 1):
        t0 = time.time()
        try:
            r = session.post(url, json=body, timeout=300)
            dt = time.time() - t0
            if r.status_code != 200:
                msg = f"HTTP {r.status_code}: {r.text[:1500]}"
                rec["attempts"].append({"attempt": attempt, "latency_s": round(dt, 3), "ok": False, "error": msg})
                rec["error"] = msg
                if r.status_code == 429 and "quota" in r.text.lower():
                    rec["quota_exhausted"] = True  # retrying cannot help; the caller stops the run
                    break
                if attempt < MAX_ATTEMPTS and r.status_code in RETRYABLE:
                    time.sleep(BACKOFF_S[attempt - 1])
                    continue
                break
            d = r.json()
            u = d.get("usageMetadata", {})
            rec["usage"] = {"prompt_token_count": u.get("promptTokenCount"),
                            "candidates_token_count": u.get("candidatesTokenCount"),
                            "thoughts_token_count": u.get("thoughtsTokenCount"),
                            "total_token_count": u.get("totalTokenCount")}
            rec["model_version"] = d.get("modelVersion")
            rec["response_id"] = d.get("responseId")
            cand = (d.get("candidates") or [{}])[0]
            rec["finish_reason"] = cand.get("finishReason")
            text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []) if not p.get("thought"))
            rec["response_text"] = text
            rec["attempts"].append({"attempt": attempt, "latency_s": round(dt, 3), "ok": True})
            try:
                rec["parsed"] = json.loads(text)
                Answer.model_validate(rec["parsed"])
                rec["error"] = None
            except Exception as e:  # malformed output is an error, kept with its raw text
                rec["error"] = f"parse_error: {str(e)[:300]}"
            break
        except requests.RequestException as e:
            dt = time.time() - t0
            msg = f"{type(e).__name__}: {str(e)[:300]}"
            rec["attempts"].append({"attempt": attempt, "latency_s": round(dt, 3), "ok": False, "error": msg})
            rec["error"] = msg
            if attempt < MAX_ATTEMPTS:
                time.sleep(BACKOFF_S[attempt - 1])
                continue
            break
    rec["latency_s"] = round(sum(a["latency_s"] for a in rec["attempts"]), 3)
    rec["cost_usd_est"] = cost(rec["usage"])
    return rec


def plan_calls(qset, tickers, methods):
    qs = [q for q in json.load((BENCH / "questions.json").open()) if q["set"] == qset]
    calls = []
    for q in qs:
        ev = json.load((BENCH / "evidence" / f"{q['id']}.json").open())
        if "A" in methods:
            calls.append({"method": "A", "question_id": q["id"], "tickers": tickers,
                          "prompt": build_prompt(q, ev, tickers)})
        if "B" in methods:
            for t in tickers:
                calls.append({"method": "B", "question_id": q["id"], "tickers": [t],
                              "prompt": build_prompt(q, ev, [t])})
    return calls


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="practice")
    ap.add_argument("--tickers", default=",".join(t for t, _ in COMPANIES.values()))
    ap.add_argument("--methods", default="A,B")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-usd", type=float, required=False, default=None,
                    help="hard stop once estimated spend in this run directory reaches this amount")
    a = ap.parse_args()
    tickers = a.tickers.split(",")
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    calls = plan_calls(a.set, tickers, a.methods.split(","))

    manifest = {"model": MODEL, "generation": GENERATION, "thinking_level": THINKING_LEVEL,
                "endpoint": ENDPOINT.format(model=MODEL), "request_template": request_body("<prompt>"),
                "prompt_template_hash": prompt_hash(), "set": a.set, "tickers": tickers,
                "n_calls": len(calls), "started_utc": datetime.now(timezone.utc).isoformat()}
    if a.dry_run:
        chars = sum(len(c["prompt"]) + len(SYSTEM_INSTRUCTION) for c in calls)
        manifest["prompt_chars_total"] = chars
        (out / "dry_run_prompts.jsonl").write_text("\n".join(json.dumps(c) for c in calls) + "\n")
        print(json.dumps(manifest, indent=1))
        return

    key = gemini_key()
    if not key:
        sys.exit("GEMINI_API_KEY is not set. Put it in .env at the project root (see .env.example).")
    if a.max_usd is None:
        sys.exit("Refusing to make paid calls without --max-usd (spend cap).")
    session = requests.Session()
    session.headers.update({"x-goog-api-key": key, "Content-Type": "application/json"})
    done, spent = set(), 0.0
    log = out / "calls.jsonl"
    if log.exists():  # resume: skip calls already recorded without error; count prior spend
        for l in log.open():
            r = json.loads(l)
            spent += r.get("cost_usd_est") or 0
            if not r.get("error"):
                done.add((r["method"], r["question_id"], ",".join(r["tickers"])))
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    with log.open("a") as fh:
        for i, c in enumerate(calls, 1):
            key_ = (c["method"], c["question_id"], ",".join(c["tickers"]))
            if key_ in done:
                continue
            if spent >= a.max_usd:
                print(f"STOP: estimated spend ${spent:.4f} reached cap ${a.max_usd:.2f}")
                break
            rec = call(session, c["prompt"])
            spent += rec["cost_usd_est"] or 0
            rec.update({"method": c["method"], "question_id": c["question_id"], "tickers": c["tickers"],
                        "companies": [TICKER_TO_NAME[t] for t in c["tickers"]], "model": MODEL,
                        "prompt_sha256": hashlib.sha256(c["prompt"].encode()).hexdigest(),
                        "timestamp_utc": datetime.now(timezone.utc).isoformat()})
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            if rec.get("quota_exhausted"):
                print("STOP: API quota exhausted (HTTP 429). Recorded as an error; resume later with the same command.")
                break
            status = "ERROR " + rec["error"][:120] if rec["error"] else "ok"
            u = rec["usage"] or {}
            print(f"[{i}/{len(calls)}] {c['method']} {c['question_id']} {','.join(c['tickers'])}: {status} | "
                  f"in {u.get('prompt_token_count')} out {u.get('candidates_token_count')} "
                  f"think {u.get('thoughts_token_count')} | {rec['latency_s']}s | ${spent:.4f} cumulative")


if __name__ == "__main__":
    main()
