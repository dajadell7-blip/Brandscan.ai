import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(os.getenv('DATABASE_URL'))

def save_scan_result(brand_name, url, description, ai_result):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute(
            "INSERT INTO users (email, name) VALUES (%s, %s) ON CONFLICT (email) DO UPDATE SET name=EXCLUDED.name RETURNING id",
            ('demo@brandscan.ai', 'Demo User')
        )
        user_id = cur.fetchone()['id']
        cur.execute(
            "INSERT INTO brand_scans (user_id, brand_name, url, description) VALUES (%s, %s, %s, %s) RETURNING id",
            (user_id, brand_name, url, description)
        )
        scan_id = cur.fetchone()['id']
        cur.execute(
            "INSERT INTO audit_results (scan_id, seo_score, tone_grade, executive_summary, raw_ai_response) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (scan_id, ai_result['seo_score'], ai_result['tone_grade'], ai_result['executive_summary'], psycopg2.extras.Json(ai_result))
        )
        result_id = cur.fetchone()['id']
        for kw in ai_result.get('keyword_gaps', []):
            cur.execute(
                "INSERT INTO keyword_suggestions (result_id, keyword, competitor_using, priority) VALUES (%s, %s, %s, %s)",
                (result_id, kw['keyword'], kw['competitor_using'], kw['priority'])
            )
        for comp in ai_result.get('competitor_suggestions', []):
            cur.execute(
                "INSERT INTO competitor_suggestions (result_id, competitor_name, reason) VALUES (%s, %s, %s)",
                (result_id, comp['competitor_name'], comp['reason'])
            )
        conn.commit()
        return str(scan_id)
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def get_scan_by_id(scan_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute(
            """SELECT bs.brand_name, bs.url, bs.scanned_at,
                      ar.seo_score, ar.tone_grade, ar.executive_summary, ar.raw_ai_response
               FROM brand_scans bs
               JOIN audit_results ar ON bs.id = ar.scan_id
               WHERE bs.id = %s""",
            (scan_id,)
        )
        return dict(cur.fetchone())
    finally:
        cur.close()
        conn.close()
