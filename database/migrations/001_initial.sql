-- EVIDENCE.AI initial PostgreSQL schema. Equivalent to SQLAlchemy models.


CREATE TABLE audit_events (
	id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(64) NOT NULL, 
	workspace_id VARCHAR(36), 
	action VARCHAR(50) NOT NULL, 
	created_at VARCHAR(40) NOT NULL, 
	PRIMARY KEY (id)
)

;


CREATE TABLE workspaces (
	id VARCHAR(36) NOT NULL, 
	owner_id VARCHAR(64) NOT NULL, 
	name VARCHAR(160) NOT NULL, 
	description TEXT NOT NULL, 
	industry VARCHAR(30) NOT NULL, 
	synthetic BOOLEAN NOT NULL, 
	created_at VARCHAR(40) NOT NULL, 
	PRIMARY KEY (id)
)

;


CREATE TABLE files (
	id VARCHAR(36) NOT NULL, 
	workspace_id VARCHAR(36) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	mime VARCHAR(100) NOT NULL, 
	size INTEGER NOT NULL, 
	path TEXT NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	error TEXT, 
	meta JSON NOT NULL, 
	created_at VARCHAR(40) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id)
)

;


CREATE TABLE generated_reports (
	id VARCHAR(36) NOT NULL, 
	workspace_id VARCHAR(36) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	path TEXT NOT NULL, 
	created_at VARCHAR(40) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id)
)

;


CREATE TABLE messages (
	id VARCHAR(36) NOT NULL, 
	workspace_id VARCHAR(36) NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	content TEXT NOT NULL, 
	citations JSON NOT NULL, 
	analysis JSON NOT NULL, 
	created_at VARCHAR(40) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id)
)

;


CREATE TABLE evidence_segments (
	id VARCHAR(36) NOT NULL, 
	workspace_id VARCHAR(36) NOT NULL, 
	file_id VARCHAR(36) NOT NULL, 
	modality VARCHAR(30) NOT NULL, 
	content TEXT NOT NULL, 
	page INTEGER, 
	timestamp FLOAT, 
	event_time VARCHAR(100), 
	meta JSON NOT NULL, 
	embedding JSON, 
	version VARCHAR(20) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id), 
	FOREIGN KEY(file_id) REFERENCES files (id)
)

;


CREATE TABLE processing_jobs (
	id VARCHAR(36) NOT NULL, 
	file_id VARCHAR(36) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	attempts INTEGER NOT NULL, 
	started_at VARCHAR(40), 
	created_at VARCHAR(40) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(file_id) REFERENCES files (id)
)

;

CREATE INDEX ix_workspaces_owner_id ON workspaces (owner_id);
CREATE INDEX ix_files_workspace_id ON files (workspace_id);
CREATE INDEX ix_generated_reports_workspace_id ON generated_reports (workspace_id);
CREATE INDEX ix_messages_workspace_id ON messages (workspace_id);
CREATE INDEX ix_evidence_segments_workspace_id ON evidence_segments (workspace_id);
CREATE INDEX ix_evidence_segments_file_id ON evidence_segments (file_id);
CREATE INDEX ix_processing_jobs_file_id ON processing_jobs (file_id);
CREATE INDEX ix_processing_jobs_status ON processing_jobs (status);