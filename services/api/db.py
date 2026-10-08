import os
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
from dotenv import load_dotenv
from sqlalchemy import create_engine, String, Text, ForeignKey, JSON, Integer, Float, event, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

load_dotenv()
DATA = Path(os.getenv('DATA_DIR', './data')).resolve()
DATA.mkdir(parents=True, exist_ok=True)
URL = os.getenv('DATABASE_URL', f'sqlite:///{DATA / "evidence.db"}')
engine = create_engine(URL, connect_args={'check_same_thread': False,'timeout':30} if URL.startswith('sqlite') else {}, pool_pre_ping=True)
if URL.startswith('sqlite'):
    @event.listens_for(engine,'connect')
    def foreign_keys(connection,record):
        cursor=connection.cursor();cursor.execute('PRAGMA foreign_keys=ON');cursor.execute('PRAGMA journal_mode=WAL');cursor.execute('PRAGMA busy_timeout=30000');cursor.close()
Session = sessionmaker(engine, expire_on_commit=False)
def uid(): return str(uuid4())
def now(): return datetime.now(timezone.utc).isoformat()
class Base(DeclarativeBase): pass
class Workspace(Base):
    __tablename__ = 'workspaces'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    owner_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default='')
    industry: Mapped[str] = mapped_column(String(30))
    synthetic: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[str] = mapped_column(String(40), default=now)
class File(Base):
    __tablename__ = 'files'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id'), index=True)
    name: Mapped[str] = mapped_column(String(255))
    mime: Mapped[str] = mapped_column(String(100))
    size: Mapped[int] = mapped_column(Integer)
    path: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default='Queued')
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(String(40), default=now)
class Job(Base):
    __tablename__ = 'processing_jobs'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    file_id: Mapped[str] = mapped_column(ForeignKey('files.id'), index=True)
    status: Mapped[str] = mapped_column(String(30), default='Queued', index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[str] = mapped_column(String(40), default=now)
class Segment(Base):
    __tablename__ = 'evidence_segments'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id'), index=True)
    file_id: Mapped[str] = mapped_column(ForeignKey('files.id'), index=True)
    modality: Mapped[str] = mapped_column(String(30))
    content: Mapped[str] = mapped_column(Text)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timestamp: Mapped[float | None] = mapped_column(Float, nullable=True)
    event_time: Mapped[str | None] = mapped_column(String(100), nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)
    version: Mapped[str] = mapped_column(String(20), default='1')
class Message(Base):
    __tablename__ = 'messages'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id'), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    citations: Mapped[list] = mapped_column(JSON, default=list)
    analysis: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(String(40), default=now)
class Report(Base):
    __tablename__ = 'generated_reports'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id'), index=True)
    name: Mapped[str] = mapped_column(String(200))
    path: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String(40), default=now)
class Audit(Base):
    __tablename__ = 'audit_events'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(String(64))
    workspace_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    action: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[str] = mapped_column(String(40), default=now)
def init_db():
    from database.migrate import migrate
    migrate()
