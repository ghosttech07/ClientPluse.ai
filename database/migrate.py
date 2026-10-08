"""Initial schema migration, idempotent and version-recorded. Subsequent schema changes require new versions."""
from sqlalchemy import text
from pathlib import Path
from services.api.db import engine,Base
from services.api import pulse_models
def migrate():
    with engine.begin() as conn:
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
    print('ClientPulse schema version 3 is ready.')
if __name__=='__main__':migrate()
