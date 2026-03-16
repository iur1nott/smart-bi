"""
Session Repository Implementation - PostgreSQL-based session persistence.
Implements the SessionRepository interface using SQLAlchemy.
"""

from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import hashlib
import secrets

from domain.entities import UserSession, Analysis
from domain.repositories import SessionRepository
from infrastructure.database import Database, get_database
from infrastructure.models import SessionModel
import logging

logger = logging.getLogger(__name__)


class SessionRepositoryImpl(SessionRepository):
    """
    PostgreSQL implementation of the SessionRepository interface.
    Handles session persistence operations using SQLAlchemy ORM.
    """

    SESSION_DURATION_HOURS = 24  # Session expires after 24 hours

    def __init__(self, database: Optional[Database] = None):
        """
        Initialize the repository with a database connection.

        Args:
            database: Optional Database instance. Uses global instance if not provided.
        """
        self._db = database or get_database()

    def save(self, session: UserSession) -> bool:
        """
        Save a session to the database.

        Args:
            session: The session entity to save

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._db.session_scope() as db_session:
                # Check if session exists
                existing = (
                    db_session.query(SessionModel)
                    .filter(SessionModel.id == session.id)
                    .first()
                )

                # Generate token hash for the session
                token_hash = self._generate_token_hash(session.id)

                # Serialize session data
                session_data = session.to_dict()

                if existing:
                    # Update existing session
                    existing.session_data = session_data
                    existing.last_activity = datetime.utcnow()
                    existing.expires_at = datetime.utcnow() + timedelta(
                        hours=self.SESSION_DURATION_HOURS
                    )
                else:
                    # Create new session
                    model = SessionModel(
                        id=session.id,
                        user_id=session.user_id,
                        token_hash=token_hash,
                        session_data=session_data,
                        created_at=session.created_at,
                        expires_at=datetime.utcnow()
                        + timedelta(hours=self.SESSION_DURATION_HOURS),
                        last_activity=datetime.utcnow(),
                    )
                    db_session.add(model)

                return True

        except Exception as e:
            logger.error(f"Error saving session {session.id}: {e}")
            return False

    def find_by_id(self, session_id: str) -> Optional[UserSession]:
        """
        Find a session by its ID.

        Args:
            session_id: The unique identifier of the session

        Returns:
            UserSession entity if found, None otherwise
        """
        try:
            with self._db.session_scope() as db_session:
                model = (
                    db_session.query(SessionModel)
                    .filter(SessionModel.id == session_id)
                    .first()
                )

                if model and not model.is_expired():
                    return self._model_to_entity(model)
                return None

        except Exception as e:
            logger.error(f"Error finding session by ID {session_id}: {e}")
            return None

    def find_by_user_id(self, user_id: str) -> Optional[UserSession]:
        """
        Find the active session for a user.

        Args:
            user_id: The unique identifier of the user

        Returns:
            UserSession entity if found, None otherwise
        """
        try:
            with self._db.session_scope() as db_session:
                model = (
                    db_session.query(SessionModel)
                    .filter(
                        SessionModel.user_id == user_id,
                        SessionModel.expires_at > datetime.utcnow(),
                    )
                    .order_by(SessionModel.last_activity.desc())
                    .first()
                )

                if model:
                    return self._model_to_entity(model)
                return None

        except Exception as e:
            logger.error(f"Error finding session for user {user_id}: {e}")
            return None

    def delete(self, session_id: str) -> bool:
        """
        Delete a session from the database.

        Args:
            session_id: The unique identifier of the session to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._db.session_scope() as db_session:
                deleted = (
                    db_session.query(SessionModel)
                    .filter(SessionModel.id == session_id)
                    .delete()
                )
                return deleted > 0

        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False

    def delete_by_user_id(self, user_id: str) -> bool:
        """
        Delete all sessions for a user.

        Args:
            user_id: The unique identifier of the user

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._db.session_scope() as db_session:
                db_session.query(SessionModel).filter(
                    SessionModel.user_id == user_id
                ).delete()
                return True

        except Exception as e:
            logger.error(f"Error deleting sessions for user {user_id}: {e}")
            return False

    def cleanup_expired(self, max_age_hours: int = 24) -> int:
        """
        Clean up expired sessions.

        Args:
            max_age_hours: Maximum session age in hours

        Returns:
            Number of sessions cleaned up
        """
        try:
            with self._db.session_scope() as db_session:
                cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
                deleted = (
                    db_session.query(SessionModel)
                    .filter(SessionModel.expires_at < cutoff)
                    .delete()
                )
                return deleted

        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0

    def update_activity(self, session_id: str) -> bool:
        """
        Update the last activity timestamp for a session.

        Args:
            session_id: The unique identifier of the session

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._db.session_scope() as db_session:
                updated = (
                    db_session.query(SessionModel)
                    .filter(SessionModel.id == session_id)
                    .update(
                        {
                            "last_activity": datetime.utcnow(),
                            "expires_at": datetime.utcnow()
                            + timedelta(hours=self.SESSION_DURATION_HOURS),
                        }
                    )
                )
                return updated > 0

        except Exception as e:
            logger.error(f"Error updating session activity {session_id}: {e}")
            return False

    def _generate_token_hash(self, session_id: str) -> str:
        """
        Generate a secure token hash for the session.

        Args:
            session_id: The session ID to hash

        Returns:
            SHA-256 hash of the session ID with salt
        """
        salt = secrets.token_hex(16)
        data = f"{session_id}:{salt}"
        return hashlib.sha256(data.encode()).hexdigest()

    def _model_to_entity(self, model: SessionModel) -> UserSession:
        """
        Convert a SQLAlchemy model to a domain entity.

        Args:
            model: SQLAlchemy SessionModel instance

        Returns:
            UserSession domain entity
        """
        session_data = model.session_data or {}

        return UserSession(
            id=str(model.id),
            user_id=str(model.user_id),
            analyses=[Analysis.from_dict(a) for a in session_data.get("analyses", [])],
            current_analysis_id=session_data.get("current_analysis_id"),
            current_slide_id=session_data.get("current_slide_id"),
            settings=session_data.get("settings", {}),
            created_at=model.created_at,
        )
