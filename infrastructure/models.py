"""
Database Models - SQLAlchemy ORM models for PostgreSQL.
These models map to database tables and handle persistence.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Text,
    Integer,
    LargeBinary,
    ForeignKey,
    Index,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .database import Base


class UserModel(Base):
    """
    SQLAlchemy model for User entity.
    Stores user authentication and profile information.
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), default="")
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    settings = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    last_login = Column(DateTime, nullable=True)

    # Relationships
    analyses = relationship(
        "AnalysisModel", back_populates="user", cascade="all, delete-orphan"
    )
    sessions = relationship(
        "SessionModel", back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_users_username_lower", username),
        Index("ix_users_email_lower", email),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "settings": self.settings or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"


class AnalysisModel(Base):
    """
    SQLAlchemy model for Analysis entity.
    Stores analysis configuration and metadata.
    """

    __tablename__ = "analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(200), nullable=False)
    file_path = Column(String(500), default="")
    data_schema = Column(JSON, nullable=True)
    slides = Column(JSON, default=list)
    settings = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user = relationship("UserModel", back_populates="analyses")

    __table_args__ = (
        Index("ix_analyses_user_id", user_id),
        Index("ix_analyses_updated_at", updated_at),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "name": self.name,
            "file_path": self.file_path,
            "data_schema": self.data_schema,
            "slides": self.slides or [],
            "settings": self.settings or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Analysis(id={self.id}, name='{self.name}', user_id={self.user_id})>"


class SessionModel(Base):
    """
    SQLAlchemy model for user sessions.
    Stores session state for authenticated users.
    """

    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    session_data = Column(JSON, default=dict)
    settings = Column(JSON, default=dict)
    current_analysis_id = Column(UUID(as_uuid=True), nullable=True)
    current_slide_id = Column(UUID(as_uuid=True), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("UserModel", back_populates="sessions")

    __table_args__ = (
        Index("ix_sessions_user_id", user_id),
        Index("ix_sessions_token_hash", token_hash),
        Index("ix_sessions_expires_at", expires_at),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "session_data": self.session_data or {},
            "settings": self.settings or {},
            "current_analysis_id": str(self.current_analysis_id)
            if self.current_analysis_id
            else None,
            "current_slide_id": str(self.current_slide_id)
            if self.current_slide_id
            else None,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_activity": self.last_activity.isoformat()
            if self.last_activity
            else None,
        }

    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() > self.expires_at

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, user_id={self.user_id})>"


class DataFileModel(Base):
    """
    SQLAlchemy model for uploaded data files.
    Stores file metadata and content for caching.
    """

    __tablename__ = "data_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    analysis_id = Column(
        UUID(as_uuid=True),
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
    )
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, default=0)
    file_content = Column(LargeBinary, nullable=True)
    mime_type = Column(
        String(100),
        default="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_data_files_user_id", user_id),
        Index("ix_data_files_analysis_id", analysis_id),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary (without content)."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "analysis_id": str(self.analysis_id),
            "filename": self.filename,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<DataFile(id={self.id}, filename='{self.filename}')>"


class ExportJobModel(Base):
    """
    SQLAlchemy model for export jobs.
    Tracks export operations for analytics and caching.
    """

    __tablename__ = "export_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    analysis_id = Column(
        UUID(as_uuid=True),
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
    )
    format = Column(String(20), nullable=False)
    options = Column(JSON, default=dict)
    status = Column(String(20), default="pending", nullable=False)
    file_path = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_export_jobs_user_id", user_id),
        Index("ix_export_jobs_analysis_id", analysis_id),
        Index("ix_export_jobs_status", status),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "analysis_id": str(self.analysis_id),
            "format": self.format,
            "options": self.options or {},
            "status": self.status,
            "file_path": self.file_path,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
        }

    def __repr__(self) -> str:
        return f"<ExportJob(id={self.id}, status='{self.status}')>"
