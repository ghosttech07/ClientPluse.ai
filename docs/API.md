# ClientPulse API

All private endpoints require `Authorization: Bearer <Supabase access token>`. Tenant identity is derived server-side. Missing authentication returns 401; inaccessible record IDs return 404. Errors use `detail`; provider messages omit secrets. UUID record IDs and request IDs are used throughout.

Base: `/api/v1`. OpenAPI: `/docs` on the FastAPI server.

| Method | Route | Use |
| --- | --- | --- |
| GET/POST | /customers | Paged directory / create customer |
| GET/PATCH/DELETE | /customers/{id} | Customer 360 / edit / delete related data |
| POST | /customers/{id}/aliases | Explicit email/account/ticket identity alias |
| GET | /customers/{id}/timeline | Source communication timeline |
| GET | /customers/{id}/complaints | Customer complaint cases |
| GET | /customers/{id}/risk | Explained score and contributing evidence |
| GET/POST | /uploads | Paged library / multipart files, optional customer_id and communication_at |
| GET | /uploads/{id} | Processing status, errors and extracts |
| GET | /uploads/{id}/content | Authorized private original |
| POST | /uploads/{id}/assign | Verify identity and queue analysis |
| POST | /uploads/{id}/retry | Retry failed processing |
| POST | /tickets | Manual communication queued for analysis |
| GET | /evidence/{id} | Authorized source excerpt |
| GET | /complaints | Paged cases, customer/status filters |
| PATCH | /complaints/{id} | Human status correction with required note |
| GET/PATCH | /alerts, /alerts/{id} | Paged alerts / status and owner |
| POST | /intelligence/query | Question and optional customer_id |
| GET | /intelligence/messages | Bounded conversation history, customer filter |
| GET/POST | /drafts | Paged drafts / create one from source evidence |
| PATCH | /drafts/{id} | Edit content and record Draft/Approved status |
| GET | /drafts/{id}/download | Generate a source-linked PDF |
| GET | /dashboard/summary | Live SQL metrics, trends and priorities |
| GET/PATCH | /settings | Organization, retention and risk weights |
| POST | /retention/purge | Explicit irreversible expiry cleanup |

Paged lists use offset >= 0 and limit 1–100. The initial UI loads up to 100 rows per list. Files accept at most 20 per request and 25 MB each. Uploaded HTML emails are shown as inert extracted text; scripts never execute in the evidence view. File access is never based solely on knowing a UUID.
