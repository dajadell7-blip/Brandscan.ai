from flask import Flask, request, jsonify, render_template, abort
from flask_cors import CORS
from google import genai
from google.genai.errors import ServerError
import json
import os
import time
import re
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps
from collections import defaultdict
from dotenv import load_dotenv
from prompts import SYSTEM_PROMPT, build_brand_audit_prompt
from database import save_scan_result, get_scan_by_id
from scraper import scrape_website, get_pagespeed_score

load_dotenv()

app = Flask(__name__)

# ── CORS (restrict to same origin in production) ─────────────────────────────
CORS(app, resources={r"/api/*": {"origins": os.getenv("ALLOWED_ORIGINS", "*")}})

# ── Gemini client ─────────────────────────────────────────────────────────────
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

# ── In-memory rate limiter (per IP, resets per minute) ───────────────────────
_rate_counts  = defaultdict(list)  # ip → [timestamps]
RATE_LIMIT    = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))

def rate_limited(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        ip  = request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0].strip()
        now = time.time()
        # prune timestamps older than 60 s
        _rate_counts[ip] = [t for t in _rate_counts[ip] if now - t < 60]
        if len(_rate_counts[ip]) >= RATE_LIMIT:
            return jsonify({"error": "Too many requests — please wait a moment."}), 429
        _rate_counts[ip].append(now)
        return f(*args, **kwargs)
    return wrapper


# ── URL validator ─────────────────────────────────────────────────────────────
def validate_url(url: str) -> str:
    """Return a normalised URL or raise ValueError."""
    if not url:
        raise ValueError("URL is required.")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    if not parsed.netloc or "." not in parsed.netloc:
        raise ValueError("Please enter a valid URL (e.g. https://example.com).")
    # block private / loopback ranges
    blocked = ("localhost", "127.", "192.168.", "10.", "0.0.0.0")
    if any(parsed.netloc.startswith(b) for b in blocked):
        raise ValueError("That URL isn't publicly accessible.")
    return url


# ── Gemini with exponential-backoff retry on 503 ─────────────────────────────
def call_gemini(prompt: str, retries: int = 4) -> str:
    delay = 2.0
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=SYSTEM_PROMPT + '\n\n' + prompt
            )
            return response.text.strip()
        except ServerError as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e).upper():
                if attempt < retries - 1:
                    print(f"Gemini 503 — retrying in {delay:.0f}s (attempt {attempt+1}/{retries})")
                    time.sleep(delay)
                    delay *= 2  # exponential backoff: 2 → 4 → 8 → 16
                    continue
            raise  # not a 503, or out of retries
    raise RuntimeError("Gemini is currently overloaded. Please try again in a minute.")


# ── Clean AI JSON response ────────────────────────────────────────────────────
def parse_ai_json(raw: str) -> dict:
    # strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw.strip())


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/results/<scan_id>')
def results(scan_id):
    # Basic scan_id sanitisation
    if not re.match(r'^[a-zA-Z0-9_-]{1,64}$', scan_id):
        abort(404)
    try:
        row = get_scan_by_id(scan_id)
    except Exception:
        abort(404)

    ai       = row.get('raw_ai_response', {}) or {}
    pagespeed = ai.get('pagespeed', {})
    scraped   = ai.get('scraped_data', {})

    # SEO checks
    seo_checks = [
        {
            'name':   'Title tag present',
            'status': 'pass' if scraped.get('title') else 'fail',
            'value':  scraped.get('title', '—'),
        },
        {
            'name':   'Meta description present',
            'status': 'pass' if scraped.get('has_meta_description') else 'fail',
            'value':  scraped.get('meta_description', 'Missing') or 'Missing',
        },
        {
            'name':   'Images with alt text',
            'status': ('pass' if scraped.get('images_without_alt', 0) == 0
                       else 'warn' if scraped.get('images_without_alt', 0) < 10
                       else 'fail'),
            'value':  f"{scraped.get('images_without_alt', 0)} missing alt attributes",
        },
        {
            'name':   'Word count',
            'status': 'pass' if scraped.get('word_count', 0) > 300 else 'warn',
            'value':  f"{scraped.get('word_count', 0)} words",
        },
    ]
    for rec in ai.get('seo_recommendations', []):
        seo_checks.append({
            'name':   rec.get('issue', ''),
            'status': 'fail' if rec.get('impact') == 'high' else 'warn',
            'value':  rec.get('what_to_fix', ''),
        })

    keyword_gaps = [
        {
            'keyword':    kw.get('keyword', ''),
            'competitor': kw.get('competitor_using', ''),
            'priority':   kw.get('priority', 'medium'),
            'intent':     kw.get('search_intent', ''),
        }
        for kw in ai.get('keyword_gaps', [])
    ]

    competitors = [
        {'name': c.get('competitor_name', ''), 'reason': c.get('reason', '')}
        for c in ai.get('competitor_suggestions', [])
    ]

    recommendations = []
    for win in ai.get('quick_wins', []):
        recommendations.append({'title': win, 'description': '', 'impact': 'high', 'effort': 'easy'})
    for rec in ai.get('seo_recommendations', []):
        recommendations.append({
            'title':       rec.get('issue', ''),
            'description': rec.get('how_to_fix', ''),
            'impact':      rec.get('impact', 'medium'),
            'effort':      rec.get('effort', 'medium'),
        })

    return render_template('results.html',
        brand_name            = row.get('brand_name', ''),
        url                   = row.get('url', ''),
        scan_id               = scan_id,
        timestamp             = row.get('scanned_at', ''),
        seo_score             = pagespeed.get('seo', ai.get('seo_score', 0)),
        performance_score     = pagespeed.get('performance', 0),
        accessibility_score   = pagespeed.get('accessibility', 0),
        best_practices_score  = pagespeed.get('best_practices', 0),
        tone_grade            = ai.get('tone_grade', '—'),
        tone_summary          = ai.get('tone_description', ''),
        executive_summary     = ai.get('executive_summary', ''),
        keyword_gaps          = keyword_gaps,
        competitors           = competitors,
        recommendations       = recommendations,
        seo_checks            = seo_checks,
        keyword_gap_count     = len(keyword_gaps),
        competitor_count      = len(competitors),
        recommendation_count  = len(recommendations),
    )


