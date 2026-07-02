"""
Run this to see exactly what's failing in Step 2.
python debug_step2.py
"""
import sys, os, json
sys.path.insert(0, '.')
from config.settings import DATABASE_URL, OPENAI_API_KEY, OPENAI_MODEL
from models import init_db, get_session_factory, NewsArticle
from openai import OpenAI

print("=" * 60)
print("STEP 2 DEBUG")
print("=" * 60)

# 1. Check DB
engine = init_db(DATABASE_URL)
Session = get_session_factory(engine)
with Session() as s:
    articles = s.query(NewsArticle).filter_by(is_processed=False).limit(1).all()
    print(f"\n[1] Unprocessed articles in DB: {s.query(NewsArticle).filter_by(is_processed=False).count()}")
    if not articles:
        print("    ERROR: No unprocessed articles found!")
        sys.exit(1)
    art = articles[0]
    print(f"    Using article: [{art.id}] {art.title[:60]}")

# 2. Check OpenAI key
print(f"\n[2] OpenAI key set: {'YES (' + OPENAI_API_KEY[:8] + '...)' if OPENAI_API_KEY and OPENAI_API_KEY != 'sk-your-openai-key-here' else 'NO - KEY MISSING!'}")

# 3. Test raw OpenAI call
print(f"\n[3] Testing OpenAI API call...")
try:
    client = OpenAI(api_key=OPENAI_API_KEY)
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        max_tokens=500,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "Extract market events. Return JSON array under key 'events'. Each item must have: event_text, event_type, entities (array)."},
            {"role": "user", "content": f"Article: {art.title}\n\n{art.summary or ''}"}
        ],
    )
    raw = resp.choices[0].message.content
    print(f"    Raw response: {raw[:300]}")
    parsed = json.loads(raw)
    print(f"    Parsed type: {type(parsed)}")
    print(f"    Parsed keys (if dict): {list(parsed.keys()) if isinstance(parsed, dict) else 'N/A'}")
    
    # unwrap
    result = []
    if isinstance(parsed, list):
        result = [i for i in parsed if isinstance(i, dict)]
    elif isinstance(parsed, dict):
        for v in parsed.values():
            if isinstance(v, list):
                result = [i for i in v if isinstance(i, dict)]
                break
    print(f"    Events extracted: {len(result)}")
    if result:
        print(f"    First event: {result[0]}")
    else:
        print("    WARNING: 0 events extracted - check unwrap logic above!")

except Exception as e:
    print(f"    FAILED: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("If you see events above, run: python pipeline.py --run-once")
print("If you see an error, share it here for the fix.")
print("=" * 60)