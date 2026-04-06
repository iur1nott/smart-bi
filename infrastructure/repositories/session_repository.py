"""
Session Repository Implementation - PostgreSQL-based session persistence.
Implements the SessionRepository interface using SQLAlchemy.
"""

from typing import Optional, List
from datetime import datetime, timedelta
import logging

from domain.entities import UserSession
from domain.repositories import SessionRepository
from infrastructure.database import Database, get_database
from infrastructure.models import SessionModel

logger = logging.getLogger(__name__)


class SessionRepositoryImpl(SessionRepository):
    """
    PostgreSQL implementation of the SessionRepository interface.
    Handles session persistence operations using SQLAlchemy ORM.
    """

    def __init__(self, database: Optional[Database] = None):
        """
        Initialize the repository with a database connection.

        Args:
            database: Optional Database instance. Uses global instance if not provided.
        """
        self._db = database or get_database()
        self._session_timeout_hours = 24  # Default session timeout

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

                # Set expiration if not set
                expires_at = session.expires_at
                if expires_at is None:
                    expires_at = datetime.utcnow() + timedelta(
                        hours=self._session_timeout_hours
                    )

                if existing:
                    # Update existing session
                    existing.user_id = session.user_id
                    existing.token_hash = session.token_hash
                    existing.session_data = session.session_data
                    existing.settings = session.settings
                    existing.current_analysis_id = session.current_analysis_id
                    existing.current_slide_id = session.current_slide_id
                    existing.expires_at = expires_at
                    existing.last_activity = session.last_activity or datetime.utcnow()
                else:
                    # Create new session
                    model = SessionModel(
                        id=session.id,
                        user_id=session.user_id,
                        token_hash=session.token_hash,
                        session_data=session.session_data,
                        settings=session.settings,
                        expires_at=expires_at,
                        last_activity=session.last_activity or datetime.utcnow(),
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
        Find a session by user ID.

        Args:
            user_id: The unique identifier of the user

        Returns:
            UserSession entity if found, None otherwise
        """
        try:
            with self._db.session_scope() as db_session:
                # Get the most recent active session for the user
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

    def find_by_token_hash(self, token_hash: str) -> Optional[UserSession]:
        """
        Find a session by its token hash.

        Args:
            token_hash: The hash of the session token

        Returns:
            UserSession entity if found, None otherwise
        """
        try:
            with self._db.session_scope() as db_session:
                model = (
                    db_session.query(SessionModel)
                    .filter(SessionModel.token_hash == token_hash)
                    .first()
                )

                if model and not model.is_expired():
                    return self._model_to_entity(model)
                return None

        except Exception as e:
            logger.error(f"Error finding session by token hash: {e}")
            return None

    def find_all_active(self, user_id: str) -> List[UserSession]:
        """
        Find all active sessions for a user.

        Args:
            user_id: The unique identifier of the user

        Returns:
            List of active UserSession entities
        """
        try:
            with self._db.session_scope() as db_session:
                models = (
                    db_session.query(SessionModel)
                    .filter(
                        SessionModel.user_id == user_id,
                        SessionModel.expires_at > datetime.utcnow(),
                    )
                    .order_by(SessionModel.last_activity.desc())
                    .all()
                )

                return [self._model_to_entity(m) for m in models]

        except Exception as e:
            logger.error(f"Error finding active sessions for user {user_id}: {e}")
            return []

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
                model = (
                    db_session.query(SessionModel)
                    .filter(SessionModel.id == session_id)
                    .first()
                )

                if model:
                    db_session.delete(model)
                    return True
                return False

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

    def delete_expired(self) -> int:
        """
        Delete all expired sessions from the database.

        Returns:
            Number of sessions deleted
        """
        try:
            with self._db.session_scope() as db_session:
                result = (
                    db_session.query(SessionModel)
                    .filter(SessionModel.expires_at <= datetime.utcnow())
                    .delete()
                )
                logger.info(f"Deleted {result} expired sessions")
                return result

        except Exception as e:
            logger.error(f"Error deleting expired sessions: {e}")
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
                model = (
                    db_session.query(SessionModel)
                    .filter(SessionModel.id == session_id)
                    .first()
                )

                if model:
                    model.last_activity = datetime.utcnow()
                    # Extend expiration on activity
                    model.expires_at = datetime.utcnow() + timedelta(
                        hours=self._session_timeout_hours
                    )
                    return True
                return False

        except Exception as e:
            logger.error(f"Error updating activity for session {session_id}: {e}")
            return False

    def update_session_data(self, session_id: str, data: dict) -> bool:
        """
        Update session data for a session.

        Args:
            session_id: The unique identifier of the session
            data: New session data to merge

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._db.session_scope() as db_session:
                model = (
                    db_session.query(SessionModel)
                    .filter(SessionModel.id == session_id)
                    .first()
                )

                if model:
                    current_data = model.session_data or {}
                    current_data.update(data)
                    model.session_data = current_data
                    model.last_activity = datetime.utcnow()
                    return True
                return False

        except Exception as e:
            logger.error(f"Error updating session data for session {session_id}: {e}")
            return False

    def _model_to_entity(self, model: SessionModel) -> UserSession:
        """Convert a SQLAlchemy model to a domain entity."""
        return UserSession(
            id=str(model.id),
            user_id=str(model.user_id),
            token_hash=model.token_hash,
            session_data=model.session_data or {},
            settings=model.settings or {},
            current_analysis_id=str(model.current_analysis_id)
            if model.current_analysis_id
            else None,
            current_slide_id=str(model.current_slide_id)
            if model.current_slide_id
            else None,
            created_at=model.created_at,
            expires_at=model.expires_at,
            last_activity=model.last_activity,
        )
