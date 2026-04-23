"""
User Repository Implementation - PostgreSQL-based user persistence.
Implements the UserRepository interface using SQLAlchemy.
Updated for new schema with user_id as primary key.
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
                existing = (
                    session.query(UserModel)
                    .filter(UserModel.user_id == user.user_id)
                    .first()
                )

                if existing:
                    # Update existing user
                    existing.username = user.username
                    existing.email = user.email
                    existing.password_hash = user.password_hash
                else:
                    # Create new user
                    model = UserModel(
                        user_id=user.user_id,
                        username=user.username,
                        email=user.email,
                        password_hash=user.password_hash,
                        created_at=user.created_at,
                    )
                    session.add(model)

                return True

        except Exception as e:
            logger.error(f"Error saving user {user.user_id}: {e}")
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
                model = (
                    session.query(UserModel)
                    .filter(UserModel.user_id == user_id)
                    .first()
                )

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
                model = (
                    session.query(UserModel)
                    .filter(UserModel.username.ilike(username))
                    .first()
                )

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
                model = (
                    session.query(UserModel)
                    .filter(UserModel.email.ilike(email))
                    .first()
                )

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
                model = (
                    session.query(UserModel)
                    .filter(UserModel.user_id == user_id)
                    .first()
                )

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
            user_id=str(model.user_id),
            username=model.username,
            email=model.email,
            password_hash=model.password_hash,
            created_at=model.created_at,
        )
