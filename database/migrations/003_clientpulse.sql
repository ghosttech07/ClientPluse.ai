-- ClientPulse PostgreSQL schema. Apply in Supabase SQL Editor or run database.migrate.

CREATE EXTENSION IF NOT EXISTS vector;


CREATE TABLE IF NOT EXISTS cp_organizations (
	owner_id VARCHAR(64) NOT NULL,
	name VARCHAR(160) NOT NULL,
	settings JSON NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at VARCHAR(40) NOT NULL,
	updated_at VARCHAR(40) NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (owner_id)
)

;

ALTER TABLE cp_organizations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_read ON cp_organizations;

CREATE POLICY tenant_read ON cp_organizations FOR SELECT TO authenticated USING (owner_id = auth.uid()::text);


CREATE TABLE IF NOT EXISTS cp_audit_events (
	user_id VARCHAR(64) NOT NULL,
	action VARCHAR(80) NOT NULL,
	record_id VARCHAR(36),
	organization_id VARCHAR(36) NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at VARCHAR(40) NOT NULL,
	updated_at VARCHAR(40) NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(organization_id) REFERENCES cp_organizations (id) ON DELETE CASCADE
)

;

CREATE INDEX IF NOT EXISTS ix_cp_audit_events_organization_id ON cp_audit_events (organization_id);

ALTER TABLE cp_audit_events ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_read ON cp_audit_events;

CREATE POLICY tenant_read ON cp_audit_events FOR SELECT TO authenticated USING (EXISTS (SELECT 1 FROM cp_users member WHERE member.organization_id = cp_audit_events.organization_id AND member.auth_id = auth.uid()::text));


CREATE TABLE IF NOT EXISTS cp_customers (
	name VARCHAR(160) NOT NULL,
	email VARCHAR(255),
	account_ref VARCHAR(100),
	status VARCHAR(30) NOT NULL,
	owner VARCHAR(160) NOT NULL,
	notes TEXT NOT NULL,
	synthetic BOOLEAN NOT NULL,
	organization_id VARCHAR(36) NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at VARCHAR(40) NOT NULL,
	updated_at VARCHAR(40) NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(organization_id) REFERENCES cp_organizations (id) ON DELETE CASCADE
)

;

CREATE INDEX IF NOT EXISTS ix_cp_customers_organization_id ON cp_customers (organization_id);

ALTER TABLE cp_customers ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_read ON cp_customers;

CREATE POLICY tenant_read ON cp_customers FOR SELECT TO authenticated USING (EXISTS (SELECT 1 FROM cp_users member WHERE member.organization_id = cp_customers.organization_id AND member.auth_id = auth.uid()::text));


CREATE TABLE IF NOT EXISTS cp_users (
	organization_id VARCHAR(36) NOT NULL,
	auth_id VARCHAR(64) NOT NULL,
	role VARCHAR(20) NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at VARCHAR(40) NOT NULL,
	updated_at VARCHAR(40) NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(organization_id) REFERENCES cp_organizations (id) ON DELETE CASCADE,
	UNIQUE (auth_id)
)

;

CREATE INDEX IF NOT EXISTS ix_cp_users_organization_id ON cp_users (organization_id);

ALTER TABLE cp_users ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_read ON cp_users;

CREATE POLICY tenant_read ON cp_users FOR SELECT TO authenticated USING (auth_id = auth.uid()::text);


CREATE TABLE IF NOT EXISTS cp_complaints (
	customer_id VARCHAR(36) NOT NULL,
	category VARCHAR(50) NOT NULL,
	description TEXT NOT NULL,
	reference VARCHAR(100),
	severity VARCHAR(20) NOT NULL,
	status VARCHAR(20) NOT NULL,
	uncertainty TEXT NOT NULL,
	human_status VARCHAR(20),
	organization_id VARCHAR(36) NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at VARCHAR(40) NOT NULL,
	updated_at VARCHAR(40) NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(customer_id) REFERENCES cp_customers (id) ON DELETE CASCADE,
	FOREIGN KEY(organization_id) REFERENCES cp_organizations (id) ON DELETE CASCADE
)

;

CREATE INDEX IF NOT EXISTS ix_cp_complaints_customer_id ON cp_complaints (customer_id);

CREATE INDEX IF NOT EXISTS ix_cp_complaints_organization_id ON cp_complaints (organization_id);

CREATE INDEX IF NOT EXISTS ix_cp_complaints_category ON cp_complaints (category);

ALTER TABLE cp_complaints ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_read ON cp_complaints;

CREATE POLICY tenant_read ON cp_complaints FOR SELECT TO authenticated USING (EXISTS (SELECT 1 FROM cp_users member WHERE member.organization_id = cp_complaints.organization_id AND member.auth_id = auth.uid()::text));


