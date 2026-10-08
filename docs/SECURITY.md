# Security and privacy

The API verifies Supabase bearer tokens using Auth's user endpoint. Every workspace route resolves the owner, and source/report routes authorize their parent workspace. SQL retrieval always scopes by workspace. A random UUID is not treated as authorization.

Default local uploads and reports have no static public URL. The authenticated API serves private content with nosniff and no-store. Optional Supabase mirror uses private bucket paths with user/workspace IDs and short-lived signed URLs after authorization. Service-role and Gemini secrets stay in root `.env`, never browser bundles. Never assign a secret to a `NEXT_PUBLIC_` variable.


Inputs have length bounds; files have extension, signature, decoding and size checks; DOCX ZIP sizes are bounded. Worker uses ffprobe with an argument array and timeout, not a shell. Evidence is never executed. Typed model outputs reference only retrieved source IDs; invalid citation IDs are rejected. The model is instructed to treat source text as untrusted and distinguish observations, interpretations and missing information. Source ID validation proves traceability, not factual correctness.

Deleting sources removes associated extracted segments and jobs. Deleting a workspace removes sources, messages and PDFs. Audit metadata contains actions/IDs, not uploaded content. Logs avoid evidence text or secret values. API process-local rate limit allows 90 requests/minute per IP; multi-instance production needs gateway/shared rate limiting.

Production hardening still required: shared quotas and upload throttles, antivirus/ZIP bomb limits for all parsers, resource isolation, database backups, TLS, encrypted persistent storage, operational alerting, retention rules, membership model if sharing is added, and review of all external providers. Do not claim a security certification.
All workspace, upload, chat, study, report and file endpoints require a verified Supabase session. Anonymous workspace access is unavailable.
