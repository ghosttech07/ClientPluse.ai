# Backend audit — 8 October 2026

## Verified
- 29 provider-mocked regression tests passed, including tenant isolation, citation validation, saved questions on failure, conversation memory, correction memory, attachment scope, chat deletion, share revocation, rename validation and retention cleanup.
- Live authenticated synthetic customer flow passed through the running frontend proxy: Supabase sign-in/onboarding, private storage, Sarvam WAV transcription, email parsing, Gemini screenshot extraction, correlated complaints, risk calculation, cancellation alert, cited answers, follow-up draft and PDF export.
- Live authenticated PDF chat passed: private upload, Gemini PDF reading, follow-up reference recall, rename, public text snapshot, deletion, link revocation and attachment deletion.
- Temporary QA accounts and tenant records were removed.
- PostgreSQL migration versions 1, 3, 4, 5 and 6 present; chat attachment and thread tables have row-level security enabled.
- Backend syntax compilation passed.

## Fixes made during this audit
- Missing risk rows serialize safely instead of raising an exception.
- Chat deletion removes unreferenced private attachments.
- Customer deletion removes its private chat attachment files and revokes organization shared snapshots, preventing retained deleted information.
- Retention removes expired chat attachment files and revokes existing organization shared snapshots.
- Failed attachment persistence rolls back records and cleans up newly saved files where storage is reachable.

## Limits
This is evidence of tested behavior, not a guarantee of perfection. Gemini/Sarvam/Supabase outages, quota restrictions, model mistakes and network timeouts remain external failure modes. Automated stress/load testing, crash recovery under process termination, independent security review and disaster recovery/backup restoration were not performed. General web search previously returned quota errors; its ongoing availability depends on the provider account. Remote storage cleanup can fail during an outage and needs operational monitoring. Deleting customer data or applying retention deliberately revokes all organization shared snapshots to avoid retained source copies.
