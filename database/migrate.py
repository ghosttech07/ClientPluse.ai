"""Initial schema migration, idempotent and version-recorded. Subsequent schema changes require new versions."""
from sqlalchemy import text
from pathlib import Path
from services.api.db import engine,Base
from services.api import pulse_models
def migrate():
    with engine.begin() as conn:
        if engine.dialect.name=='postgresql':conn.execute(text('SELECT pg_advisory_xact_lock(734821045)'))
        conn.execute(text('CREATE TABLE IF NOT EXISTS schema_versions (version INTEGER PRIMARY KEY, applied_at VARCHAR(40) NOT NULL)'))
        if engine.dialect.name=='postgresql':conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
        if not conn.scalar(text('SELECT version FROM schema_versions WHERE version=1')):
            Base.metadata.create_all(conn)
            conn.execute(text("INSERT INTO schema_versions(version,applied_at) VALUES (1,CURRENT_TIMESTAMP)"))
        if not conn.scalar(text('SELECT version FROM schema_versions WHERE version=3')):
            Base.metadata.create_all(conn)
            if engine.dialect.name=='postgresql':
                source=Path(__file__).parent/'migrations'/'003_clientpulse.sql'
                for statement in source.read_text().split(';'):
                    if statement.strip():conn.execute(text(statement))
            conn.execute(text("INSERT INTO schema_versions(version,applied_at) VALUES (3,CURRENT_TIMESTAMP)"))
        if not conn.scalar(text('SELECT version FROM schema_versions WHERE version=4')):
            pulse_models.EmailDelivery.__table__.create(conn,checkfirst=True)
            if engine.dialect.name=='postgresql':
                conn.execute(text('ALTER TABLE cp_email_deliveries ENABLE ROW LEVEL SECURITY'))
                conn.execute(text('REVOKE ALL ON cp_email_deliveries FROM anon, authenticated'))
            conn.execute(text("INSERT INTO schema_versions(version,applied_at) VALUES (4,CURRENT_TIMESTAMP)"))
    print('ClientPulse schema version 4 is ready.')
if __name__=='__main__':migrate()