CREATE TABLE IF NOT EXISTS cp_customer_aliases (
	customer_id VARCHAR(36) NOT NULL,
	kind VARCHAR(30) NOT NULL,
	value VARCHAR(255) NOT NULL,
	organization_id VARCHAR(36) NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at VARCHAR(40) NOT NULL,
	updated_at VARCHAR(40) NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (organization_id, kind, value),
	FOREIGN KEY(customer_id) REFERENCES cp_customers (id) ON DELETE CASCADE,
	FOREIGN KEY(organization_id) REFERENCES cp_organizations (id) ON DELETE CASCADE
)

;

CREATE INDEX IF NOT EXISTS ix_cp_customer_aliases_organization_id ON cp_customer_aliases (organization_id);

CREATE INDEX IF NOT EXISTS ix_cp_customer_aliases_customer_id ON cp_customer_aliases (customer_id);

ALTER TABLE cp_customer_aliases ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_read ON cp_customer_aliases;

CREATE POLICY tenant_read ON cp_customer_aliases FOR SELECT TO authenticated USING (EXISTS (SELECT 1 FROM cp_users member WHERE member.organization_id = cp_customer_aliases.organization_id AND member.auth_id = auth.uid()::text));


CREATE TABLE IF NOT EXISTS cp_customer_risk_scores (
	customer_id VARCHAR(36) NOT NULL,
	score INTEGER,
	category VARCHAR(30) NOT NULL,
	factors JSON NOT NULL,
	version VARCHAR(30) NOT NULL,
	organization_id VARCHAR(36) NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at VARCHAR(40) NOT NULL,
	updated_at VARCHAR(40) NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (customer_id),
	FOREIGN KEY(customer_id) REFERENCES cp_customers (id) ON DELETE CASCADE,
	FOREIGN KEY(organization_id) REFERENCES cp_organizations (id) ON DELETE CASCADE
)

;

CREATE INDEX IF NOT EXISTS ix_cp_customer_risk_scores_organization_id ON cp_customer_risk_scores (organization_id);

ALTER TABLE cp_customer_risk_scores ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_read ON cp_customer_risk_scores;

CREATE POLICY tenant_read ON cp_customer_risk_scores FOR SELECT TO authenticated USING (EXISTS (SELECT 1 FROM cp_users member WHERE member.organization_id = cp_customer_risk_scores.organization_id AND member.auth_id = auth.uid()::text));


CREATE TABLE IF NOT EXISTS cp_generated_drafts (
	customer_id VARCHAR(36),
	kind VARCHAR(40) NOT NULL,
	title VARCHAR(200) NOT NULL,
	content TEXT NOT NULL,
	citations JSON NOT NULL,
	status VARCHAR(20) NOT NULL,
	organization_id VARCHAR(36) NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at VARCHAR(40) NOT NULL,
	updated_at VARCHAR(40) NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(customer_id) REFERENCES cp_customers (id) ON DELETE CASCADE,
	FOREIGN KEY(organization_id) REFERENCES cp_organizations (id) ON DELETE CASCADE
)

;

CREATE INDEX IF NOT EXISTS ix_cp_generated_drafts_organization_id ON cp_generated_drafts (organization_id);

CREATE INDEX IF NOT EXISTS ix_cp_generated_drafts_customer_id ON cp_generated_drafts (customer_id);

ALTER TABLE cp_generated_drafts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_read ON cp_generated_drafts;

CREATE POLICY tenant_read ON cp_generated_drafts FOR SELECT TO authenticated USING (EXISTS (SELECT 1 FROM cp_users member WHERE member.organization_id = cp_generated_drafts.organization_id AND member.auth_id = auth.uid()::text));


CREATE TABLE IF NOT EXISTS cp_messages (
	customer_id VARCHAR(36),
	role VARCHAR(20) NOT NULL,
	content TEXT NOT NULL,
	citations JSON NOT NULL,
	organization_id VARCHAR(36) NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at VARCHAR(40) NOT NULL,
	updated_at VARCHAR(40) NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(customer_id) REFERENCES cp_customers (id) ON DELETE CASCADE,
	FOREIGN KEY(organization_id) REFERENCES cp_organizations (id) ON DELETE CASCADE
)

;

CREATE INDEX IF NOT EXISTS ix_cp_messages_organization_id ON cp_messages (organization_id);

CREATE INDEX IF NOT EXISTS ix_cp_messages_customer_id ON cp_messages (customer_id);

ALTER TABLE cp_messages ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_read ON cp_messages;

