"""Build benchmark/answer_key.csv from a hand-written spec.

Each expected value below was read by hand from the extracted 10-K text (data/text/).
For table facts the spec names the statement title and the exact row; this script copies
the title, unit line, column header and row verbatim into `supporting_passage` so the
reviewer sees the full table context. For prose facts the spec gives the exact sentence.
validate_key.py then re-checks every passage against the filing and fills provenance.

This file is NEVER imported by prompt construction or the model runner.
"""
import csv
import re

from config import BENCH, DATA

YEAR = re.compile(r"20\d\d")

# (qid, ticker, expected_answer, value, unit, period, period_year, abstain,
#  alternates "value@unit;...", (title, row) or "prose sentence", tricky_type, notes)
T = "table"
SPEC = [
 # ---------------- F1 net income ----------------
 ("F1", "AAPL", "$132,175 million", 132175, "USD millions", "fiscal year ended September 26 2026", "2026", "", "",
  (T, "CONSOLIDATED STATEMENTS OF OPERATIONS", "Net income | $132,175 | $112,010 | $93,736"), "", ""),
 ("F1", "MSFT", "$133,749 million", 133749, "USD millions", "fiscal year ended June 30 2026", "2026", "", "",
  (T, "INCOME STATEMENTS", "Net income | $133,749 | $101,832 | $88,136"), "", ""),
 ("F1", "GOOGL", "$132,170 million", 132170, "USD millions", "year ended December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED STATEMENTS OF INCOME", "Net income | $73,795 | $100,118 | $132,170"), "",
  "Columns run oldest to newest (2023 | 2024 | 2025); the most recent year is the LAST column."),
 ("F1", "META", "$60,458 million", 60458, "USD millions", "year ended December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED STATEMENTS OF INCOME", "Net income | $60,458 | $62,360 | $39,098"), "",
  "2025 net income is LOWER than 2024 ($62,360M); a model assuming growth could pick the wrong column."),
 ("F1", "AMZN", "$77,670 million", 77670, "USD millions", "year ended December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED STATEMENTS OF OPERATIONS", "Net income | $30,425 | $59,248 | $77,670"), "",
  "Columns run oldest to newest."),
 # ---------------- F2 diluted EPS ----------------
 ("F2", "AAPL", "$8.98 per diluted share", 8.98, "USD per share", "fiscal year ended September 26 2026", "2026", "", "",
  (T, "CONSOLIDATED STATEMENTS OF OPERATIONS", "Diluted | $8.98 | $7.46 | $6.08"), "", ""),
 ("F2", "MSFT", "$17.95 per diluted share", 17.95, "USD per share", "fiscal year ended June 30 2026", "2026", "", "",
  (T, "INCOME STATEMENTS", "Diluted | $17.95 | $13.64 | $11.80"), "", ""),
 ("F2", "GOOGL", "$10.81 per diluted share", 10.81, "USD per share", "year ended December 31 2025", "2025", "", "",
  "Diluted net income per share (Note 12) | $5.80 | $8.04 | $10.81 || Diluted net income per share | $10.82 | $10.81 | $10.80 | $10.81", "",
  "DECIDED (reviewer, 2026-11-22): question now asks for the company-wide figure as reported on the consolidated income statement, so $10.81 is expected. Note 12's per-class figures (Class A $10.82, Class C $10.80) are NOT accepted; EPS rows use a tight tolerance so they are not silently accepted."),
 ("F2", "META", "$23.49 per diluted share", 23.49, "USD per share", "year ended December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED STATEMENTS OF INCOME", "Diluted | $23.49 | $23.86 | $14.87"), "", ""),
 ("F2", "AMZN", "$7.17 per diluted share", 7.17, "USD per share", "year ended December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED STATEMENTS OF OPERATIONS", "Diluted earnings per share | $2.90 | $5.53 | $7.17"), "", ""),
 # ---------------- F3 cash and cash equivalents ----------------
 ("F3", "AAPL", "$36,305 million", 36305, "USD millions", "as of September 26 2026", "2026", "", "",
  (T, "CONSOLIDATED BALANCE SHEETS", "Cash and cash equivalents | $36,305 | $35,934"), "", ""),
 ("F3", "MSFT", "$20,935 million", 20935, "USD millions", "as of June 30 2026", "2026", "", "",
  (T, "BALANCE SHEETS", "Cash and cash equivalents | $20,935 | $30,242"), "",
  "Balance-sheet cash and cash equivalents only; excludes short-term investments."),
 ("F3", "GOOGL", "$30,708 million", 30708, "USD millions", "as of December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED BALANCE SHEETS", "Cash and cash equivalents | $23,466 | $30,708"), "",
  "Columns 2024 | 2025."),
 ("F3", "META", "$35,873 million", 35873, "USD millions", "as of December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED BALANCE SHEETS", "Cash and cash equivalents | $35,873 | $43,889"), "",
  "Columns 2025 | 2024; cash fell year over year."),
 ("F3", "AMZN", "$86,810 million", 86810, "USD millions", "as of December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED BALANCE SHEETS", "Cash and cash equivalents | $78,779 | $86,810"), "",
  "Columns 2024 | 2025."),
 # ---------------- F4 total assets ----------------
 ("F4", "AAPL", "$404,548 million", 404548, "USD millions", "as of September 26 2026", "2026", "", "",
  (T, "CONSOLIDATED BALANCE SHEETS", "Total assets | $404,548 | $359,241"), "", ""),
 ("F4", "MSFT", "$758,376 million", 758376, "USD millions", "as of June 30 2026", "2026", "", "",
  (T, "BALANCE SHEETS", "Total assets | $758,376 | $619,003"), "", ""),
 ("F4", "GOOGL", "$595,281 million", 595281, "USD millions", "as of December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED BALANCE SHEETS", "Total assets | $450,256 | $595,281"), "", "Columns 2024 | 2025."),
 ("F4", "META", "$366,021 million", 366021, "USD millions", "as of December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED BALANCE SHEETS", "Total assets | $366,021 | $276,054"), "", ""),
 ("F4", "AMZN", "$818,042 million", 818042, "USD millions", "as of December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED BALANCE SHEETS", "Total assets | $624,894 | $818,042"), "", "Columns 2024 | 2025."),
 # ---------------- F5 capex ----------------
 ("F5", "AAPL", "$9,041 million", 9041, "USD millions", "fiscal year ended September 26 2026", "2026", "", "",
  (T, "CONSOLIDATED STATEMENTS OF CASH FLOWS", "Payments for acquisition of property, plant and equipment | (9,041) | (12,715) | (9,447)"), "",
  "Shown as a negative (cash outflow) in the filing; scored on magnitude."),
 ("F5", "MSFT", "$115,948 million", 115948, "USD millions", "fiscal year ended June 30 2026", "2026", "", "",
  (T, "CASH FLOWS STATEMENTS", "Additions to property and equipment | (115,948) | (64,551) | (44,477)"), "",
  "Excludes assets acquired under finance leases, which Microsoft discusses separately."),
 ("F5", "GOOGL", "$91,447 million", 91447, "USD millions", "year ended December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED STATEMENTS OF CASH FLOWS", "Purchases of property and equipment | (32,251) | (52,535) | (91,447)"), "", ""),
 ("F5", "META", "$69,691 million", 69691, "USD millions", "year ended December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED STATEMENTS OF CASH FLOWS", "Purchases of property and equipment | (69,691) | (37,256) | (27,045)"), "", ""),
 ("F5", "AMZN", "$131,819 million", 131819, "USD millions", "year ended December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED STATEMENTS OF CASH FLOWS", "Purchases of property and equipment | (52,729) | (82,999) | (131,819)"), "",
  "AMBIGUOUS-MINOR: gross purchases. Amazon also reports proceeds from property and equipment sales and incentives; a net figure is not accepted."),
 # ---------------- F6 operating income ----------------
 ("F6", "AAPL", "$158,063 million", 158063, "USD millions", "fiscal year ended September 26 2026", "2026", "", "",
  (T, "CONSOLIDATED STATEMENTS OF OPERATIONS", "Operating income | 158,063 | 133,050 | 123,216"), "", ""),
 ("F6", "MSFT", "$155,237 million", 155237, "USD millions", "fiscal year ended June 30 2026", "2026", "", "",
  (T, "INCOME STATEMENTS", "Operating income | 155,237 | 128,528 | 109,433"), "", ""),
 ("F6", "GOOGL", "$129,039 million", 129039, "USD millions", "year ended December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED STATEMENTS OF INCOME", "Income from operations | 84,293 | 112,390 | 129,039"), "", ""),
 ("F6", "META", "$83,276 million", 83276, "USD millions", "year ended December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED STATEMENTS OF INCOME", "Income from operations | 83,276 | 69,380 | 46,751"), "", ""),
 ("F6", "AMZN", "$79,975 million", 79975, "USD millions", "year ended December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED STATEMENTS OF OPERATIONS", "Operating income | 36,852 | 68,593 | 79,975"), "", ""),
 # ---------------- F7 operating cash flow ----------------
 ("F7", "AAPL", "$145,097 million", 145097, "USD millions", "fiscal year ended September 26 2026", "2026", "", "",
  (T, "CONSOLIDATED STATEMENTS OF CASH FLOWS", "Cash generated by operating activities | 145,097 | 111,482 | 118,254"), "", ""),
 ("F7", "MSFT", "$182,935 million", 182935, "USD millions", "fiscal year ended June 30 2026", "2026", "", "",
  (T, "CASH FLOWS STATEMENTS", "Net cash from operations | 182,935 | 136,162 | 118,548"), "", ""),
 ("F7", "GOOGL", "$164,713 million", 164713, "USD millions", "year ended December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED STATEMENTS OF CASH FLOWS", "Net cash provided by operating activities | 101,746 | 125,299 | 164,713"), "", ""),
 ("F7", "META", "$115,800 million", 115800, "USD millions", "year ended December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED STATEMENTS OF CASH FLOWS", "Net cash provided by operating activities | 115,800 | 91,328 | 71,113"), "", ""),
 ("F7", "AMZN", "$139,514 million", 139514, "USD millions", "year ended December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED STATEMENTS OF CASH FLOWS", "Net cash provided by (used in) operating activities | 84,946 | 115,877 | 139,514"), "", ""),
 # ---------------- F8 stockholders' equity ----------------
 ("F8", "AAPL", "$112,093 million", 112093, "USD millions", "as of September 26 2026", "2026", "", "",
  (T, "CONSOLIDATED BALANCE SHEETS", "Total shareholders' equity | 112,093 | 73,733"), "", ""),
 ("F8", "MSFT", "$442,387 million", 442387, "USD millions", "as of June 30 2026", "2026", "", "",
  (T, "BALANCE SHEETS", "Total stockholders' equity | 442,387 | 343,479"), "", ""),
 ("F8", "GOOGL", "$415,265 million", 415265, "USD millions", "as of December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED BALANCE SHEETS", "Total stockholders' equity | 325,084 | 415,265"), "", ""),
 ("F8", "META", "$217,243 million", 217243, "USD millions", "as of December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED BALANCE SHEETS", "Total stockholders' equity | 217,243 | 182,637"), "", ""),
 ("F8", "AMZN", "$411,065 million", 411065, "USD millions", "as of December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED BALANCE SHEETS", "Total stockholders' equity | 285,970 | 411,065"), "", ""),
 # ---------------- F9 / F10 matched pair: repurchased vs remaining ----------------
 ("F9", "AAPL", "$85.8 billion repurchased", 85.8, "USD billions", "fiscal year ended September 26 2026", "2026", "", "",
  "During 2026, the Company repurchased 297 million shares of its common stock for $85.8 billion.", "",
  "DECIDED (reviewer, 2026-11-22): only $85.8B accepted. The equity-statement ($86,485M) and cash-flow ($86,390M) figures are NOT accepted."),
 ("F9", "MSFT", "$16.7 billion repurchased", 16.7, "USD billions", "fiscal year ended June 30 2026", "2026", "", "",
  "During fiscal years 2026 and 2025, we repurchased 36 million shares and 31 million shares of our common stock for $16.7 billion and $13.0 billion, respectively, through our share repurchase program.", "",
  "DECIDED (reviewer, 2026-11-22): only $16.7B accepted. The cash-flow line 'Common stock repurchased' ($22,271M) also includes shares withheld for employee taxes and is NOT accepted. Same sentence also gives FY2025 ($13.0B) - period trap."),
 ("F9", "GOOGL", "$45.4 billion repurchased", 45.4, "USD billions", "year ended December 31 2025", "2025", "", "",
  "During 2025, we repurchased and subsequently retired 240 million shares for $45.4 billion.", "", ""),
 ("F9", "META", "$26.26 billion repurchased", 26.26, "USD billions", "year ended December 31 2025", "2025", "", "",
  "In 2025, we repurchased and subsequently retired 40 million shares of our Class A common stock for an aggregate amount of $26.26 billion.", "",
  "MATCHED-PAIR SHOWCASE: the same two sentences give $26.26B repurchased and $25.03B remaining."),
 ("F9", "AMZN", "$0 (no repurchases in 2025)", 0, "USD billions", "year ended December 31 2025", "2025", "", "",
  "There were no repurchases of our common stock in 2023, 2024, or 2025.", "",
  "Correct answer is zero, stated explicitly; an 'insufficient evidence' abstention is scored wrong. Same passage gives $6.1B remaining (F10)."),
 ("F10", "AAPL", "$114,004 million (about $114.0 billion) may yet be purchased under the plans or programs", 114004, "USD millions",
  "as of September 26 2026", "2026", "", "",
  "Periods | Total Number of Shares Purchased | Average Price Paid Per Share | Total Number of Shares Purchased as Part of Publicly Announced Plans or Programs | Approximate Dollar Value of Shares That May Yet Be Purchased Under the Plans or Programs (1) || As of September 26, 2026, remaining availability under the May 2025 program was $14.0 billion. || Total | 81,767 | $114,004", "",
  "DECIDED (reviewer rule, 2026-11-22): $114B is accepted only if the excerpts both methods receive establish the full total. They do: the Item 5 table (excerpt AAPL-0091, in the F10 evidence) states the 'Approximate Dollar Value of Shares That May Yet Be Purchased Under the Plans or Programs' as $114,004 million, and footnote (1) gives $14.0B under the May 2025 program plus the new $100B program. $14.0B alone is NOT accepted, because the question asks for the total across all active programs. Note the extracted Total row drops empty cells, so the $114,004 figure sits next to the share count; the column header names it. Caution: the table is labeled 'in millions, except number of shares, which are reflected in thousands'."),
 ("F10", "MSFT", "$40.6 billion remaining", 40.6, "USD billions", "as of June 30 2026", "2026", "", "",
  "As of June 30, 2026, $40.6 billion remained of our $60 billion share repurchase program.", "",
  "Trap: the $60B program size appears in the same sentence."),
 ("F10", "GOOGL", "$69.5 billion remaining", 69.5, "USD billions", "as of December 31 2025", "2025", "", "",
  "As of December 31, 2025, $69.5 billion remained available for Class A and Class C share repurchases.", "",
  "Trap: two $70.0B authorizations appear in the same paragraph."),
 ("F10", "META", "$25.03 billion remaining", 25.03, "USD billions", "as of December 31 2025", "2025", "", "",
  "As of December 31, 2025, $25.03 billion remained available and authorized for repurchases.", "",
  "MATCHED-PAIR SHOWCASE (see F9). The Note version of this passage also gives the prior-year $51.28B remaining."),
 ("F10", "AMZN", "$6.1 billion remaining", 6.1, "USD billions", "as of December 31 2025", "2025", "", "",
  "As of December 31, 2025, we have $6.1 billion remaining under the repurchase program.", "",
  "Trap: the $10.0B program size appears in the same passage."),
 # ---------------- T1 units: diluted weighted-average shares ----------------
 ("T1", "AAPL", "14,720,306 thousand shares (about 14.72 billion)", 14720306, "thousand shares", "fiscal year ended September 26 2026", "2026", "", "",
  (T, "CONSOLIDATED STATEMENTS OF OPERATIONS", "Diluted | 14,720,306 | 15,004,697 | 15,408,095"), "units",
  "UNIT TRAP: Apple reports share counts in THOUSANDS while dollar amounts are in millions (stated in the statement's unit line). A model reading 14,720,306 as millions is off by 1,000x."),
 ("T1", "MSFT", "7,453 million shares", 7453, "million shares", "fiscal year ended June 30 2026", "2026", "", "",
  (T, "INCOME STATEMENTS", "Diluted | 7,453 | 7,465 | 7,469"), "units", ""),
 ("T1", "GOOGL", "12,230 million shares (Class A 6,671M as-converted + Class C 5,559M)", 12230, "million shares", "year ended December 31 2025", "2025", "", "",
  (T, "", "Number of shares used in per share computation | 6,671 | 849 | 5,559 | 12,230"), "units",
  "AMBIGUOUS: Alphabet computes EPS per share class. The 'Total' column of the 2025 diluted computation (Note 12) is 12,230M. The Class A diluted count (6,671M) already includes the as-converted Class B shares, so summing A+B+C would double count. Only 12,230M accepted."),
 ("T1", "META", "2,574 million shares", 2574, "million shares", "year ended December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED STATEMENTS OF INCOME", "Diluted | 2,574 | 2,614 | 2,629"), "units", ""),
 ("T1", "AMZN", "10,827 million shares", 10827, "million shares", "year ended December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED STATEMENTS OF OPERATIONS", "Diluted | 10,492 | 10,721 | 10,827"), "units", ""),
 # ---------------- T2 period: FY2025 revenue ----------------
 ("T2", "AAPL", "$416,161 million (fiscal 2025 = year ended September 27 2025, the PRIOR-year column)", 416161, "USD millions",
  "fiscal year ended September 27 2025", "2025", "", "",
  (T, "CONSOLIDATED STATEMENTS OF OPERATIONS", "Total net sales | 478,834 | 416,161 | 391,035"), "period",
  "PERIOD TRAP: this 10-K covers fiscal 2026; fiscal 2025 is the middle column."),
 ("T2", "MSFT", "$281,724 million (fiscal 2025 = year ended June 30 2025, the PRIOR-year column)", 281724, "USD millions",
  "fiscal year ended June 30 2025", "2025", "", "",
  (T, "INCOME STATEMENTS", "Total revenue | 331,839 | 281,724 | 245,122"), "period",
  "PERIOD TRAP: this 10-K covers fiscal 2026; fiscal 2025 is the middle column."),
 ("T2", "GOOGL", "$402,836 million", 402836, "USD millions", "year ended December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED STATEMENTS OF INCOME", "Revenues | $307,394 | $350,018 | $402,836"), "period",
  "Fiscal 2025 is the most recent year here (last column)."),
 ("T2", "META", "$200,966 million", 200966, "USD millions", "year ended December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED STATEMENTS OF INCOME", "Revenue | $200,966 | $164,501 | $134,902"), "period", ""),
 ("T2", "AMZN", "$716,924 million", 716924, "USD millions", "year ended December 31 2025", "2025", "", "",
  (T, "CONSOLIDATED STATEMENTS OF OPERATIONS", "Total net sales | 574,785 | 637,959 | 716,924"), "period",
  "Fiscal 2025 is the most recent year here (last column)."),
 # ---------------- T3 period + units: non-affiliate market value ----------------
 ("T3", "AAPL", "approximately $3,647,099,000,000 as of March 27 2026", 3647099000000, "USD",
  "as of March 27 2026 (last business day of second fiscal quarter)", "2026", "", "",
  "The aggregate market value of the voting and non-voting stock held by non-affiliates of the Registrant, as of March 27, 2026, the last business day of the Registrant's most recently completed second fiscal quarter, was approximately $3,647,099,000,000.",
  "period_and_units", "PERIOD TRAP: measured at mid-year, not fiscal year-end. UNITS: stated in whole dollars."),
 ("T3", "MSFT", "$3.6 trillion as of December 31 2025", 3.6, "USD trillions", "as of December 31 2025", "2025", "", "",
  "As of December 31, 2025, the aggregate market value of the registrant's common stock held by non-affiliates of the registrant was $3.6 trillion",
  "period_and_units", "PERIOD TRAP: Microsoft's measurement date (Dec 31, 2025) falls in a different calendar year than its fiscal year-end (June 30, 2026)."),
 ("T3", "GOOGL", "approximately $1.9 trillion as of June 30 2025", 1.9, "USD trillions", "as of June 30 2025", "2025", "", "",
  "As of June 30, 2025, the aggregate market value of shares held by non-affiliates of the registrant (based upon the closing sale prices of such shares on the Nasdaq Global Select Market on June 30, 2025) was approximately $1.9 trillion.",
  "period_and_units", ""),
 ("T3", "META", "approximately $1.6 trillion as of June 30 2025", 1.6, "USD trillions", "as of June 30 2025", "2025", "", "",
  "The aggregate market value of the voting and non-voting stock held by non-affiliates of the registrant as of June 30, 2025, the last business day of the registrant's most recently completed second fiscal quarter, was approximately $1.6 trillion",
  "period_and_units", ""),
 ("T3", "AMZN", "$2,118,061,430,046 as of June 30 2025", 2118061430046, "USD", "as of June 30 2025", "2025", "", "",
  "Aggregate market value of voting stock held by non-affiliates of the registrant as of June 30, 2025 | $2,118,061,430,046",
  "period_and_units", "UNITS: whole dollars."),
 # ---------------- T4 footnote: United States revenue ----------------
 ("T4", "AAPL", "$167,746 million", 167746, "USD millions", "fiscal year ended September 26 2026", "2026", "", "",
  "U.S. | $167,746 | $151,790 | $142,196", "footnote",
  "From the country table in Note 13 (Segment Information). Do not confuse with the 'Americas' segment, which includes Canada and Latin America."),
 ("T4", "MSFT", "$170,794 million", 170794, "USD millions", "fiscal year ended June 30 2026", "2026", "", "",
  "Includes billings to OEMs and certain multinational organizations because of the nature of these businesses and the impracticability of determining the geographic source of the revenue. || Revenue, classified by the major geographic areas in which our customers were located, was as follows: || Year Ended June 30, | 2026 | 2025 | 2024 || United States (a) | $170,794 | $144,546 | $124,704",
  "footnote", "FOOTNOTE: footnote (a) qualifies the U.S. figure (includes some OEM/multinational billings). Still the reported U.S. figure."),
 ("T4", "GOOGL", "$194,229 million", 194229, "USD millions", "year ended December 31 2025", "2025", "", "",
  "United States | $146,286 | 47% | $170,447 | 49% | $194,229 | 48%", "footnote",
  "Columns 2023 | % | 2024 | % | 2025 | %. The percentage cells are a trap."),
 ("T4", "META", "$74.78 billion (U.S. only; from footnote)", 74.78, "USD billions", "year ended December 31 2025", "2025", "", "",
  "United States and Canada (1) | $78,866 | $63,207 | $52,888 || (1)United States revenue was $74.78 billion, $59.73 billion, and $49.78 billion for the years ended December 31, 2025, 2024, and 2023, respectively.",
  "footnote", "FOOTNOTE TRAP: the table row is 'United States and Canada' ($78,866M). The U.S.-only figure exists only in footnote (1). $78,866M is WRONG."),
 ("T4", "AMZN", "$489,657 million", 489657, "USD millions", "year ended December 31 2025", "2025", "", "",
  "United States | $395,637 | $438,015 | $489,657", "footnote",
  "From 'Net sales attributed to countries' (Note 10). Do not confuse with the North America segment."),
 # ---------------- T5 insufficient evidence (mixed) ----------------
 ("T5", "AAPL", "INSUFFICIENT EVIDENCE - Apple's 10-K describes no revolving credit facility", "", "", "", "", "yes", "", "", "insufficient_evidence",
  "Checked: no 'revolving' / 'credit facility' / 'credit agreement' text in the extracted filing. Apple discusses commercial paper and term debt only; citing those as a revolver balance is wrong."),
 ("T5", "MSFT", "INSUFFICIENT EVIDENCE - Microsoft's 10-K describes no revolving credit facility", "", "", "", "", "yes", "", "", "insufficient_evidence",
  "Checked: no revolving-credit-facility text in the extracted filing."),
 ("T5", "GOOGL", "$0 - no amounts borrowed under $10.0B of revolving credit facilities", 0, "USD billions", "as of December 31 2025", "2025", "", "",
  "As of December 31, 2025, we had $10.0 billion of revolving credit facilities, $4.0 billion expiring in April 2026 and $6.0 billion expiring in April 2030. No amounts have been borrowed under the credit facilities.",
  "insufficient_evidence", "Answerable (zero). The $10.0B capacity is a trap."),
 ("T5", "META", "INSUFFICIENT EVIDENCE - Meta's 10-K describes no revolving credit facility", "", "", "", "", "yes", "", "", "insufficient_evidence",
  "Checked: no revolving-credit-facility text in the extracted filing."),
 ("T5", "AMZN", "$0 - no borrowings under the two unsecured revolving credit facilities", 0, "USD billions", "as of December 31 2025", "2025", "", "",
  "We had no borrowings outstanding under the two unsecured revolving credit facilities or the commercial paper programs as of December 31, 2025.",
  "insufficient_evidence",
  "DECIDED (reviewer, 2026-11-22): $0 kept because the provided excerpt (AMZN-0073) states it for exactly the facilities the question names - the two unsecured revolving credit facilities ($15.0B Credit Agreement and $5.0B 364-day Short-Term Credit Agreement) - as of December 31, 2025, Amazon's fiscal year-end. The $455M belongs to 'other short-term credit facilities', which the question now excludes. Also excluded: a secured revolving facility terminated in 2024. Capacity figures ($15.0B, $5.0B) are traps."),
]


