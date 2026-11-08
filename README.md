# BrandScan AI

**Free AI-powered SEO brand analysis — Fortune 500 clarity for any business.**

Built and deployed solo by [Daja Dowdell](https://github.com/dajadell7-blip) while finishing a CS degree.

🔗 **Live:** [brandscan.ai](https://brandscan.ai)

---

## The Story

I kept seeing the same gap: small businesses and independent brands have no real way to know if their site is showing up online. Tools like Ahrefs and SEMrush cost $500/month and require a marketing background to interpret. Free alternatives give you one number and a wall of jargon.

I wanted to build something that gave any business owner — not just SEO professionals — a clear, actionable picture of their brand's digital presence. No account. No credit card. Just paste your URL.

BrandScan AI is the result: a tool that runs real SEO checks, pulls live PageSpeed data from Google, and uses Claude AI to synthesize everything into plain-English recommendations with actual next steps.

---

## How It Works

```
User URL
   │
   ├─► Scraper (BeautifulSoup)        ─┐
   │     title, meta description,      │  concurrent.futures
   │     word count, alt text,         │  ThreadPoolExecutor
   │     heading structure             │
   │                                   │
   ├─► Google PageSpeed Insights API  ─┘
   │     performance, SEO,
   │     accessibility, best practices
   │
   └─► Both results → Claude AI (Haiku)
         keyword gaps, competitor suggestions,
         tone analysis, quick wins
              │
              ▼
         PostgreSQL  (scan history)
              │
              ▼
         Results page  (Flask + Jinja2)
```

**Parallel execution** — scraping and PageSpeed run simultaneously via `ThreadPoolExecutor`, cutting wait time ~40%.  
**Retry logic** — Claude API errors (503, connection drops) retry with exponential backoff: 2 → 4 → 8 → 16s.

---

## Features

| Feature | Details |
|---|---|
| **SEO audit** | Title tag, meta description, alt text, word count, heading structure |
| **PageSpeed scores** | Performance, accessibility, best practices — live from Google's API |
| **Keyword gap analysis** | Keywords competitors rank for that you're missing, ranked by priority |
| **Competitor detection** | AI-identified direct competitors with reasoning |
| **Tone grading** | A–F brand voice assessment with plain-English description |
| **Prioritised recommendations** | Quick wins ranked by impact so you know what to fix first |
| **Scan history** | Every audit saved to PostgreSQL, retrievable by ID |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11 · Flask · Gunicorn |
| AI | Claude Haiku (`anthropic` SDK) |
| Data | BeautifulSoup4 · Google PageSpeed Insights API |
| Database | PostgreSQL · psycopg2 |
| Frontend | Jinja2 · Vanilla JS · CSS custom properties |
| Hosting | Render |
| Security | Per-IP rate limiting · URL validation · sanitised error messages |

---

## Local Setup

```bash
git clone https://github.com/dajadell7-blip/brandscan.ai.git
cd brandscan.ai
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Create a .env file (never commit this)
cp .env.example .env
# Fill in your keys:
#   ANTHROPIC_API_KEY=
#   PAGESPEED_API_KEY=
#   DATABASE_URL=postgresql://user:pass@localhost/brandscan

flask run
# → http://localhost:5000
```

> ⚠️ **Never commit your `.env` file.** API keys stay local or in Render's environment variables only.

---

## Design Decisions

**Why Claude instead of Gemini?**  
Claude returns well-structured JSON reliably across a wide range of inputs. After testing both, Claude produced more consistent, accurate competitor and keyword analysis — especially for niche brands with limited online presence.

**Why parallel API calls?**  
Scraping and PageSpeed are completely independent. Running them sequentially added 3–4 seconds of unnecessary wait. `ThreadPoolExecutor` cuts that to whichever finishes slower.

**Why PostgreSQL over SQLite?**  
Scan history needs to survive server restarts and support a full `/history` dashboard with sorting and filtering. PostgreSQL also pairs well with Render's managed database.

**Why no account required?**  
The whole point is zero friction. The target user is a business owner, not a developer. Making them sign up before seeing value would kill the product.

---

## What's Next

- [ ] PDF export — proper branded report download
- [ ] Scheduled re-scans — weekly delta reports showing what improved
- [ ] Multi-page crawl — audit beyond just the homepage
- [ ] Email delivery — get your report in your inbox

---

## Author

**Daja Dowdell** — developer & designer  
CS graduate (May 2027) · [github.com/dajadell7-blip](https://github.com/dajadell7-blip) · [dajadell7@gmail.com](mailto:dajadell7@gmail.com)
