"""Opt-in live provider smoke test. Run with a configured root .env. Does not fake success."""
from dotenv import load_dotenv
load_dotenv()
from services.worker.ai import available,generate,Extraction,embed
if not available():raise SystemExit('Not run: GEMINI_API_KEY is missing.')
result=generate('Extract this synthetic customer statement: Order ORD-1042 has not arrived. Cause unknown. No timestamp supplied.',Extraction)
assert result.items and result.items[0].content
vectors=embed([result.items[0].content]);assert vectors and len(vectors[0])==768
print('Live Gemini structured output and embedding smoke test passed.')
