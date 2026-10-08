"""ClientPulse tenant records; legacy Evidence tables remain intact."""
from sqlalchemy import String, Text, ForeignKey, JSON, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from services.api.db import Base, uid, now


class Record:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    created_at: Mapped[str] = mapped_column(String(40), default=now)
    updated_at: Mapped[str] = mapped_column(String(40), default=now, onupdate=now)


class Organization(Record, Base):
    __tablename__ = 'cp_organizations'
    owner_id: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(160), default='My organization')
    settings: Mapped[dict] = mapped_column(JSON, default=dict)


class Member(Record, Base):
    __tablename__ = 'cp_users'
    organization_id: Mapped[str] = mapped_column(ForeignKey('cp_organizations.id', ondelete='CASCADE'), index=True)
    auth_id: Mapped[str] = mapped_column(String(64), unique=True)
    role: Mapped[str] = mapped_column(String(20), default='owner')


class TenantRecord(Record):
    organization_id: Mapped[str] = mapped_column(ForeignKey('cp_organizations.id', ondelete='CASCADE'), index=True)


class Customer(TenantRecord, Base):
    __tablename__ = 'cp_customers'
    name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    account_ref: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default='Active')
    owner: Mapped[str] = mapped_column(String(160), default='Unassigned')
    notes: Mapped[str] = mapped_column(Text, default='')
    synthetic: Mapped[bool] = mapped_column(default=False)


class Alias(TenantRecord, Base):
    __tablename__ = 'cp_customer_aliases'
    __table_args__ = (UniqueConstraint('organization_id', 'kind', 'value'),)
    customer_id: Mapped[str] = mapped_column(ForeignKey('cp_customers.id', ondelete='CASCADE'), index=True)
    kind: Mapped[str] = mapped_column(String(30))
    value: Mapped[str] = mapped_column(String(255))


class Upload(TenantRecord, Base):
    __tablename__ = 'cp_uploaded_files'
    customer_id: Mapped[str | None] = mapped_column(ForeignKey('cp_customers.id', ondelete='CASCADE'), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    mime: Mapped[str] = mapped_column(String(100))
    source_type: Mapped[str] = mapped_column(String(30))
    path: Mapped[str] = mapped_column(Text)
    size: Mapped[int] = mapped_column(Integer)
    communication_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default='Queued', index=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    lease_at: Mapped[str | None] = mapped_column(String(40), nullable=True)


class Communication(TenantRecord, Base):
    __tablename__ = 'cp_communication_events'
    customer_id: Mapped[str] = mapped_column(ForeignKey('cp_customers.id', ondelete='CASCADE'), index=True)
    upload_id: Mapped[str] = mapped_column(ForeignKey('cp_uploaded_files.id', ondelete='CASCADE'), unique=True)
    channel: Mapped[str] = mapped_column(String(30))
    occurred_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    identity_basis: Mapped[str] = mapped_column(String(100), default='Explicit customer assignment')


class Evidence(TenantRecord, Base):
    __tablename__ = 'cp_evidence_items'
    customer_id: Mapped[str | None] = mapped_column(ForeignKey('cp_customers.id', ondelete='CASCADE'), nullable=True, index=True)
    upload_id: Mapped[str] = mapped_column(ForeignKey('cp_uploaded_files.id', ondelete='CASCADE'), index=True)
    content: Mapped[str] = mapped_column(Text)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timestamp: Mapped[float | None] = mapped_column(nullable=True)
    occurred_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    embedding: Mapped[list | None] = mapped_column(Vector(768).with_variant(JSON, "sqlite"), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(160), nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)


class Complaint(TenantRecord, Base):
    __tablename__ = 'cp_complaints'
    customer_id: Mapped[str] = mapped_column(ForeignKey('cp_customers.id', ondelete='CASCADE'), index=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    description: Mapped[str] = mapped_column(Text)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    severity: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default='Open')
    uncertainty: Mapped[str] = mapped_column(Text)
    human_status: Mapped[str | None] = mapped_column(String(20), nullable=True)


class ComplaintLink(TenantRecord, Base):
    __tablename__ = 'cp_complaint_evidence_links'
    __table_args__ = (UniqueConstraint('complaint_id', 'evidence_id'),)
    complaint_id: Mapped[str] = mapped_column(ForeignKey('cp_complaints.id', ondelete='CASCADE'), index=True)
    evidence_id: Mapped[str] = mapped_column(ForeignKey('cp_evidence_items.id', ondelete='CASCADE'), index=True)
    finding: Mapped[dict] = mapped_column(JSON)


class Risk(TenantRecord, Base):
    __tablename__ = 'cp_customer_risk_scores'
    customer_id: Mapped[str] = mapped_column(ForeignKey('cp_customers.id', ondelete='CASCADE'), unique=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    category: Mapped[str] = mapped_column(String(30))
    factors: Mapped[list] = mapped_column(JSON, default=list)
    version: Mapped[str] = mapped_column(String(30), default='heuristic-v1')


class Alert(TenantRecord, Base):
    __tablename__ = 'cp_alerts'
    customer_id: Mapped[str] = mapped_column(ForeignKey('cp_customers.id', ondelete='CASCADE'), index=True)
    complaint_id: Mapped[str] = mapped_column(ForeignKey('cp_complaints.id', ondelete='CASCADE'), index=True)
    kind: Mapped[str] = mapped_column(String(40))
    severity: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default='Open')
    owner: Mapped[str] = mapped_column(String(160), default='Unassigned')
    evidence_ids: Mapped[list] = mapped_column(JSON, default=list)


class AnalysisRun(TenantRecord, Base):
    __tablename__ = 'cp_ai_analysis_runs'
    upload_id: Mapped[str] = mapped_column(ForeignKey('cp_uploaded_files.id', ondelete='CASCADE'), index=True)
    model: Mapped[str] = mapped_column(String(160))
    version: Mapped[str] = mapped_column(String(30), default='complaints-v1')
    output: Mapped[dict] = mapped_column(JSON, default=dict)


class Draft(TenantRecord, Base):
    __tablename__ = 'cp_generated_drafts'
    customer_id: Mapped[str | None] = mapped_column(ForeignKey('cp_customers.id', ondelete='CASCADE'), nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    citations: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default='Draft')


class Conversation(TenantRecord, Base):
    __tablename__ = 'cp_messages'
    customer_id: Mapped[str | None] = mapped_column(ForeignKey('cp_customers.id', ondelete='CASCADE'), nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    citations: Mapped[list] = mapped_column(JSON, default=list)


class PulseAudit(TenantRecord, Base):
    __tablename__ = 'cp_audit_events'
    user_id: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(80))
    record_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
