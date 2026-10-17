SYSTEM_PROMPT = """You are a senior digital marketing strategist and SEO expert with 10 years of experience auditing brand digital presence. You analyze real website data and return structured, actionable insights.

Always respond with ONLY a valid JSON object. No preamble, no explanation, no markdown code fences. Just raw JSON."""


def build_brand_audit_prompt(brand_name, url, description, website_data=None, pagespeed_data=None):
    base_info = f"""
Brand Name: {brand_name}
Website URL: {url}
Description: {description}
"""
    real_data_section = ""
    if website_data and website_data.get('success'):
        real_data_section = f"""
REAL WEBSITE DATA scraped live from {url}:
- Page Title: {website_data.get('title', 'Not found')}
- Meta Description: {website_data.get('meta_description', 'MISSING')}
- H1 Headings: {website_data.get('h1_tags', [])}
- H2 Headings: {website_data.get('h2_tags', [])}
- Has Meta Description: {website_data.get('has_meta_description', False)}
- Has H1 Tag: {website_data.get('has_h1', False)}
- Images Missing Alt Text: {website_data.get('images_without_alt', 0)}
- Internal Links: {website_data.get('internal_link_count', 0)}
- Word Count: {website_data.get('word_count', 0)}
- Page Content: {website_data.get('page_text_preview', '')}
"""
    pagespeed_section = ""
    if pagespeed_data and pagespeed_data.get('success'):
        pagespeed_section = f"""
REAL GOOGLE PAGESPEED SCORES:
- Overall Score: {pagespeed_data.get('overall_score')}/100
- SEO Score: {pagespeed_data.get('seo_score')}/100
- Performance: {pagespeed_data.get('performance_score')}/100
- Accessibility: {pagespeed_data.get('accessibility_score')}/100
- Best Practices: {pagespeed_data.get('best_practices_score')}/100
IMPORTANT: Use {pagespeed_data.get('overall_score')} as the seo_score. Do not estimate it.
"""
    return f"""Analyze this brand using the real data provided. Return ONLY a JSON object.

{base_info}
{real_data_section}
{pagespeed_section}

Return this exact JSON:
{{
  "seo_score": <use real PageSpeed score if provided, otherwise estimate 0-100>,
  "tone_grade": <"A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", or "F">,
  "tone_description": <one sentence on brand tone based on real content>,
  "executive_summary": <2 sentences on real strengths and biggest opportunity>,
  "keyword_gaps": [
    {{"keyword": <keyword missing from page>, "competitor_using": <competitor>, "priority": <"high", "medium", or "low">, "search_intent": <one phrase describing why people search this, e.g. "users comparing laptop prices">}}
  ],
  "competitor_suggestions": [
    {{"competitor_name": <competitor>, "reason": <one sentence>}}
  ],
  "quick_wins": [<specific fix based on real issues found>],
  "seo_recommendations": [
    {{
      "issue": <short title of the problem, e.g. "Missing Meta Description">,
      "impact": <"high", "medium", or "low">,
      "what_to_fix": <one sentence describing exactly what is wrong based on real data>,
      "how_to_fix": <one to two sentences of specific actionable steps to fix it>,
      "effort": <"easy", "medium", or "hard">
    }}
  ],
  "data_quality": <"real" if you had actual data, "estimated" if guessing>
}}

Rules:
- keyword_gaps: exactly 5 items
- competitor_suggestions: exactly 3 items
- quick_wins: exactly 3 items
- seo_recommendations: exactly 5 items, each based on REAL issues found in the data above
- For seo_recommendations, look at: missing meta description, low performance score, images without alt text, H1 quality, word count, internal links, accessibility score
- Be specific — reference actual numbers and content from the real data, not generic advice
- Base everything on the real data above""" 