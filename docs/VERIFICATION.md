# Executed verification

Verified locally on 8 October 2026. Results below describe actual executed checks, not a projected checklist.

## Latest interface and sign-in update

- Added a light application design, Manrope typography, clearer sign-in layout, password visibility toggle, Google OAuth with PKCE, and an authenticated callback page.
- Landing page has a separate dark purple palette and the exact React Bits LiquidEther JS-CSS component from the requested registry, with the user's supplied settings. Its canvas is mounted exclusively on the landing route. The wrapper respects reduced motion.
- Browser checked the Google button and confirmed a readable disabled-provider message. Supabase Google provider is currently disabled; Google consent and completed Google account login remain unverified until the owner configures the provider. No Google account was created or signed into during this check.
- Mobile landing and login checked at 390 pixels: page width 375 pixels with scrollbar, no horizontal overflow. Exactly one cloud background on the landing route and zero on login. Signup retains the Google option. Password visibility control changed the password field to text.
- Google setup addresses and private credential placement are documented in `GOOGLE_SIGN_IN.md`.
- LiquidEther files were compared against the downloaded registry contents and match exactly. Three.js dependency is installed. Desktop browser found one LiquidEther canvas, no captured console errors/warnings, and no horizontal overflow. Clicking Log in navigated successfully and removed the LiquidEther canvas.
- Production build and TypeScript passed with the installed JS-CSS LiquidEther variant and the new OAuth callback route. Exact LiquidEther mobile layout checked at 390 pixels: one effect canvas, page width 375 pixels with scrollbar, no horizontal overflow. Pointer drag produced a visible purple fluid trail.

| Check | Actual result |
|---|---|
| Next.js production build | Passed; landing, dashboard, login and dynamic workspace routes compiled and rendered |
| TypeScript | Passed |
| Python suite | 28 tests passed; one upstream Starlette/httpx deprecation warning |
| Versioned SQL schema setup | Passed against local SQLite |
| Live Gemini key/model discovery | Passed; supported model list read using the supplied key |
| Live Gemini structured extraction + embedding smoke | Passed; schema validated and 768-dimensional embedding returned |
| Live Supabase settings | HTTP 200; email sign-in enabled |
| Live Supabase sign-in/account isolation | Passed after user approval: two disposable confirmed accounts; real password login, verified owner access, 404 cross-owner denial and 401 invalid token. Test accounts and workspace cleaned up |
| Browser empty workspace creation | Passed; synthetic QA workspace created through the website |
| Browser multi-file upload | Passed: PNG, 4-second MP4, narrated WAV, invoice PDF and delivery CSV uploaded through the file chooser |
| Live image understanding | Passed; actual test label and graphic described, with source segments |
| Live audio transcription | Passed; actual synthesized spoken phrase containing “bent corner” extracted |
| Live video understanding | Passed; representative observations with valid positions extracted from the actual clip; no claim of complete frame coverage |
| Live PDF/CSV | Passed; extracted PDF page, actual CSV records and real numerical statistics |
| Live cross-modal answer | Passed; returned Gemini mode and claims/citations referencing stored evidence IDs |
| Live education generation | Passed after restarting the final services; uploaded notes produced a study guide, flashcards and four-option quiz questions with valid source IDs. Temporary workspace removed |
| Browser manufacturing question + PDF citation | Passed; Gemini produced analysis and the selected reference opened page 1 of the stored maintenance PDF |
| Live PDF export | Passed; backend produced a valid PDF using stored case data; browser download event succeeded |
| Sample PDF visual review | Both one-page PDFs rendered and visually checked |
| Investigation PDF visual review | Seven pages rendered; sampled pages inspected, then heading formatting improved |
| Desktop landing | Visual check at requested 1440-pixel width; no captured console errors |
| Mobile workspace/library | Checked at 390-pixel width, page width 375 with scrollbar; no horizontal overflow; drawer navigation and source/report controls worked |

Tablet graph check at 820 pixels passed with no horizontal overflow. Final production build includes Account settings; graph search/filter controls were added. Report headings and numbered reference keys were improved and the final eight-page report rendered for visual inspection. Final regression suite remained at 28 passing tests.

Cloud deployment, production PostgreSQL and Supabase Storage mirror are prepared but not verified. Password-reset delivery and interactive profile changes were not performed on a real personal account. No real user's account/password was modified.

The final start.ps1 launch brought the frontend, API and worker online; the live education check ran successfully against those managed processes. An earlier study request returned a provider error, so provider availability and quota can still affect generation.

Seeded cases and temporary live-upload fixtures have been removed from the local database; the user-owned NIAT workspace was preserved. Anonymous access is rejected by the backend.
