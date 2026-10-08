# ClientPulse architecture

Authenticated browser → Next.js API rewrite → FastAPI authorization → tenant SQL records and private Supabase Storage → durable upload queue → worker extraction → normalized evidence → identity matching → structured complaint extraction → guarded cross-channel correlation → stored risk and alerts → source-linked UI, assistant and drafts.

A verified Supabase auth identity owns an organization; membership is stored server-side. Clients cannot choose another organization ID. This release creates one owner organization per account; shared team invitation management is not implemented.

PDF/DOCX/TXT/CSV use actual parsers. EML uses Python email parsing. Gemini Vision transcribes screenshots. Sarvam or Deepgram preserves transcript offsets and provider speaker numbers, without inventing identities. Input metadata retains actual communication dates separately from upload dates. Models treat source content as untrusted data.

Aliases match exact configured email/account/ticket identifiers; ambiguous identities require review. Cases require the same tenant, customer and category, then an explicit incident reference or compatible semantic evidence, date proximity and lexical support. Different incident IDs cannot merge. Findings link to original evidence IDs. Retries of failed files are transactional; Ready files cannot be retried into duplicate cases. Human status corrections are retained.

Scoring weights are configurable. Unresolved high severity, explicit customer cancellation, repeated follow-ups, overdue recorded deadlines, escalation, unresolved duration and recent negative statements contribute documented points capped at 100. Cases without supported complaints show insufficient evidence. Stored scores refresh after processing, corrections, setting changes and periodic worker review. Resolved cases contribute no active points.

Gemini embeddings use a 768-dimensional pgvector column on PostgreSQL. Tenant and optional customer filters apply before semantic ranking. SQLite tests store equivalent vectors as JSON; they do not verify PostgreSQL execution. Search is bounded and combines semantic and lexical support; answers disclose retrieval limits. Querying large corpora may require additional aggregate SQL tools beyond this initial assistant.

Private storage is authoritative; local files are processing caches. The worker restores missing files from Storage. API original-file requests authorize tenant ownership before issuing short-lived signed URLs. API and worker can run on separate hosts with the same database and bucket.

Drafts are saved records with source citations and human-review status; no outbound integration sends them. PDF reports are generated from saved drafts and cite supporting extracts.
