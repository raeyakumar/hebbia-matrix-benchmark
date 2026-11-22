"""Select evidence ONCE per question and freeze it to benchmark/evidence/<qid>.json.

Retrieval is plain BM25 over each company's chunks, driven only by the question's
`retrieval_query` in benchmark/questions.json. The answer key is never read here.
Method A receives every company's excerpts concatenated; Method B receives the same
excerpts split by company. Both read this file, so the evidence is identical.
"""
import json
import math
import re
import sys
from collections import Counter

from config import BENCH, CHUNKS, COMPANIES, EXCERPTS_PER_COMPANY

TOKEN = re.compile(r"[a-z0-9]+")
STOP = set("the a an of and or to in for on by with as at is are was were be from that this which its our we".split())


def toks(s):
    return [t for t in TOKEN.findall(s.lower()) if t not in STOP]


class BM25:
    def __init__(self, docs, k1=1.5, b=0.75):
        self.docs = [Counter(d) for d in docs]
        self.len = [len(d) for d in docs]
        self.avg = sum(self.len) / max(len(docs), 1)
        df = Counter(t for d in self.docs for t in d)
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.k1, self.b = k1, b

    def score(self, q):
        out = []
        for d, L in zip(self.docs, self.len):
            s = 0.0
            for t in q:
                if t in d:
                    tf = d[t]
                    s += self.idf[t] * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * L / self.avg))
            out.append(s)
        return out


def load_chunks(ticker):
    return [json.loads(l) for l in (CHUNKS / f"{ticker}.jsonl").open()]


def select(question, tickers, k=EXCERPTS_PER_COMPANY):
    q = toks(question["retrieval_query"])
    ev = {"question_id": question["id"], "retrieval_query": question["retrieval_query"],
          "k_per_company": k, "companies": {}}
    for t in tickers:
        chunks = load_chunks(t)
        bm = BM25([toks(c["heading"] + " " + c["text"]) for c in chunks])
        scores = bm.score(q)
        top = sorted(range(len(chunks)), key=lambda i: (-scores[i], i))[:k]
        top.sort()  # present in document order
        ev["companies"][t] = [{**chunks[i], "bm25": round(scores[i], 3)} for i in top]
    return ev


def main(qset, tickers):
    qs = [q for q in json.load((BENCH / "questions.json").open()) if q["set"] == qset]
    out_dir = BENCH / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)
    for q in qs:
        ev = select(q, tickers)
        (out_dir / f"{q['id']}.json").write_text(json.dumps(ev, indent=1))
        print(q["id"], {t: [c["id"] for c in v] for t, v in ev["companies"].items()})


if __name__ == "__main__":
    qset = sys.argv[1] if len(sys.argv) > 1 else "practice"
    tickers = sys.argv[2].split(",") if len(sys.argv) > 2 else [t for t, _ in COMPANIES.values()]
    main(qset, tickers)
