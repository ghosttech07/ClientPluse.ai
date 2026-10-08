# Security and privacy

Supabase Auth validates sessions server-side; only positively verified sessions have a short cache (up to 10 seconds, never beyond token expiry). Organization membership and tenant predicates are applied in every API lookup and assistant query. PostgreSQL migration enables tenant SELECT RLS; browser writes must go through the authenticated backend. Backend credentials must use a trusted server role and never appear in NEXT_PUBLIC variables.

The clientpulse Storage bucket is private. Backend service credentials perform writes, reads and deletion; authorized original-file requests receive short-lived signed URLs. Anyone holding a signed URL can use it until expiration. Do not make the bucket public. The API limits formats and sizes and uses random stored filenames. MIME/container validation, document decompression limits and Pillow image verification reduce malformed upload risks. This is not a malware scanning service.

Only data you are authorized to process should be uploaded. Customer communications can be sent to Gemini and the selected Sarvam/Deepgram provider for processing. The UI discloses provider processing. Optional common payment-number/password redaction applies before text reasoning and embedding; original binary media and original files are not comprehensively anonymized. Do not treat this as a complete DLP or regulatory compliance solution.

Audit records log user, tenant, action and record ID; request logs omit tokens and source bodies. Secrets belong in ignored backend env files or deployment secret stores. Google OAuth secrets belong in Supabase provider configuration.

Deletion removes related SQL records, original Storage objects and processing caches, plus drafts/history that copied deleted evidence and cached reports. Processing records cannot be deleted mid-job. Retention cleanup is explicit and destructive, with an in-product confirmation. Automatic scheduled purging is not enabled; schedule the documented owner-authorized purge operationally if required.

LLM prompts treat source text as untrusted, separate customer/employee claims, validate citation IDs, and keep outbound actions as drafts. Source checking and human corrections remain necessary. The configurable risk score is a prioritization heuristic, not a statistically validated churn prediction.

Deployment needs HTTPS, private network/database credentials, backups, monitoring, a reviewed retention schedule and provider agreements appropriate for the data. In-memory request throttling is a single-process baseline; distributed deployments should add a shared rate limiter.
