# Architecture

```mermaid
flowchart LR
  Browser[Responsive Next.js website] --> Proxy[Next.js API proxy]
  Proxy --> API[FastAPI authorization and validation]
  API --> Auth[Supabase Auth user verification]
  API --> DB[(SQLite / PostgreSQL)]
  API --> Private[(Private upload volume)]
  API --> Mirror[Optional Supabase private bucket]
  DB --> Worker[SQL job worker]
  Worker --> Extract[PDF / DOCX / text / CSV extraction]
  Worker --> Gemini[Gemini media understanding and embeddings]
  Extract --> DB
  Gemini --> DB
  API --> Retrieval[Workspace-filtered hybrid retrieval]
  Retrieval --> Reasoning[Validated cited Gemini output]
  Reasoning --> DB
  DB --> Reports[PDF report generation]
```

Processing flow: upload signature/size validation → private storage → SQL job → lease claim → extraction → sentence chunking → optional embeddings → source-linked segments → Indexed → Ready or Partially Processed. Errors become Failed; retry replaces prior segments transactionally. A stale processing lease is recovered after 15 minutes.

```mermaid
erDiagram
  WORKSPACES ||--o{ FILES : contains
  FILES ||--o{ PROCESSING_JOBS : queues
  FILES ||--o{ EVIDENCE_SEGMENTS : yields
  WORKSPACES ||--o{ EVIDENCE_SEGMENTS : scopes
  WORKSPACES ||--o{ MESSAGES : contains
  WORKSPACES ||--o{ GENERATED_REPORTS : exports
  WORKSPACES ||--o{ AUDIT_EVENTS : tracks
```

Entities/relationships and timeline events are derived from evidence segments; citations and validated reasoning are persisted on messages. Embeddings are stored with segments as JSON. User identities come from Supabase rather than custom password records. Optional policies prevent direct frontend database reads. The implemented schema intentionally omits separate duplicated content, entity and conversation tables at MVP scale.