CREATE POLICY tenant_read ON cp_messages FOR SELECT TO authenticated USING (EXISTS (SELECT 1 FROM cp_users member WHERE member.organization_id = cp_messages.organization_id AND member.auth_id = auth.uid()::text));


CREATE TABLE IF NOT EXISTS cp_uploaded_files (
	customer_id VARCHAR(36),
	name VARCHAR(255) NOT NULL,
	mime VARCHAR(100) NOT NULL,
	source_type VARCHAR(30) NOT NULL,
	path TEXT NOT NULL,
	size INTEGER NOT NULL,
	communication_at VARCHAR(40),
	status VARCHAR(30) NOT NULL,
	error TEXT,
	meta JSON NOT NULL,
	lease_at VARCHAR(40),
	organization_id VARCHAR(36) NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at VARCHAR(40) NOT NULL,
	updated_at VARCHAR(40) NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(customer_id) REFERENCES cp_customers (id) ON DELETE CASCADE,
	FOREIGN KEY(organization_id) REFERENCES cp_organizations (id) ON DELETE CASCADE
)

;

CREATE INDEX IF NOT EXISTS ix_cp_uploaded_files_organization_id ON cp_uploaded_files (organization_id);

CREATE INDEX IF NOT EXISTS ix_cp_uploaded_files_customer_id ON cp_uploaded_files (customer_id);

CREATE INDEX IF NOT EXISTS ix_cp_uploaded_files_status ON cp_uploaded_files (status);

ALTER TABLE cp_uploaded_files ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_read ON cp_uploaded_files;

CREATE POLICY tenant_read ON cp_uploaded_files FOR SELECT TO authenticated USING (EXISTS (SELECT 1 FROM cp_users member WHERE member.organization_id = cp_uploaded_files.organization_id AND member.auth_id = auth.uid()::text));


CREATE TABLE IF NOT EXISTS cp_ai_analysis_runs (
	upload_id VARCHAR(36) NOT NULL,
	model VARCHAR(160) NOT NULL,
	version VARCHAR(30) NOT NULL,
	output JSON NOT NULL,
	organization_id VARCHAR(36) NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at VARCHAR(40) NOT NULL,
	updated_at VARCHAR(40) NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(upload_id) REFERENCES cp_uploaded_files (id) ON DELETE CASCADE,
	FOREIGN KEY(organization_id) REFERENCES cp_organizations (id) ON DELETE CASCADE
)

;

CREATE INDEX IF NOT EXISTS ix_cp_ai_analysis_runs_organization_id ON cp_ai_analysis_runs (organization_id);

CREATE INDEX IF NOT EXISTS ix_cp_ai_analysis_runs_upload_id ON cp_ai_analysis_runs (upload_id);

ALTER TABLE cp_ai_analysis_runs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_read ON cp_ai_analysis_runs;

CREATE POLICY tenant_read ON cp_ai_analysis_runs FOR SELECT TO authenticated USING (EXISTS (SELECT 1 FROM cp_users member WHERE member.organization_id = cp_ai_analysis_runs.organization_id AND member.auth_id = auth.uid()::text));


CREATE TABLE IF NOT EXISTS cp_alerts (
	customer_id VARCHAR(36) NOT NULL,
	complaint_id VARCHAR(36) NOT NULL,
	kind VARCHAR(40) NOT NULL,
	severity VARCHAR(20) NOT NULL,
	title VARCHAR(200) NOT NULL,
	status VARCHAR(20) NOT NULL,
	owner VARCHAR(160) NOT NULL,
	evidence_ids JSON NOT NULL,
	organization_id VARCHAR(36) NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at VARCHAR(40) NOT NULL,
	updated_at VARCHAR(40) NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(customer_id) REFERENCES cp_customers (id) ON DELETE CASCADE,
	FOREIGN KEY(complaint_id) REFERENCES cp_complaints (id) ON DELETE CASCADE,
	FOREIGN KEY(organization_id) REFERENCES cp_organizations (id) ON DELETE CASCADE
)

;

CREATE INDEX IF NOT EXISTS ix_cp_alerts_customer_id ON cp_alerts (customer_id);

CREATE INDEX IF NOT EXISTS ix_cp_alerts_organization_id ON cp_alerts (organization_id);

CREATE INDEX IF NOT EXISTS ix_cp_alerts_complaint_id ON cp_alerts (complaint_id);

ALTER TABLE cp_alerts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_read ON cp_alerts;

CREATE POLICY tenant_read ON cp_alerts FOR SELECT TO authenticated USING (EXISTS (SELECT 1 FROM cp_users member WHERE member.organization_id = cp_alerts.organization_id AND member.auth_id = auth.uid()::text));


