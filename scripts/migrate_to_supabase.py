"""Copy existing SQLite records to Supabase without deleting the source.

Stop API and worker before migration. Set DATABASE_URL in root .env to the
Supabase PostgreSQL URI, then run --source data/evidence.db.
"""
import argparse
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, select, func, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import make_url


def normalized(value):
    if hasattr(value,'tolist'):value=value.tolist()
    if isinstance(value,dict):return {k:normalized(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):return [normalized(v) for v in value]
    return value


def equivalent(a,b):
    a,b=normalized(a),normalized(b)
    if isinstance(a,(float,int)) and isinstance(b,(float,int)):return abs(a-b)<1e-6
    if isinstance(a,list) and isinstance(b,list):return len(a)==len(b) and all(equivalent(x,y) for x,y in zip(a,b))
    if isinstance(a,dict) and isinstance(b,dict):return a.keys()==b.keys() and all(equivalent(a[k],b[k]) for k in a)
    return a==b


def migrate(source_path, target_url):
    target=make_url(target_url)
    if target.get_backend_name()!='postgresql' or not target.host or not (target.host.endswith('.supabase.co') or target.host.endswith('.supabase.com')):
        raise ValueError('DATABASE_URL must point to Supabase PostgreSQL, not SQLite or another database.')
    source_path=Path(source_path).resolve()
    if not source_path.is_file():raise ValueError('The source SQLite database does not exist.')
    root=Path(__file__).resolve().parents[1]
    backup_dir=root/'data'/'backups';backup_dir.mkdir(parents=True,exist_ok=True)
    backup=backup_dir/('before-supabase-'+datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')+'.sqlite')
    with sqlite3.connect(source_path) as original,sqlite3.connect(backup) as copy:original.backup(copy)
    print('Local backup saved:',backup,flush=True)
    target=target.set(drivername='postgresql+psycopg')
    # Set before importing the application metadata, which constructs its engine.
    os.environ['DATABASE_URL']=target.render_as_string(hide_password=False)
    from services.api.db import Base,engine
    from services.api import pulse_models
    from database.migrate import migrate as schema
    schema()
    local=create_engine('sqlite:///'+backup.as_posix())
    names=set(inspect(local).get_table_names())
    tables=[t for t in Base.metadata.sorted_tables if t.name in names]
    unknown=names-{t.name for t in tables}-{'schema_versions','sqlite_sequence'}
    if unknown:raise ValueError('Unrecognized source tables require review before migration: '+', '.join(sorted(unknown)))
    # Both preflight and copying use a single PostgreSQL transaction. Existing
    # records with the same ID must match; conflicts never overwrite cloud data.
    counts={}
    with local.connect() as source,engine.begin() as dest:
        dest.execute(text("SELECT pg_advisory_xact_lock(714026108)"))
        for table in tables:
            source_rows=list(source.execute(select(table)).mappings())
            for row in source_rows:
                predicate=[column==row[column.name] for column in table.primary_key.columns]
                existing=dest.execute(select(table).where(*predicate)).mappings().first()
                if existing and any(not equivalent(row[column.name],existing[column.name]) for column in table.columns):
                    raise ValueError('Cloud/source record conflict in '+table.name+'. No record data was copied; review before retrying.')
            counts[table.name]=len(source_rows)
        for table in tables:
            rows=[dict(row) for row in source.execute(select(table)).mappings()]
            for index in range(0,len(rows),100):
                dest.execute(insert(table).values(rows[index:index+100]).on_conflict_do_nothing())
            # Check every migrated row, not just counts, while rollback is possible.
            for row in rows:
                predicate=[column==row[column.name] for column in table.primary_key.columns]
                copied=dest.execute(select(table).where(*predicate)).mappings().first()
                if not copied or any(not equivalent(row[column.name],copied[column.name]) for column in table.columns):
                    raise ValueError('Data verification failed in '+table.name+'. Copy transaction rolled back.')
        # Legacy archives have no browser API. Deny direct browser access while
        # retaining records for the trusted backend database role.
        for table in tables:
            if not table.name.startswith('cp_'):dest.execute(text('ALTER TABLE "'+table.name+'" ENABLE ROW LEVEL SECURITY'))
        distance=dest.scalar(text("SELECT '[1,0,0]'::vector <=> '[1,0,0]'::vector"))
        if distance!=0:raise ValueError('pgvector operator verification failed.')
    print('Verified migrated record counts:',json.dumps(counts,sort_keys=True),flush=True)
    print('Supabase record copy and pgvector operator verification passed. Local backup remains intact.',flush=True)
    return counts


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',required=True,help='Existing SQLite database path')
    parser.add_argument('--inventory',action='store_true',help='Print table counts only, without cloud changes')
    args=parser.parse_args();load_dotenv()
    if args.inventory:
        path=Path(args.source).resolve()
        if not path.is_file():raise SystemExit('Source database does not exist.')
        with sqlite3.connect(path) as db:
            names=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
            print({name:db.execute('SELECT count(*) FROM "'+name.replace('"','""')+'"').fetchone()[0] for name in names})
        return
    try:migrate(args.source,os.environ.get('DATABASE_URL',''))
    except Exception as error:
        # Provider exceptions may contain passwords/connection URIs. Do not print them.
        if isinstance(error,ValueError):print(str(error))
        else:print('Migration failed ('+type(error).__name__+'). Check database credentials/network and retry. No secrets logged.')
        raise SystemExit(1)


if __name__=='__main__':main()
