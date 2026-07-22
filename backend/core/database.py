"""
Core Database — SQLite with SQLAlchemy
Stores document metadata, entities, maintenance records
"""
import os
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, Boolean, JSON,
    create_engine, event
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./iki_database.db")
DATABASE_URL = f"sqlite+aiosqlite:///{SQLITE_DB_PATH}"


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_type = Column(String(50))  # pdf, xlsx, docx, image
    file_size = Column(Integer)
    status = Column(String(50), default="processing")  # processing, ready, failed
    page_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    upload_date = Column(DateTime, default=datetime.utcnow)
    processed_date = Column(DateTime)
    tags = Column(JSON, default=list)
    summary = Column(Text)
    error_message = Column(Text)


class Entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer)
    entity_type = Column(String(100))  # equipment, operator, location, date, failure_mode
    entity_value = Column(String(255))
    context = Column(Text)
    confidence = Column(Float, default=1.0)
    page_number = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer)
    equipment_id = Column(String(100))
    equipment_name = Column(String(255))
    maintenance_type = Column(String(100))  # preventive, corrective, emergency
    description = Column(Text)
    operator = Column(String(255))
    location = Column(String(255))
    maintenance_date = Column(DateTime)
    next_due_date = Column(DateTime)
    status = Column(String(50), default="completed")
    failure_mode = Column(String(255))
    cost = Column(Float)
    risk_score = Column(String(20), default="Low")  # Low, Medium, High, Critical
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditReport(Base):
    __tablename__ = "audit_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255))
    report_type = Column(String(100))  # monthly, quarterly, compliance, equipment
    file_path = Column(String(500))
    generated_at = Column(DateTime, default=datetime.utcnow)
    summary = Column(Text)
    compliance_score = Column(Float, default=0.0)
    total_equipment = Column(Integer, default=0)
    pending_maintenance = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    message_count = Column(Integer, default=0)
    last_message = Column(Text)


# Async engine
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Create all tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency for FastAPI routes"""
    async with AsyncSessionLocal() as session:
        yield session
