"""One instruction template shared verbatim by Method A and Method B.

The only things that differ between methods are (1) which companies are listed and
(2) which companies' excerpts are attached -- and B's excerpts for a company are the
exact same objects A receives for that company.
"""
import csv
import hashlib
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from config import DATA, TICKER_TO_NAME

SYSTEM_INSTRUCTION = """You are a careful financial analyst answering questions about companies' SEC Form 10-K filings.

Rules:
1. Use ONLY the excerpts provided. Do not use outside knowledge, even if you believe you know the answer.
2. Return exactly one row for every company listed under "Companies", using the company name exactly as written there.
3. For each row, cite exactly one excerpt by its id (for example "AAPL-0123") and copy a short verbatim quote (one sentence or one table row, at most 300 characters) from that excerpt that directly supports your answer. Copy the quote character for character, including the " | " separators used in tables.
4. Report the number as it is stated in the filing in `value` and give its unit in `unit` (for example "USD millions", "USD billions", "percent", "employees"). Do not rescale unless the question asks you to.
5. State the reporting period the value refers to in `period` (for example "fiscal year ended September 26, 2026" or "as of December 31, 2025").
6. If the excerpts for a company do not contain enough information to answer, set `status` to "insufficient_evidence", leave `value` null, and explain briefly in `answer`. Do not guess.
7. Cite only an excerpt that belongs to the company in that row."""

USER_TEMPLATE = """Question: {question}

Companies: {company_list}

Excerpts:
{excerpts}"""


class Row(BaseModel):
    company: str
    status: Literal["answered", "insufficient_evidence"]
    answer: str = Field(description="Short natural-language answer")
    value: Optional[float] = Field(description="Numeric value as stated in the filing, or null")
    unit: str
    period: str
    excerpt_id: str
    quote: str


class Answer(BaseModel):
    rows: List[Row]


# JSON Schema sent as responseJsonSchema (inlined; mirrors the Answer model above).
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {"rows": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "company": {"type": "string"},
            "status": {"type": "string", "enum": ["answered", "insufficient_evidence"]},
            "answer": {"type": "string", "description": "Short natural-language answer"},
            "value": {"type": ["number", "null"], "description": "Numeric value as stated in the filing, or null"},
            "unit": {"type": "string"},
            "period": {"type": "string"},
            "excerpt_id": {"type": "string"},
            "quote": {"type": "string"},
        },
        "required": ["company", "status", "answer", "value", "unit", "period", "excerpt_id", "quote"],
    }}},
    "required": ["rows"],
}


def _filing_meta():
    return {r["ticker"]: r for r in csv.DictReader((DATA / "filings.csv").open())}


def render_excerpts(evidence, tickers):
    meta = _filing_meta()
    parts = []
    for t in tickers:
        m = meta[t]
        parts.append(f"=== Company: {TICKER_TO_NAME[t]} | Form 10-K for fiscal year ended {m['fiscal_year_end']} "
                     f"(filed {m['filing_date']}) ===")
        for c in evidence["companies"][t]:
            head = f" | Section: {c['heading']}" if c["heading"] else ""
            parts.append(f"[{c['id']}]{head}\n{c['text']}\n")
    return "\n".join(parts)


def build_prompt(question, evidence, tickers):
    return USER_TEMPLATE.format(
        question=question["question"],
        company_list=", ".join(TICKER_TO_NAME[t] for t in tickers),
        excerpts=render_excerpts(evidence, tickers),
    )


def prompt_hash():
    import json as _j
    return hashlib.sha256((SYSTEM_INSTRUCTION + USER_TEMPLATE + _j.dumps(RESPONSE_SCHEMA, sort_keys=True)).encode()).hexdigest()[:12]
