# API reference

Open `/docs` on the backend for generated OpenAPI schemas. All data endpoints require a verified Supabase bearer token. Unauthorized or cross-owner IDs return 404. Health reveals service capability booleans, not secrets.

| Method | Path | Behavior |
|---|---|---|
| GET | `/api/health` | Service capability status |
| GET/POST | `/api/workspaces` | List own / create workspace |
| GET/PATCH/DELETE | `/api/workspaces/{id}` | Get evidence summary / edit / delete |
| GET/POST | `/api/workspaces/{id}/files` | Paginated inventory / multipart multi-file upload and queue |
| GET | `/api/files/{id}` | File detail, status and errors |
| GET | `/api/files/{id}/content` | Authorized original source or private signed URL |
| POST | `/api/files/{id}/retry` | Requeue failed/partial extraction |
| DELETE | `/api/files/{id}` | Delete file, jobs and segments |
| POST | `/api/workspaces/{id}/ask` | `{question}` → saved grounded message, citations, analysis |
| GET | `/api/workspaces/{id}/messages` | Stored conversation |
| GET | `/api/workspaces/{id}/timeline` | Source-timestamped events |
| GET | `/api/workspaces/{id}/graph` | Nodes, source-mentioned edges and evidence IDs |
| GET/POST | `/api/workspaces/{id}/reports` | List / create PDF report |
| GET | `/api/reports/{id}/download` | Authorized PDF download |
| POST | `/api/workspaces/{id}/study` | Gemini study guide, flashcards and quiz |

Upload is proxied through the authenticated API, not a two-stage signed upload flow. Formats are signature-verified where applicable. Processing is asynchronous in a separate worker. Failed AI requests do not persist fabricated assistant messages. Sources carry actual file IDs, segment IDs, pages/seconds/CSV rows when available.

