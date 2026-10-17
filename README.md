# BrandScan AI

**AI-powered brand audit tool** — paste a URL, get a real SEO score, keyword gaps, competitor analysis, and Gemini AI recommendations in under 60 seconds.

Built by [Daja Dowdell](https://github.com/dajadell7-blip)

---

## The Problem

Small brands and freelancers don't have $500/month for Ahrefs or SEMrush. They need to know if their site is findable — fast — without a marketing degree. Existing free tools give you one score and a wall of jargon. Nothing synthesises SEO, performance, content tone, and competitor gaps into one actionable report.

## The Solution

BrandScan AI runs four data sources in parallel, hands the combined output to Gemini, and returns a structured audit with prioritised recommendations — all in a single page visit.

---

## How It Works

```
User URL
   │
   ├─► Scraper (BeautifulSoup)       ─┐
   │     title, meta, word count,     │  concurrent.futures
   │     alt text, headings           │  ThreadPoolExecutor
   │                                  │
   ├─► Google PageSpeed Insights API ─┘
   │     performance, SEO,
   │     accessibility, best practices
   │
   └─► Both results → Gemini 2.0 Flash
         keyword gaps, competitor suggestions,
         tone analysis, quick wins
              │
              ▼
         PostgreSQL  (scan history)
              │
              ▼
         Results page  (Flask + Jinja2)
```

**Retry logic** — Gemini 503s retry with exponential backoff (2 → 4 → 8 → 16 s).  
**Parallel calls** — Scrape + PageSpeed run simultaneously, cutting wait time ~40%.

---

## Features

| | |
|---|---|
| **SEO audit** | Title, meta description, alt text, word count, heading structure |
| **PageSpeed scores** | Performance, accessibility, best practices via Google API |
| **Keyword gap analysis** | Keywords competitors rank for that you're missing |
| **Competitor detection** | AI-identified direct competitors with reasoning |
| **Tone grading** | A–F brand voice assessment with plain-English description |
| **Prioritised recommendations** | Quick wins ranked by impact × effort |
| **Scan history** | Every audit saved to PostgreSQL, retrievable by ID |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11 · Flask · Gunicorn |
| AI | Google Gemini 2.0 Flash (`google-genai`) |
| Data | BeautifulSoup4 · Google PageSpeed Insights API |
| Database | PostgreSQL · psycopg2 |
| Frontend | Jinja2 · Vanilla JS · CSS custom properties |
| Design system | Linear-inspired light theme · WCAG AA contrast |
| Security | Per-IP rate limiting · URL validation · sanitised error messages |

---

## Local Setup

```bash
git clone https://github.com/dajadell7-blip/Brandscan.ai.git
cd Brandscan.ai
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Fill in GEMINI_API_KEY, PAGESPEED_API_KEY, DATABASE_URL

flask run
# → http://localhost:5000
```

**.env keys required:**
```
GEMINI_API_KEY=
PAGESPEED_API_KEY=
DATABASE_URL=postgresql://user:pass@localhost/brandscan
```

---

## Design Decisions

**Why Gemini instead of GPT-4?** Gemini 2.0 Flash returns structured JSON reliably and is fast enough for a synchronous web request.

**Why parallel API calls?** Scraping and PageSpeed are independent — running them sequentially added ~3 s of unnecessary wait. `ThreadPoolExecutor` cuts that to whichever is slower.

**Why PostgreSQL over SQLite?** Scan history needs to survive restarts and eventually support a `/history` dashboard with full-text search.

**Why a custom light theme?** Most audit tools use dark dashboards. The warm canvas (`#e8e3da`) + white card system makes reports polished enough to screenshot for a client.

---

## What's Next

- [ ] `/history` route — paginated scan history
- [ ] Cloudflare Tunnel — public URL without hosting costs
- [ ] PDF export — proper print stylesheet
- [ ] Scheduled re-scans — weekly delta reports
- [ ] Multi-page crawl — audit beyond the homepage

---

## Author

**Daja Dowdell** — designer & developer  
[github.com/dajadell7-blip](https://github.com/dajadell7-blip) · [dajadell7@gmail.com](mailto:dajadell7@gmail.com)
