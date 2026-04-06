"""
Database Module - PostgreSQL database connection and session management.
Provides database connection pooling and session handling using SQLAlchemy.
"""

from typing import Optional
from contextlib import contextmanager
import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import QueuePool
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Global database instance
_db_instance: Optional["Database"] = None

# Declarative base for models
Base = declarative_base()


class Database:
    """
    Database connection manager for PostgreSQL.
    Provides connection pooling and session management.
    Implements the Singleton pattern for database connections.
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the database connection.

        Args:
            database_url: PostgreSQL connection URL. If not provided,
                         uses environment variable DATABASE_URL or defaults to localhost.
        """
        self.database_url = database_url or os.getenv(
            "DATABASE_URL", "postgresql://postgres:k4m1c4451@localhost:5432/postgres"
        )
        self._engine = None
        self._session_factory = None
        self._initialized = False

    @property
    def engine(self):
        """Get or create the SQLAlchemy engine."""
        if self._engine is None:
            self._engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=os.getenv("SQL_ECHO", "false").lower() == "true",
            )
            self._configure_engine()
        return self._engine

    def _configure_engine(self) -> None:
        """Configure engine event listeners."""

        @event.listens_for(self._engine, "connect")
        def set_connection_settings(dbapi_connection, connection_record):
            """Set connection-level settings on each new connection."""
            cursor = dbapi_connection.cursor()
            cursor.execute("SET TIME ZONE 'UTC'")
            cursor.close()

    @property
    def session_factory(self):
        """Get or create the session factory."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
            )
        return self._session_factory

    def get_session(self) -> Session:
        """
        Create a new database session.

        Returns:
            SQLAlchemy Session object
        """
        return self.session_factory()

    @contextmanager
    def session_scope(self):
        """
        Provide a transactional scope around a series of operations.

        Usage:
            with db.session_scope() as session:
                session.add(user)
                # Automatically commits on success, rolls back on error
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def init_db(self) -> None:
        """
        Initialize the database by creating all tables.
        Should be called once at application startup.
        """
        from .models import UserModel, AnalysisModel, SessionModel, DataFileModel

        Base.metadata.create_all(self.engine)
        self._initialized = True
        logger.info("Database tables created successfully")

    def drop_all(self) -> None:
        """
        Drop all database tables.
        WARNING: This will delete all data!
        """
        Base.metadata.drop_all(self.engine)
        logger.warning("All database tables dropped")

    def health_check(self) -> bool:
        """
        Check database connectivity.

        Returns:
            True if database is accessible, False otherwise
        """
        try:
            with self.session_scope() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    def close(self) -> None:
        """Close all database connections."""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database connections closed")


def get_database() -> Database:
    """
    Get the global database instance.
    Creates a new instance if none exists.

    Returns:
        Database instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


def init_database(database_url: Optional[str] = None) -> Database:
    """
    Initialize the global database instance.

    Args:
        database_url: Optional database URL override

    Returns:
        Initialized Database instance
    """
    global _db_instance
    _db_instance = Database(database_url)
    _db_instance.init_db()
    return _db_instance


def reset_database() -> None:
    """
    Reset the global database instance.
    Used for testing purposes.
    """
    global _db_instance
    if _db_instance:
        _db_instance.close()
    _db_instance = None
