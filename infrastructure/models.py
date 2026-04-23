"""
Database Models - SQLAlchemy ORM models for PostgreSQL.
These models map to database tables and handle persistence.
Matches the schema defined in smartxl_db_creator.sql
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
    BigInteger,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from .database import Base


class UserModel(Base):
    """
    SQLAlchemy model for User entity.
    Stores user authentication and profile information.
    """

    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    files = relationship(
        "FileModel", back_populates="user", cascade="all, delete-orphan"
    )
    dashboards = relationship(
        "DashboardModel", back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_users_email", email),)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "user_id": str(self.user_id),
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, username='{self.username}')>"


class FileModel(Base):
    """
    SQLAlchemy model for uploaded files.
    Stores file metadata and S3 storage path.
    """

    __tablename__ = "files"

    file_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    file_name = Column(Text, nullable=False)
    storage_path = Column(Text, nullable=False)  # S3 path
    file_size_kb = Column(BigInteger, nullable=False)
    uploaded_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    user = relationship("UserModel", back_populates="files")
    sheets = relationship(
        "FileSheetModel", back_populates="file", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_files_user_id", user_id),)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "file_id": str(self.file_id),
            "user_id": str(self.user_id),
            "file_name": self.file_name,
            "storage_path": self.storage_path,
            "file_size_kb": self.file_size_kb,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
        }

    def __repr__(self) -> str:
        return f"<File(file_id={self.file_id}, file_name='{self.file_name}')>"


class FileSheetModel(Base):
    """
    SQLAlchemy model for sheets within Excel files.
    Each uploaded file can have multiple sheets.
    """

    __tablename__ = "file_sheets"

    sheet_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(
        UUID(as_uuid=True),
        ForeignKey("files.file_id", ondelete="CASCADE"),
        nullable=False,
    )
    sheet_name = Column(Text, nullable=False)

    # Relationships
    file = relationship("FileModel", back_populates="sheets")
    columns = relationship(
        "SheetColumnModel", back_populates="sheet", cascade="all, delete-orphan"
    )
    visualizations = relationship(
        "VisualizationModel", back_populates="sheet", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_file_sheets_file_id", file_id),)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "sheet_id": str(self.sheet_id),
            "file_id": str(self.file_id),
            "sheet_name": self.sheet_name,
        }

    def __repr__(self) -> str:
        return f"<FileSheet(sheet_id={self.sheet_id}, sheet_name='{self.sheet_name}')>"


class SheetColumnModel(Base):
    """
    SQLAlchemy model for columns within sheets.
    Stores column metadata and data types.
    """

    __tablename__ = "sheet_columns"

    column_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sheet_id = Column(
        UUID(as_uuid=True),
        ForeignKey("file_sheets.sheet_id", ondelete="CASCADE"),
        nullable=False,
    )
    column_name = Column(Text, nullable=False)
    data_type = Column(String(20), nullable=False)  # Int64, Float64, String, etc.

    # Relationships
    sheet = relationship("FileSheetModel", back_populates="columns")

    __table_args__ = (Index("idx_sheet_columns_sheet_id", sheet_id),)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "column_id": str(self.column_id),
            "sheet_id": str(self.sheet_id),
            "column_name": self.column_name,
            "data_type": self.data_type,
        }

    def __repr__(self) -> str:
        return f"<SheetColumn(column_id={self.column_id}, column_name='{self.column_name}')>"


class DashboardModel(Base):
    """
    SQLAlchemy model for dashboards.
    A dashboard is a collection of visualizations from one or more sheets.
    """

    __tablename__ = "dashboards"

    dashboard_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    user = relationship("UserModel", back_populates="dashboards")
    visualizations = relationship(
        "VisualizationModel", back_populates="dashboard", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_dashboards_user_id", user_id),)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "dashboard_id": str(self.dashboard_id),
            "user_id": str(self.user_id),
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Dashboard(dashboard_id={self.dashboard_id}, title='{self.title}')>"


class VisualizationModel(Base):
    """
    SQLAlchemy model for visualizations.
    Stores visualization configuration as JSONB.
    """

    __tablename__ = "visualizations"

    viz_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dashboards.dashboard_id", ondelete="CASCADE"),
        nullable=False,
    )
    sheet_id = Column(
        UUID(as_uuid=True), ForeignKey("file_sheets.sheet_id"), nullable=False
    )
    viz_type = Column(String(50), nullable=False)  # bar, scatter, pie, etc.
    config = Column(JSONB, nullable=False)  # Stores axis, colors, layout, etc.
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    dashboard = relationship("DashboardModel", back_populates="visualizations")
    sheet = relationship("FileSheetModel", back_populates="visualizations")

    __table_args__ = (
        Index("idx_visualizations_config", config, postgresql_using="gin"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "viz_id": str(self.viz_id),
            "dashboard_id": str(self.dashboard_id),
            "sheet_id": str(self.sheet_id),
            "viz_type": self.viz_type,
            "config": self.config or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Visualization(viz_id={self.viz_id}, viz_type='{self.viz_type}')>"
