import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

def scrape_website(url):
    if not url.startswith('http'):
        url = 'https://' + url
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string if soup.title else ''
        meta_tag = soup.find('meta', attrs={'name': 'description'})
        meta_desc = meta_tag.get('content', '') if meta_tag else ''
        h1_tags = [h.get_text(strip=True) for h in soup.find_all('h1')]
        h2_tags = [h.get_text(strip=True) for h in soup.find_all('h2')][:8]
        for script in soup(['script', 'style', 'nav', 'footer']):
            script.decompose()
        page_text = soup.get_text(separator=' ', strip=True)[:3000]
        all_links = soup.find_all('a', href=True)
        internal_links = [l for l in all_links if url.split('/')[2] in str(l['href']) or str(l['href']).startswith('/')]
        images_without_alt = len([img for img in soup.find_all('img') if not img.get('alt')])
        return {
            'success': True,
            'url': url,
            'title': title,
            'meta_description': meta_desc,
            'h1_tags': h1_tags,
            'h2_tags': h2_tags,
            'page_text_preview': page_text,
            'internal_link_count': len(internal_links),
            'has_meta_description': bool(meta_desc),
            'has_h1': len(h1_tags) > 0,
            'images_without_alt': images_without_alt,
            'word_count': len(page_text.split())
        }
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Website took too long to respond'}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'error': 'Could not reach the website'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_pagespeed_score(url):
    if not url.startswith('http'):
        url = 'https://' + url
    api_key = os.getenv('GOOGLE_API_KEY')
    api_url = 'https://www.googleapis.com/pagespeedonline/v5/runPagespeed'
    params = {
        'url': url,
        'key': api_key,
        'strategy': 'mobile',
        'category': ['performance', 'seo', 'accessibility', 'best-practices']
    }
    try:
        response = requests.get(api_url, params=params, timeout=30)
        data = response.json()
        categories = data.get('lighthouseResult', {}).get('categories', {})
        performance = round(categories.get('performance', {}).get('score', 0) * 100)
        seo = round(categories.get('seo', {}).get('score', 0) * 100)
        accessibility = round(categories.get('accessibility', {}).get('score', 0) * 100)
        best_practices = round(categories.get('best-practices', {}).get('score', 0) * 100)
        overall_score = round((seo * 0.40) + (performance * 0.30) + (accessibility * 0.15) + (best_practices * 0.15))
        return {
            'success': True,
            'overall_score': overall_score,
            'seo_score': seo,
            'performance_score': performance,
            'accessibility_score': accessibility,
            'best_practices_score': best_practices
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}
