# EVIDENCE.AI

Every Format. One Intelligence.

A responsive Next.js website with a FastAPI backend for persistent, source-linked investigation workspaces. The application supports Manufacturing, Education, Insurance, and E-commerce through a shared ingestion and retrieval engine.

## What works

- Responsive landing page with an interactive React Three Fiber neural sphere and reduced-motion fallback.
- Workspace creation, search, editing, and deletion; separate evidence, messages, graphs, timelines, and reports per workspace.
- Real multi-file uploads with progress, MIME/signature verification, 25 MB limits, a durable background queue, errors, retries, and source previews.
- PDF text with page references; scanned-page OCR using Gemini; DOCX paragraphs/tables; UTF-8 text; CSV statistics, missing values and 3-sigma outlier counts calculated from actual records.
- Configurable Gemini image observation, timestamped audio transcription, and short-video analysis. No identity inference; no fabricated event dates. FFmpeg validates video duration.
- Gemini embeddings and hybrid retrieval; keyword retrieval remains available without a provider key. Local mode returns matching passages and explicitly does **not** pretend to provide an AI diagnosis.
- Structured Gemini cross-source reasoning, uncertainty, consistency checks, and source-ID validation. Chat history and export.
- Cited PDF page, media position, image, text and CSV row previews.
- Source-mentioned entity graph with evidence references; timestamp-only event timeline; CSV charts.
- PDF reports using stored evidence and saved findings.
- Source-grounded flashcards, quizzes with score and retry, and study guides (Gemini required).
- Supabase signup, login, logout, password recovery/update, profile settings and account session handling when configured.

## Architecture and stack

Next.js 16 / React 19 / TypeScript / CSS design tokens / Lucide / React Three Fiber / React Flow / Recharts / safe Markdown. The frontend proxies `/api` to FastAPI. SQLAlchemy stores metadata in SQLite for zero-service local setup, or PostgreSQL through `DATABASE_URL`. The SQL queue is polled by a separate Python process. PyMuPDF, python-docx and standard-library CSV/statistics perform local extraction; Google Gen AI SDK handles configured multimodal understanding and embeddings. ReportLab produces PDFs.

The implementation uses CSS instead of Tailwind/shadcn for a coherent bespoke visual system, SQL leases instead of Redis for a simple durable single-worker MVP, and JSON embedding vectors plus cosine search instead of a pgvector query index at this scale. These are deliberate simplifications; see [limitations](docs/LIMITATIONS.md) for differences from the full master brief.

## Prerequisites

Node.js 22+, npm, Python 3.11+, and FFmpeg/ffprobe for videos. A Gemini API key enables AI reasoning, embeddings, image/audio/video analysis and scanned PDF OCR. Supabase is required for real accounts. Do not expose secret provider or service-role keys in browser environment settings.

## Install on Windows

From `E:\evidence.ai`:

```powershell
npm install
python -m venv .venv
python -m pip --python .venv install -r services/api/requirements.txt
```

If you prefer a normal virtual environment pip, use `.\.venv\Scripts\python.exe -m pip install -r services/api/requirements.txt`.

The `.env` and `apps/web/.env.local` files have been created with blank key fields. Fill them in, then **restart the API, worker and frontend** after any credential changes. `.env` is a file, not a folder.

## Environment

| Variable | Location | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | root `.env` | Secret server-only Gemini key |
| `GEMINI_MODEL` | root `.env` | Model ID; default `gemini-3.1-flash-lite`, verified with live text and media requests; configurable fallback `gemini-3.8-flash` |
| `EMBEDDING_MODEL` | root `.env` | Default `gemini-embedding-001`; 768 dimensions |
| `SUPABASE_URL` | root `.env` | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | root `.env` | Publishable/anon key used to verify Auth users |
| `DATABASE_URL` | root `.env` | Default SQLite; production `postgresql+psycopg://...` |
| `DATA_DIR` | root `.env` | Private persistent uploads/reports; shared by API and worker |
| `STORAGE_PROVIDER` | root `.env` | `local` or `supabase` |
| `SUPABASE_SERVICE_ROLE_KEY` | root `.env` | Secret backend-only key for optional private storage mirror |
| `SUPABASE_STORAGE_BUCKET` | root `.env` | Private bucket name, default `evidence` |
| `WEB_ORIGINS` | root `.env` | Comma-separated production frontend origins |
| `NEXT_PUBLIC_SUPABASE_URL` | `apps/web/.env.local` | Same Supabase URL, for browser Auth |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `apps/web/.env.local` | Same public/anon key, never a service-role key |
| `API_URL` | `apps/web/.env.local` | Backend destination, default `http://127.0.0.1:8000` |