CREATE TABLE IF NOT EXISTS cp_communication_events (
	customer_id VARCHAR(36) NOT NULL,
	upload_id VARCHAR(36) NOT NULL,
	channel VARCHAR(30) NOT NULL,
	occurred_at VARCHAR(40),
	identity_basis VARCHAR(100) NOT NULL,
	organization_id VARCHAR(36) NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at VARCHAR(40) NOT NULL,
	updated_at VARCHAR(40) NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(customer_id) REFERENCES cp_customers (id) ON DELETE CASCADE,
	UNIQUE (upload_id),
	FOREIGN KEY(upload_id) REFERENCES cp_uploaded_files (id) ON DELETE CASCADE,
	FOREIGN KEY(organization_id) REFERENCES cp_organizations (id) ON DELETE CASCADE
)

;

CREATE INDEX IF NOT EXISTS ix_cp_communication_events_customer_id ON cp_communication_events (customer_id);

CREATE INDEX IF NOT EXISTS ix_cp_communication_events_organization_id ON cp_communication_events (organization_id);

ALTER TABLE cp_communication_events ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_read ON cp_communication_events;

CREATE POLICY tenant_read ON cp_communication_events FOR SELECT TO authenticated USING (EXISTS (SELECT 1 FROM cp_users member WHERE member.organization_id = cp_communication_events.organization_id AND member.auth_id = auth.uid()::text));


CREATE TABLE IF NOT EXISTS cp_evidence_items (
	customer_id VARCHAR(36),
	upload_id VARCHAR(36) NOT NULL,
	content TEXT NOT NULL,
	page INTEGER,
	timestamp DOUBLE PRECISION,
	occurred_at VARCHAR(40),
	embedding VECTOR(768),
	embedding_model VARCHAR(160),
	meta JSON NOT NULL,
	organization_id VARCHAR(36) NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at VARCHAR(40) NOT NULL,
	updated_at VARCHAR(40) NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(customer_id) REFERENCES cp_customers (id) ON DELETE CASCADE,
	FOREIGN KEY(upload_id) REFERENCES cp_uploaded_files (id) ON DELETE CASCADE,
	FOREIGN KEY(organization_id) REFERENCES cp_organizations (id) ON DELETE CASCADE
)

;

CREATE INDEX IF NOT EXISTS ix_cp_evidence_items_customer_id ON cp_evidence_items (customer_id);

CREATE INDEX IF NOT EXISTS ix_cp_evidence_items_upload_id ON cp_evidence_items (upload_id);

CREATE INDEX IF NOT EXISTS ix_cp_evidence_items_organization_id ON cp_evidence_items (organization_id);

ALTER TABLE cp_evidence_items ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_read ON cp_evidence_items;

CREATE POLICY tenant_read ON cp_evidence_items FOR SELECT TO authenticated USING (EXISTS (SELECT 1 FROM cp_users member WHERE member.organization_id = cp_evidence_items.organization_id AND member.auth_id = auth.uid()::text));


CREATE TABLE IF NOT EXISTS cp_complaint_evidence_links (
	complaint_id VARCHAR(36) NOT NULL,
	evidence_id VARCHAR(36) NOT NULL,
	finding JSON NOT NULL,
	organization_id VARCHAR(36) NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at VARCHAR(40) NOT NULL,
	updated_at VARCHAR(40) NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (complaint_id, evidence_id),
	FOREIGN KEY(complaint_id) REFERENCES cp_complaints (id) ON DELETE CASCADE,
	FOREIGN KEY(evidence_id) REFERENCES cp_evidence_items (id) ON DELETE CASCADE,
	FOREIGN KEY(organization_id) REFERENCES cp_organizations (id) ON DELETE CASCADE
)

;

CREATE INDEX IF NOT EXISTS ix_cp_complaint_evidence_links_complaint_id ON cp_complaint_evidence_links (complaint_id);

CREATE INDEX IF NOT EXISTS ix_cp_complaint_evidence_links_organization_id ON cp_complaint_evidence_links (organization_id);

CREATE INDEX IF NOT EXISTS ix_cp_complaint_evidence_links_evidence_id ON cp_complaint_evidence_links (evidence_id);

ALTER TABLE cp_complaint_evidence_links ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_read ON cp_complaint_evidence_links;

CREATE POLICY tenant_read ON cp_complaint_evidence_links FOR SELECT TO authenticated USING (EXISTS (SELECT 1 FROM cp_users member WHERE member.organization_id = cp_complaint_evidence_links.organization_id AND member.auth_id = auth.uid()::text));

CREATE INDEX IF NOT EXISTS cp_evidence_vector_idx ON cp_evidence_items USING hnsw (embedding vector_cosine_ops);
