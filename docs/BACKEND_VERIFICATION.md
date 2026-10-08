# Backend reliability verification — 8 October 2026

The user flow is authenticated upload → durable processing job → extracted evidence → grounded Gemini answer → saved citations and PDF report.

## Issues corrected

- Next's rewrite proxy defaulted to 30 seconds while a provider request could take 90 seconds before fallback. The proxy now permits 180 seconds; generation has a 60-second per-model timeout, at most two models, and no hidden SDK retry multiplication. Query embeddings have a 15-second timeout.
- Live media testing timed out with the previous primary model. Its `gemini-2.5-flash` fallback returned an explicit provider error saying it was unavailable to new users. The verified primary is now `gemini-3.1-flash-lite`, with `gemini-3.8-flash` as configurable fallback. API keys remain backend-only.
- Embedding failures previously made extracted files fail or prevented questions from reaching reasoning. Extracted passages now remain available for text retrieval, with a visible metadata limitation. Failed generation still reports an error; answers are never substituted with canned results.
- Workspace list counts now come from SQL aggregation, removing a separate full-detail request for every dashboard card. Citation serialization reuses a file map. Processing polls cannot overlap and run every four seconds.
- Local SQLite connections use WAL and a 30-second busy timeout. Worker-loop failures are logged and retried instead of terminating the worker process.
- API responses include request IDs; backend logs include paths, status and elapsed time without keys, tokens or prompts. Provider/network errors have actionable messages.

## Evidence

| Check | Result |
| --- | --- |
| Isolated backend regression suite | 33 tests passed |
| Frontend TypeScript | Passed |
| Production build | Passed; all seven routes generated |
| Browser sign-in, dashboard counts, question submission and answer rendering | Passed with a temporary account |
| Browser citation viewer and Generate evidence report button | Loaded original text and generated a report |
| Real Supabase password authentication | Passed with two temporary confirmed accounts; no emails sent |
| Website proxy → authenticated API → worker | Seven disposable formats reached Ready: PDF, DOCX, TXT, CSV, PNG, WAV and MP4 |
| Multimodal extraction | Document, data, image, audio and video evidence persisted |
| CSV statistics | Values 2 and 8 produced mean 5 |
| Real Gemini question and saved citations | Passed; one measured answer took 4.6 seconds through the website proxy |
| Conversation persistence | Saved user question and assistant answer |
| Graph and timeline | Returned source nodes and dated CSV events |
| Education study generation | Returned real generated flashcards |
| PDF report and original source access | Passed |
| Cross-account access | Denied workspace, source and report access |

Test fixtures are generated temporarily for QA and removed with their test workspaces/accounts. The audio fixture is a two-second tone, so this run does not establish speech-transcription quality. Timing is one measured request, not a latency guarantee. Provider quotas, outages and input complexity remain external constraints; files exceeding configured size/duration limits are rejected explicitly. Local process testing does not certify a deployed multi-server SaaS environment.

Reproduce the full live check with backend credentials configured: set `QA_FULL_PIPELINE=1` and `QA_API_BASE=http://127.0.0.1:3000`, then run `python -m tests.smoke_supabase`. It creates/deletes temporary accounts and workspace data, so it is opt-in. Regular regression tests use isolated local storage and do not contact Gemini or Supabase.
