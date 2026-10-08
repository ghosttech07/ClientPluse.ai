# ClientPulse AI

Detect customer dissatisfaction before it becomes customer churn.

ClientPulse connects customer calls, emails, screenshots, tickets and documents into source-backed complaint cases, transparent risk factors, alerts and draft follow-ups. Dashboard values come from SQL records. A promise to fix a problem is not a resolution; risk scores are automatic evidence-based review heuristics, not churn probabilities.

## Stack

Next.js, TypeScript, Tailwind CSS, Recharts; Python FastAPI, Pydantic and SQLAlchemy; Supabase Auth, PostgreSQL, private Storage and pgvector; Sarvam Saaras v4 (or Deepgram Nova-3) for audio; Gemini Vision, structured complaint reasoning and 768-dimensional embeddings. Gemini is the selected reasoning option; Groq is not required or integrated. No Hugging Face billing is needed for this stack.

## Local setup

1. Install Node.js 22+, Python 3.12+ and uv (or use pip in a normal Python environment).
2. Run `npm install` at the repository root.
3. Create the Python environment: `uv venv .venv`, then `uv pip install --python .venv/Scripts/python.exe -r services/api/requirements.txt` on Windows. Linux uses `.venv/bin/python`.
4. Copy `.env.example` to `.env` and fill the backend credentials. Never commit this file.
5. Set `DATABASE_URL` to the Supabase PostgreSQL connection string using the `postgresql+psycopg://` scheme. Use the session pooler on an IPv4-only host; URL-encode the password. A Supabase API service-role key is not a PostgreSQL password.
6. Create a private Supabase Storage bucket named `clientpulse` with a 25 MB size limit. Set STORAGE_PROVIDER=supabase.
7. Set SPEECH_PROVIDER=sarvam and add SARVAM_API_KEY plus GEMINI_API_KEY. Deepgram is an alternative with SPEECH_PROVIDER=deepgram and DEEPGRAM_API_KEY. Audio fails explicitly when the selected provider is not configured.
8. In `apps/web/.env.local`, set NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY and API_URL=http://127.0.0.1:8000. These public variables never contain service keys.
9. Apply `python -m database.migrate`. PostgreSQL migration installs vector support and tenant read policies. Alternatively apply `database/migrations/003_clientpulse.sql` in Supabase SQL Editor. Use a backend database role allowed to perform the migration.
10. Start Windows services with `./start.ps1`. Open http://127.0.0.1:3000. Stop with `./stop.ps1`.

For separate terminals: `python -m uvicorn services.api.main:app --port 8000`, `python -m services.worker.main`, and `npm run dev`. API and worker use the same database and bucket. The worker can restore its processing cache from private Storage when its local file is missing.

SQLite can be used for isolated development and tests with DATABASE_URL=sqlite:///./data/evidence.db and STORAGE_PROVIDER=local. This does not satisfy or verify the requested production Supabase PostgreSQL/pgvector configuration.

The current application is connected to Supabase PostgreSQL with TLS, private Storage and pgvector. There is no implicit SQLite fallback. To migrate another existing local database, stop API and worker, configure the Supabase DATABASE_URL, then run `python -m scripts.migrate_to_supabase --source data/evidence.db`. The tool saves a SQLite backup, refuses conflicting cloud records and verifies all copied rows before committing. Restart both services afterwards. Credentials and backups stay out of Git.

## Use the product

After first sign-in, enter a company name on the required setup page. Company setup is enforced by the API as well as the frontend. Subsequent sign-ins open the existing workspace. The workspace logo opens the dashboard; the account menu shows the user's name, email and company with a sign-out option. Already signed-in users bypass the login page. Customer risk is updated automatically from AI-analyzed evidence and resolution status; manual risk-weight controls are not available.

Sign in with Supabase Auth. Create a customer with an exact email/account identifier. Upload communications, optionally supplying their actual communication date. Unknown identities go to human review. Wait for Ready, then inspect the customer’s linked cases, risk factors and timeline. Ask the assistant a customer-scoped question and click source citations. Generate a follow-up or report, edit it, and approve it for your own use. Nothing is sent automatically.

Supported core inputs: PDF, DOCX, TXT, CSV, EML, PNG/JPG/WEBP and MP3/WAV. Manually entered tickets use the same background pipeline. Scanned PDFs use Gemini for OCR. Upload and analysis failures are visible and retryable. Private originals are retrieved after server-side authorization.

## Synthetic demonstration

`fixtures/clientpulse` contains 12 fictional customer definitions, 20 tickets, 12 emails, 8 chat screenshots, 5 spoken synthetic WAV files and 5 PDFs. Inputs are labelled; no analysis results are seeded. Two customers have neutral communications and insufficient complaint evidence. Three accounts have cross-channel recurring issues; two have explicit cancellation statements.

For Acme, upload call-01.wav (Oct 3), email-01.eml (Oct 5), and chat-01.png (Oct 7), assigning them to the same customer. They share ORD-1042. Expected: one linked delivery case, three interactions, an escalation/cancellation signal, an explained risk score, and a draft follow-up.

An explicit importer is available: `python -m scripts.import_clientpulse_demo --user-id YOUR_AUTH_USER_UUID`. It creates labelled synthetic customers and queues the three flagship files for real processing. Add `--all-files` to queue all 50 inputs. It does not run automatically or bypass authentication.

Regenerate fixtures on Windows with `python -m scripts.generate_clientpulse_data`; local speech synthesis creates labelled spoken audio. Costs for processing synthetic inputs depend on configured providers.

## Checks

`python -m pytest tests -q` runs provider-mocked integration tests. `npm run typecheck` and `npm run build` verify the web app. `python -m tests.live_clientpulse` is an opt-in synthetic live test that creates and deletes two confirmed Supabase QA accounts without sending emails; run only with explicit authorization. It verifies sign-in, storage, correlation, risk, source filtering, Gemini answers, drafts and PDF generation. Without a key for the selected speech provider it uses the labelled transcript and explicitly leaves audio unverified.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Versioned API](docs/API.md); live OpenAPI at http://127.0.0.1:8000/docs
- [Deployment](docs/DEPLOYMENT.md)
- [Security](docs/SECURITY.md)
- [Verification and remaining limitations](docs/VERIFICATION.md)

The previous Evidence.ai UI, domain-specific APIs, study mode and graph screens have been retired. Legacy schema definitions/migrations and original user data remain intact to avoid destructive migration. New customer records live in cp_* tables. The existing GitHub repository remains the delivery location.
