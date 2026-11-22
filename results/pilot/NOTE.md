# Pilot run (pipeline test only)

Run 2026-11-22 on Apple + Microsoft, practice questions P1-P2, gemini-3.8-flash.
- The first attempts hit HTTP 503 (model overloaded) and then the free-tier daily quota (HTTP 429); all are kept in calls.jsonl as error records.
- The 6 scored calls succeeded after billing was enabled: Method A 4/4 verified, Method B 4/4 verified.
- After the pilot, the text extractor was fixed (words glued across table-cell lines, e.g. "June 30,2026"). The pilot prompts therefore
  differ slightly from what the current code would build. The pilot is evidence that the pipeline works, not a result.
- The first scored call (A/P1) ran during the overload: its 198 s latency is not representative.