@app.route('/loading/<scan_id>')
def loading(scan_id):
    if not re.match(r'^[a-zA-Z0-9_-]{1,64}$', scan_id):
        abort(404)
    return render_template('loading.html', scan_id=scan_id)


@app.route('/api/scan', methods=['POST'])
@rate_limited
def scan_brand():
    try:
        data = request.get_json(silent=True) or {}
        brand_name  = str(data.get('brand_name', '')).strip()[:200]
        url         = str(data.get('url', '')).strip()[:500]
        description = str(data.get('description', '')).strip()[:1000]

        if not brand_name:
            return jsonify({'error': 'Brand name is required.'}), 400

        try:
            url = validate_url(url)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

        # ── Parallel scrape + PageSpeed ───────────────────────────────────────
        with ThreadPoolExecutor(max_workers=2) as pool:
            fut_scrape = pool.submit(scrape_website, url)
            fut_psi    = pool.submit(get_pagespeed_score, url)
            website_data  = fut_scrape.result()
            pagespeed_data = fut_psi.result()

        print(f"Scrape: {'OK – ' + str(website_data.get('word_count')) + ' words' if website_data.get('success') else website_data.get('error')}")
        print(f"PageSpeed: {'score ' + str(pagespeed_data.get('overall_score')) if pagespeed_data.get('success') else pagespeed_data.get('error')}")

        # ── Gemini with retry ─────────────────────────────────────────────────
        prompt     = build_brand_audit_prompt(brand_name, url, description,
                                              website_data=website_data,
                                              pagespeed_data=pagespeed_data)
        raw_response = call_gemini(prompt)
        ai_result    = parse_ai_json(raw_response)

        # Attach scraped + pagespeed for results route
        ai_result['scraped_data'] = {
            'title':               website_data.get('title', '') if website_data.get('success') else '',
            'meta_description':    website_data.get('meta_description', '') if website_data.get('success') else '',
            'word_count':          website_data.get('word_count', 0) if website_data.get('success') else 0,
            'has_meta_description':website_data.get('has_meta_description', False) if website_data.get('success') else False,
            'images_without_alt':  website_data.get('images_without_alt', 0) if website_data.get('success') else 0,
        }
        if pagespeed_data.get('success'):
            ai_result['pagespeed'] = {
                'seo':            pagespeed_data.get('seo_score'),
                'performance':    pagespeed_data.get('performance_score'),
                'accessibility':  pagespeed_data.get('accessibility_score'),
                'best_practices': pagespeed_data.get('best_practices_score'),
            }

        scan_id = save_scan_result(brand_name, url, description, ai_result)
        return jsonify({'success': True, 'scan_id': scan_id, 'result': ai_result})

    except json.JSONDecodeError:
        return jsonify({'error': 'AI returned an unexpected format — please try again.'}), 500
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 503
    except Exception as e:
        print(f"Scan error: {e}")
        return jsonify({'error': 'Something went wrong. Please try again.'}), 500


@app.route('/api/scan/<scan_id>', methods=['GET'])
def get_scan(scan_id):
    if not re.match(r'^[a-zA-Z0-9_-]{1,64}$', scan_id):
        return jsonify({'error': 'Not found.'}), 404
    try:
        return jsonify(get_scan_by_id(scan_id))
    except Exception:
        return jsonify({'error': 'Scan not found.'}), 404


if __name__ == '__main__':
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug, port=5000)
