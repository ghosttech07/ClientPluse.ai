# Deploy ClientPulse

Frontend: deploy the Next.js app on Vercel (root apps/web, install from the workspace root). Build uses supported Next webpack after a local Turbopack CSS-worker launch failure. Set API_URL to the deployed HTTPS FastAPI origin, plus NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY. These values are required at build time. Configure Supabase Auth site URL and redirect allowlist for the deployed frontend and /auth/callback. Enable Google OAuth in Supabase if desired.

Backend: deploy services/api/Dockerfile on Render, Railway, Fly.io or another container host. Set DATABASE_URL to the Supabase session-pooler PostgreSQL connection (postgresql+psycopg scheme, SSL as appropriate). Set GEMINI_API_KEY, GEMINI_MODEL, EMBEDDING_MODEL, DEEPGRAM_API_KEY, SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_STORAGE_BUCKET=clientpulse, STORAGE_PROVIDER=supabase and WEB_ORIGINS to the frontend HTTPS origin. Do not expose the service key or provider keys in frontend variables.

Worker: deploy the same image with `python -m services.worker.main`, sharing database and Storage settings. It polls SQL status with atomic claims and recovers stale 15-minute leases. The API and worker do not require a shared local disk when using Supabase Storage; missing caches are restored from private objects. Use persistent disk for caches if helpful.

Run `python -m database.migrate` with a migration-capable database role before serving traffic. Migration 003 creates ClientPulse tables, vector column/index and tenant read policies. Supabase pgvector must be available. Do not substitute a Supabase REST API key for the database password.

No frontend/backend public deployment was provisioned automatically. No paid provider plan was activated. Live audio needs the selected Sarvam or Deepgram credentials; the selected production SQL/vector stack needs a working Supabase DATABASE_URL. Run real synthetic deployment verification after configuring these, including private originals and cross-account denial.

For a standalone local PostgreSQL development alternative, docker-compose uses pgvector/pgvector:pg17 and separate API/worker services. This is not the selected Supabase production database.
