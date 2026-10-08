# Current implementation boundaries

ClientPulse uses real customer uploads and provider responses. Dashboard data is never automatically seeded. The labelled synthetic fixtures are opt-in inputs, processed through the same pipeline.

- The application now uses Supabase PostgreSQL through its TLS session pooler. Existing SQLite records were backed up, copied and verified. The vector extension, HNSW index and tenant RLS policies are present. SQLite remains only an explicit isolated test/development option and an offline migration backup.
- Sarvam Saaras v4 batch transcription is integrated and has passed a live synthetic audio check. Deepgram Nova-3 remains a selectable alternative; its adapter is tested with mocked provider responses, but no live Deepgram key is configured.
- Gemini handles screenshot transcription, scanned PDF OCR, complaint reasoning, cited answers, drafts and embeddings. Output remains uncertain and must be reviewed against source evidence. Similar customer names never establish identity.
- Risk is an automatic evidence-based heuristic, not a calibrated churn prediction model. Promises and conditional cancellation threats are distinguished from completed resolutions and cancellations.
- The SQL queue uses a 15-minute job lease. Sarvam polling is capped at 8 minutes. A single worker is recommended until lease renewal and long-job stress testing are added.
- One owner organization is created per Supabase account. Team invitations, shared role administration, billing subscriptions, CRM connectors and live call streaming are not implemented.
- Initial dashboard lists show up to 100 records; API endpoints support pagination. Large-tenant pagination UI and load testing remain deployment work.
- Text redaction covers common payment-number and credential patterns; original media is not comprehensively anonymized. This is not a regulatory compliance certification.
- Retention is configurable with an explicit purge action. Drafts are editable and require human approval; nothing sends email automatically. Approved follow-up emails can be explicitly sent through Resend after reviewing the recipient. A verified sender domain is required; provider acceptance does not confirm inbox delivery.
- No public hosting deployment or PostgreSQL production load test has been completed. Existing legacy data remains intact; obsolete active screens and endpoints were removed.
