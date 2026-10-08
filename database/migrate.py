"""Initial schema migration, idempotent and version-recorded. Subsequent schema changes require new versions."""
from sqlalchemy import text
from services.api.db import engine,Base
def migrate():
    with engine.begin() as conn:
        conn.execute(text('CREATE TABLE IF NOT EXISTS schema_versions (version INTEGER PRIMARY KEY, applied_at VARCHAR(40) NOT NULL)'))
        if not conn.scalar(text('SELECT version FROM schema_versions WHERE version=1')):
            Base.metadata.create_all(conn)
            conn.execute(text("INSERT INTO schema_versions(version,applied_at) VALUES (1,CURRENT_TIMESTAMP)"))
    print('Schema version 1 is ready.')
if __name__=='__main__':migrate()
