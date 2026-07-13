# Ledger — AI Personal Finance Assistant

An AI-powered personal finance assistant that categorizes bank transactions, generates plain-English financial summaries, and answers natural-language questions about spending — all while keeping the LLM out of any actual math.

**Live demo:** [magenta-rabanadas-8b0ed4.netlify.app](https://magenta-rabanadas-8b0ed4.netlify.app/)
**API docs (Swagger):** [finance-assistant-qsrh.onrender.com/docs](https://finance-assistant-qsrh.onrender.com/docs)

> The backend runs on Render's free tier, which spins down after inactivity. The first request after a period of idle time may take 30–60 seconds while the server wakes up.

---

## What it does

- **Categorizes transactions** — batches unique transaction descriptions into a single Gemini call, mapping each to one of 11 categories (Food, Transport, Shopping, Bills, Rent, Income, etc.)
- **Generates financial summaries** — pandas computes every number (totals, savings rate, monthly trends, top merchants); Gemini only explains those pre-computed numbers in plain English and never performs its own calculations
- **Answers natural-language questions** — a two-step pipeline where Gemini classifies user intent into structured JSON, then a Python router calls the matching pandas function to produce the actual answer
- **Frontend accepts plain English** — type something like *"I spent ₹450 on Swiggy and got ₹5000 salary"* and the transactions are parsed and logged automatically, no forms required (CSV upload is also supported as an alternative)

---

## Architecture

```
User (browser)
      │
      ▼
Frontend (static HTML/JS, hosted on Netlify)
      │  fetch() calls
      ▼
FastAPI backend (hosted on Render)
      │
      ├── routers/finance.py       → HTTP endpoints, no business logic
      ├── services/gemini_service.py → all Gemini calls (categorize, summarize, ask)
      ├── services/analytics_service.py → all pandas calculations
      ├── models/schemas.py        → Pydantic request/response shapes
      └── utils/json_helpers.py    → cleans markdown-wrapped JSON from LLM responses
      │
      ▼
Google Gemini API (gemini-2.5-flash, REST)
```

**Core design principle:** Gemini never does math. Every number in a response is computed by pandas first; Gemini's only job is categorization, natural-language explanation, and intent classification — never arithmetic. This keeps the numbers trustworthy regardless of what the LLM generates.

---

## Why these specific technical choices

**REST API instead of the `google-genai` SDK.**
The SDK pulled in a `pydantic` version that conflicted with Kaggle's pre-installed packages (`ImportError: cannot import name 'iter_union_choices' from pydantic_core.core_schema`). Rather than fight the dependency graph, the project calls Gemini's REST endpoint directly with `requests` — fewer moving parts, no SDK version to manage.

**Batch categorization instead of one call per transaction.**
Gemini's free tier caps out at ~20 requests/day. Categorizing row-by-row would exhaust that in minutes on any real dataset. Instead, unique transaction descriptions are deduplicated and sent in a single batched prompt, which returns a JSON mapping (`{"SWIGGY BANGALORE": "Food", ...}`) applied across the whole dataset with `df.map()`. A 300-row statement costs roughly 12 requests instead of 300.

**Amounts are always positive; direction lives in a separate `type` field.**
Rather than encoding debit/expense as negative numbers, every transaction has `amount` (always ≥ 0) and `type` (`"debit"` or `"credit"`). This makes every pandas filter explicit and readable (`df[df["type"] == "debit"]`) instead of relying on sign conventions that are easy to get backwards.

**Retry logic with exponential backoff on every Gemini call.**
`call_gemini_with_retry()` retries on HTTP 429 with increasing wait times (5s, 10s, 15s) before giving up and returning a graceful fallback message. No user-facing request ever surfaces a raw traceback from a rate-limited API call.

---

## Project structure

```
finance-assistant/
├── app/
│   ├── main.py                    # FastAPI app instance, CORS, router registration
│   ├── routers/
│   │   └── finance.py             # /categorize, /summary, /ask, /health endpoints
│   ├── services/
│   │   ├── gemini_service.py      # Gemini REST calls + retry logic
│   │   └── analytics_service.py   # compute_analytics() — all pandas math
│   ├── models/
│   │   └── schemas.py             # Pydantic models for request/response validation
│   └── utils/
│       └── json_helpers.py        # strips markdown fences from LLM JSON responses
├── requirements.txt
├── Dockerfile
└── .env                           # GEMINI_API_KEY (not committed)
```

---

## API endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `POST` | `/categorize` | Returns each transaction mapped to a category |
| `POST` | `/summary` | Returns an AI-generated financial health report |
| `POST` | `/ask` | Accepts a natural-language question, returns a computed answer |

All `POST` endpoints expect a `transactions` object shaped as:

```json
{
  "transactions": {
    "dates": ["2026-07-13"],
    "descriptions": ["Swiggy"],
    "amounts": [450],
    "types": ["debit"]
  }
}
```

`/ask` additionally requires a `question` field at the same top level.

Full interactive documentation (with a "Try it out" button for every endpoint) is available at [`/docs`](https://finance-assistant-qsrh.onrender.com/docs).

---

## Running locally

```bash
git clone https://github.com/snehach03/Finance_Assistant.git
cd Finance_Assistant

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_key_here
```

Run the server:
```bash
uvicorn app.main:app --reload
```

Visit `http://127.0.0.1:8000/docs` to test the API directly.

---

## Deployment

- **Backend:** Render (free tier), auto-deploys from GitHub on every push to `main`. Environment variables (including `GEMINI_API_KEY`) are set directly in Render's dashboard, never committed to the repo.
- **Frontend:** a single static HTML/CSS/JS file, deployed on Netlify.

---

## Known limitations

- **Gemini free tier: ~20 requests/day, 5 requests/minute.** The app degrades gracefully (returns a clear "AI service is temporarily busy" message) rather than crashing when the quota is exhausted, but real answers aren't available once the daily limit is hit.
- **Render's free tier spins down after ~15 minutes of inactivity.** The first request after idle time is slow while the instance wakes up.
- **The frontend's natural-language transaction parser is heuristic**, not LLM-based — it handles clear patterns like *"spent ₹X on Y"* well, but unusual phrasing may not parse correctly. CSV upload is available as a more reliable alternative for larger datasets.

---

## Tech stack

**Backend:** Python, FastAPI, pandas, Pydantic, Google Gemini API (REST)
**Frontend:** Vanilla HTML/CSS/JS (no framework, no build step)
**Deployment:** Render (backend), Netlify (frontend)
