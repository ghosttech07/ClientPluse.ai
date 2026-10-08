# Executed verification — ClientPulse AI

Verified locally on 8 October 2026. This records actual checks, not a public deployment claim.

- Next.js production build with webpack passed, including TypeScript and all static/dynamic routes. Windows sandbox folder permissions required the build to run outside the sandbox.
- Backend integration suite passed. Tests isolate SQL records and mock external providers, covering tenant isolation, supported uploads, exact identity matching, correlation, resolutions, human corrections, retry idempotency, invalid citations, risk/settings, email extraction and speech segment metadata.
- Live Sarvam Saaras v4 transcribed a labelled synthetic WAV recording and returned chunk timestamps and a speaker label.
- Full live check used real Supabase Auth, private Supabase Storage, Sarvam and Gemini. A WAV call, EML email and PNG screenshot all reached Ready. Explicit spoken order normalization connected order 1042 with ORD-1042 while unrelated references stay distinct.
- Those three communications formed one delivery-delay case with three linked interactions. An explicit conditional cancellation statement produced a cancellation alert; risk was 95/Critical from stored factors.
- Gemini assistant citations belonged to the selected customer. A real follow-up draft and a PDF download were generated. The last assistant response took 16.6 seconds; an earlier check took 3.3 seconds. These are observations, not a latency guarantee or load benchmark.
- A second temporary Supabase account received 404 for the first account’s customer and original files. Both confirmed QA accounts and their synthetic records/files were removed afterwards. No emails were sent.
- Browser checked landing, sign-in, dashboard, customer profile and source viewer. A source citation displayed the actual extracted screenshot wording and a private original-file link. Mobile landing checked at 390 px, with content width equal to viewport width and working navigation to the distinct workflow section.
- Original LiquidEther background, independent globe, motion header highlight and SpecularButton remain on the landing page. Dashboard controls use a lightweight CSS sheen. Background is absent on application routes. Reduced-motion preferences are respected.

## Not yet verified

The full disposable live workflow was rerun successfully on Supabase PostgreSQL: real Sarvam WAV transcription, email and screenshot processing, a single correlated case, 95/Critical risk, cancellation alert, customer-scoped cited Gemini answer, draft and PDF. The answer took 6.3 seconds in that run. Cross-account original-file/customer access was denied, and temporary QA accounts and data were cleaned up. The isolated regression suite also passed all 18 tests after removing implicit local fallback.

Supabase PostgreSQL is now the active application database. Migration preserved one legacy workspace, 23 audit entries, one ClientPulse organization and one member; all source rows were compared with copied rows. TLS, vector extension, HNSW index and RLS on all 15 ClientPulse tables were verified. Deepgram is an optional adapter with mocked checks; Sarvam is the live-tested transcription provider. Completed Google OAuth consent, public hosting, long multi-speaker Hindi recordings, concurrent load and tenant scale have not been tested in this run.

Screenshots in this directory are real local UI captures. Dashboard/profile captures used explicitly labelled temporary synthetic QA records; the landing graphic is an illustrative workflow rather than customer data.
