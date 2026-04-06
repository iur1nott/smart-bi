"""
User Repository Implementation - PostgreSQL-based user persistence.
Implements the UserRepository interface using SQLAlchemy.
"""

from typing import List, Optional
from datetime import datetime
import logging

from domain.entities import User
from domain.repositories import UserRepository
from infrastructure.database import Database, get_database
from infrastructure.models import UserModel

logger = logging.getLogger(__name__)


class UserRepositoryImpl(UserRepository):
    """
    PostgreSQL implementation of the UserRepository interface.
    Handles user persistence operations using SQLAlchemy ORM.
    """

    def __init__(self, database: Optional[Database] = None):
        """
        Initialize the repository with a database connection.

        Args:
            database: Optional Database instance. Uses global instance if not provided.
        """
        self._db = database or get_database()

    def save(self, user: User) -> bool:
        """
        Save a user to the database.

        Args:
            user: The user entity to save

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._db.session_scope() as session:
                # Check if user exists
                existing = session.query(UserModel).filter(UserModel.id == user.id).first()

                if existing:
                    # Update existing user
                    existing.username = user.username
                    existing.email = user.email
                    existing.password_hash = user.password_hash
                    existing.full_name = user.full_name
                    existing.is_active = user.is_active
                    existing.is_admin = user.is_admin
                    existing.settings = user.settings
                    existing.updated_at = datetime.utcnow()
                    if user.last_login:
                        existing.last_login = user.last_login
                else:
                    # Create new user
                    model = UserModel(
                        id=user.id,
                        username=user.username,
                        email=user.email,
                        password_hash=user.password_hash,
                        full_name=user.full_name,
                        is_active=user.is_active,
                        is_admin=user.is_admin,
                        settings=user.settings,
                        created_at=user.created_at,
                        updated_at=user.updated_at,
                        last_login=user.last_login,
                    )
                    session.add(model)

                return True

        except Exception as e:
            logger.error(f"Error saving user {user.id}: {e}")
            return False

    def find_by_id(self, user_id: str) -> Optional[User]:
        """
        Find a user by their ID.

        Args:
            user_id: The unique identifier of the user

        Returns:
            User entity if found, None otherwise
        """
        try:
            with self._db.session_scope() as session:
                model = session.query(UserModel).filter(UserModel.id == user_id).first()

                if model:
                    return self._model_to_entity(model)
                return None

        except Exception as e:
            logger.error(f"Error finding user by ID {user_id}: {e}")
            return None

    def find_by_username(self, username: str) -> Optional[User]:
        """
        Find a user by their username.

        Args:
            username: The username to search for

        Returns:
            User entity if found, None otherwise
        """
        try:
            with self._db.session_scope() as session:
                model = session.query(UserModel).filter(UserModel.username.ilike(username)).first()

                if model:
                    return self._model_to_entity(model)
                return None

        except Exception as e:
            logger.error(f"Error finding user by username {username}: {e}")
            return None

    def find_by_email(self, email: str) -> Optional[User]:
        """
        Find a user by their email address.

        Args:
            email: The email address to search for

        Returns:
            User entity if found, None otherwise
        """
        try:
            with self._db.session_scope() as session:
                model = session.query(UserModel).filter(UserModel.email.ilike(email)).first()

                if model:
                    return self._model_to_entity(model)
                return None

        except Exception as e:
            logger.error(f"Error finding user by email {email}: {e}")
            return None

    def find_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """
        Find all users with pagination.

        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip

        Returns:
            List of User entities
        """
        try:
            with self._db.session_scope() as session:
                models = (
                    session.query(UserModel)
                    .order_by(UserModel.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                    .all()
                )

                return [self._model_to_entity(m) for m in models]

        except Exception as e:
            logger.error(f"Error finding all users: {e}")
            return []

    def delete(self, user_id: str) -> bool:
        """
        Delete a user from the database.

        Args:
            user_id: The unique identifier of the user to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._db.session_scope() as session:
                model = session.query(UserModel).filter(UserModel.id == user_id).first()

                if model:
                    session.delete(model)
                    return True
                return False

        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False

    def count(self) -> int:
        """
        Count the total number of users.

        Returns:
            Total user count
        """
        try:
            with self._db.session_scope() as session:
                return session.query(UserModel).count()

        except Exception as e:
            logger.error(f"Error counting users: {e}")
            return 0

    def _model_to_entity(self, model: UserModel) -> User:
        """Convert a SQLAlchemy model to a domain entity."""
        return User(
            id=str(model.id),
            username=model.username,
            email=model.email,
            password_hash=model.password_hash,
            full_name=model.full_name or "",
            is_active=model.is_active,
            is_admin=model.is_admin,
            settings=model.settings or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_login=model.last_login,
        )
