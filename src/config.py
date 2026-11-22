"""Shared configuration. Everything that affects model inputs or scoring lives here
or in benchmark/ so it can be frozen in one Git commit."""
from pathlib import Path
import os

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

DATA = ROOT / "data"
RAW = DATA / "raw"            # downloaded HTML (git-ignored, re-fetchable, hash-checked)
TEXT = DATA / "text"          # extracted plain text with tables preserved
CHUNKS = DATA / "chunks"      # excerpt units with stable ids
BENCH = ROOT / "benchmark"
RESULTS = ROOT / "results"

SEC_USER_AGENT = os.getenv("SEC_USER_AGENT", "independent-research-benchmark research@example.org")

COMPANIES = {
    # name: (ticker, CIK)
    "Apple": ("AAPL", "0000320193"),
    "Microsoft": ("MSFT", "0000789019"),
    "Alphabet": ("GOOGL", "0001652044"),
    "Meta": ("META", "0001326801"),
    "Amazon": ("AMZN", "0001018724"),
}
TICKER_TO_NAME = {t: n for n, (t, _) in COMPANIES.items()}

# ---- Model settings (identical for Method A and Method B) ----
# gemini-3.8-flash: newest stable (non-preview) Flash available to the key on 2026-11-22.
# gemini-2.5-flash was rejected: deprecated, and rerouted to another model from 2026-12-01.
MODEL = os.getenv("BENCH_MODEL", "gemini-3.8-flash")
GENERATION = {
    "temperature": 0.0,
    "topP": 1.0,
    "maxOutputTokens": 8192,
    "seed": 7,
}
# 3.8 Flash cannot disable thinking; "low" is its lowest documented level. Same for both methods.
THINKING_LEVEL = os.getenv("BENCH_THINKING_LEVEL", "low")

# USD per 1M tokens, paid Standard tier, from https://ai.google.dev/gemini-api/docs/pricing (read 2026-11-22).
# Output price includes thinking tokens. 3.8 Flash rates double on 2027-01-01.
# Costs in results are labeled "estimated": API token counts x these rates.
PRICING = {
    "gemini-3.8-flash": {"input": 0.75, "output": 3.75},
    "gemini-2.5-flash": {"input": 0.30, "output": 2.50},
}

# ---- Evidence selection ----
CHUNK_TARGET_CHARS = 1800      # approximate excerpt size
EXCERPTS_PER_COMPANY = 5       # top-k per company per question


def gemini_key():
    k = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    return k or None