def table_passage(lines, title, row):
    """title || unit line || column header || row, copied verbatim from the text."""
    idx = [i for i, l in enumerate(lines) if l == row]
    if not idx:
        raise ValueError(f"row not found: {row!r}")
    r, s = idx[0], max(0, idx[0] - 25)
    if title:
        found = [(r_, i) for r_ in idx for i in range(max(0, r_ - 120), r_) if lines[i] == title]
        if not found:
            raise ValueError(f"title {title!r} not found within 120 lines above {row!r}")
        r, s = found[0][0], max(i for r_, i in found if r_ == found[0][0])
    unit = next((lines[i] for i in range(s, r) if lines[i].lower().startswith("(in ")), None)
    header = next((lines[i] for i in range(r - 1, s - 1, -1)
                   if len(YEAR.findall(lines[i])) >= 2 and len(lines[i]) < 200), None)
    segs = [x for x in (title or None, unit, header, row) if x]
    return " || ".join(segs)


def main():
    text = {}
    rows = []
    for (qid, t, exp, val, unit, period, py, abstain, alts, src, ttype, notes) in SPEC:
        if t not in text:
            text[t] = (DATA / "text" / f"{t}.txt").read_text().split("\n")
        if isinstance(src, tuple):
            passage = table_passage(text[t], src[1], src[2])
        else:
            passage = src
        rows.append({"question_id": qid, "ticker": t, "expected_answer": exp, "expected_value": val,
                     "unit": unit, "period": period, "period_year": py,
                     "expect_abstain": "yes" if abstain else "no",
                     "tolerance_rel": "0.0001" if unit == "USD per share" else "0.001",
                     "accepted_alternates": alts, "supporting_passage": passage, "tricky_type": ttype,
                     "ambiguity_notes": notes})
    with (BENCH / "answer_key.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows")


if __name__ == "__main__":
    main()
