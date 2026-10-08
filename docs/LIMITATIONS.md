# Implementation boundaries

This is a functional local MVP with a configured provider path, not a claim that every production feature in the master brief has been completed.

## Credential-dependent features

Gemini generation, semantic embeddings, scanned-page OCR, image observation, audio transcription, video understanding and education generation require a real Gemini API key and enabled model quota. Supabase account lifecycle and private storage mirror require configured projects. Tests mock external providers; a live provider smoke check is included and must be run after keys are set. No cloud deployment has been verified.

## Deliberate MVP differences

- SQLite default and optional PostgreSQL. No pgvector query/index implementation: embeddings are persisted in JSON and compared in Python. This is suitable for small workspaces, not large collections.
- SQL processing queue with a 15-minute lease, single worker recommended. Redis/RQ is not implemented. Long jobs beyond the lease need heartbeat renewal before multiple workers are enabled.
- Owner-only account authorization, not shared workspace collaboration or membership invitations.
- Workspace is the case/collection. Separate nested cases, account deletion and advanced organization settings are not implemented. Profile name, password reset and account sign-out are available.
- Source entity mention graph; no inferred causal graph or arbitrary entity-resolution system. Timeline includes explicitly extracted CSV dates or media positions; document prose dates are not automatically promoted to events.
- Gemini processes short video directly rather than a custom adaptive FFmpeg frame/audio pipeline. Video duration must be checked with installed ffprobe. Sampled video understanding is incomplete. Media is limited to 25 MB; large uploads and long clips need multipart object uploads, provider Files API and a separate cost-control workflow.
- Native scanned-page OCR uses Gemini; no offline OCR engine. DOCX has no reliable page coordinates, so citations open a download and extracted passage.
- Chat responses are returned after validation, not streamed. Report creation and chat execute in backend worker threads. Reports are persisted; no asynchronous report-job queue.
- Education study guides/quizzes are generated on request and held in the current page session. Scores/flashcards are not persisted as separate learning records.
- Insurance and E-commerce specialize the same evidence workflow and prompts; dedicated repair estimate comparison and order/claim metadata panels are not implemented.
- No built-in demo photo/audio/video. Exact staged-media requirements are in the asset checklist. Provided PDFs, CSV and statements are actual files processed by the real pipeline.
- The library endpoint supports pagination, but workspace overview fetches all file metadata and up to 500 segments; very large workspaces need UI pagination and server aggregates.
- API rate limits are process-local. Production requires a shared gateway limiter, malware scanning, encrypted disk/storage backups, monitoring and retention policy.
- Prompt rules, typed output and source-ID validation reduce prompt injection risk; this is not a guarantee that a model cannot misinterpret malicious source text. Review outputs.
- Private Supabase mirrored files still require a shared persistent local processing volume. Reports currently remain on that volume.

All unsupported or missing-provider behavior must remain visible. Never replace a failed extraction with an invented observation, guessed timestamp, or canned diagnosis.