Create a Supabase project, enable email/password authentication and add `http://127.0.0.1:3000/dashboard` and `http://127.0.0.1:3000/login` as allowed redirect URLs (and production equivalents). Supabase handles passwords; this application stores no passwords. Backend Auth validates bearer sessions through Supabase `/auth/v1/user` on every authenticated request.

For Supabase storage, create a **private** `evidence` bucket. Set `STORAGE_PROVIDER=supabase` and the service-role key on the backend. Files are mirrored to owner/workspace-specific keys. The API authorizes ownership before issuing 120-second signed URLs. Keep a persistent local volume mounted in API and worker for processing. Private mirror and signed URL integration are implemented but require live credentials to verify.

## Start

Conveniently run `./start.ps1`. It starts the three services with hidden helper windows and writes logs in `data/logs`. To stop only those saved processes, run `./stop.ps1`.

Or use three terminals from the project root:

```powershell
# Backend
.\.venv\Scripts\python.exe -m uvicorn services.api.main:app --host 127.0.0.1 --port 8000
# Background worker
.\.venv\Scripts\python.exe -m services.worker.main
# Website
npm run dev
```

Open [the local website](http://127.0.0.1:3000) and [API documentation](http://127.0.0.1:8000/docs).

The worker must run; uploading alone queues a file. Files remain Queued until the worker claims them. Failed files retain a visible error and can be retried after fixing configuration. PDF/image/audio/video extraction and indexing must finish before Ready is set. External AI calls execute in the worker or a FastAPI thread, not in the browser.

## Database

SQLite tables are created on startup. PostgreSQL can use the same SQLAlchemy schema. For explicit versioned schema setup run `python -m database.migrate` using the project virtual environment. It records applied SQLAlchemy schema versions. See `database/migrations/001_initial.sql` for the equivalent PostgreSQL DDL and `002_supabase_policies.sql` for optional Supabase RLS/storage hardening. Restrict the backend database connection to a server role; do not allow clients to write through PostgREST.

## Real uploads

Sign in, create a workspace, and upload your own evidence. Extraction, answers, and reports use those uploaded sources.

## Checks

```powershell
npm run typecheck
npm run build
.\.venv\Scripts\python.exe -m pytest tests -q --basetemp=data/pytest-temp
# Opt-in real provider check after adding Gemini credentials:
.\.venv\Scripts\python.exe -m tests.smoke_gemini
# Opt-in live five-modality check after uploading the clearly labeled QA fixtures:
.\.venv\Scripts\python.exe -m tests.live_pipeline
# With explicit permission to create and remove disposable Supabase accounts:
.\.venv\Scripts\python.exe -m tests.smoke_supabase
```

External providers are mocked in automated tests. The real smoke script fails with an explicit missing-key message rather than pretending success. See `docs/VERIFICATION.md` for actual executed results.

## Deploy

Google sign-in is available through Supabase OAuth. Enable the Google provider and configure the client credentials and redirect addresses described in [Google sign-in setup](docs/GOOGLE_SIGN_IN.md). Google OAuth secrets belong in Supabase's provider settings, never in browser environment variables.

Frontend: Vercel, root directory `apps/web`, build `npm run build`; configure the public Supabase settings and `API_URL` pointing to an HTTPS Python backend. Set public settings before building. Backend: Docker/Python host with a persistent volume at `/app/data`, PostgreSQL, and the same env settings for API and worker. Require authenticated access, restrict origins, provide secrets privately and use HTTPS. Docker Compose provides a local PostgreSQL + API + worker deployment.

No cloud deployment is performed or claimed in this build. PostgreSQL, Supabase Auth/storage and live Gemini require service setup and live verification. See [deployment](docs/DEPLOYMENT.md), [security](docs/SECURITY.md), [architecture](docs/ARCHITECTURE.md), [API](docs/API.md).
