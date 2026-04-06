"""
Authentication Service - Handles user authentication and session management.
Implements business logic for login, registration, and token management.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import logging

from domain.entities import User, UserSession
from domain.repositories import UserRepository, SessionRepository
from domain.value_objects import Credentials
from infrastructure.auth import JWTHandler, PasswordHandler, AuthToken
from infrastructure.repositories import UserRepositoryImpl, SessionRepositoryImpl

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Exception raised when authentication fails."""

    pass


@dataclass
class AuthResult:
    """Result of an authentication operation."""

    success: bool
    user: Optional[User] = None
    token: Optional[AuthToken] = None
    session: Optional[UserSession] = None
    error_message: Optional[str] = None


class AuthService:
    """
    Service responsible for user authentication and session management.
    Implements authentication business logic following the Single Responsibility Principle.
    """

    def __init__(
        self,
        user_repository: Optional[UserRepository] = None,
        session_repository: Optional[SessionRepository] = None,
        jwt_handler: Optional[JWTHandler] = None,
    ):
        """
        Initialize the authentication service.

        Args:
            user_repository: Repository for user persistence
            session_repository: Repository for session persistence
            jwt_handler: Handler for JWT token operations
        """
        self._user_repository = user_repository or UserRepositoryImpl()
        self._session_repository = session_repository or SessionRepositoryImpl()
        self._jwt_handler = jwt_handler or JWTHandler()

    def register(self, username: str, email: str, password: str, full_name: str = "") -> AuthResult:
        """
        Register a new user.

        Args:
            username: Desired username
            email: User's email address
            password: Plain text password
            full_name: User's full name (optional)

        Returns:
            AuthResult with registration outcome
        """
        # Validate credentials
        credentials = Credentials(username=username, password=password)
        if not credentials.is_valid():
            return AuthResult(
                success=False,
                error_message="Username must be at least 3 characters and password at least 6 characters",
            )

        # Check if username already exists
        existing_user = self._user_repository.find_by_username(username)
        if existing_user:
            return AuthResult(success=False, error_message="Username already exists")

        # Check if email already exists
        existing_email = self._user_repository.find_by_email(email)
        if existing_email:
            return AuthResult(success=False, error_message="Email already registered")

        # Create new user
        hashed_password = PasswordHandler.hash_password(password)
        user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            full_name=full_name,
        )

        # Save user
        if not self._user_repository.save(user):
            return AuthResult(success=False, error_message="Failed to create user account")

        # Create session and token
        session = UserSession(user_id=user.id, settings=user.settings)
        self._session_repository.save(session)

        token = self._jwt_handler.create_access_token(user_id=user.id, username=user.username)

        logger.info(f"User registered: {username}")

        return AuthResult(
            success=True,
            user=user,
            token=token,
            session=session,
        )

    def login(self, username: str, password: str) -> AuthResult:
        """
        Authenticate a user with username and password.

        Args:
            username: User's username
            password: Plain text password

        Returns:
            AuthResult with login outcome
        """
        # Find user by username
        user = self._user_repository.find_by_username(username)

        # Also try email
        if not user:
            user = self._user_repository.find_by_email(username)

        if not user:
            logger.warning(f"Login failed: user not found - {username}")
            return AuthResult(success=False, error_message="Invalid username or password")

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login failed: user inactive - {username}")
            return AuthResult(success=False, error_message="Account is disabled")

        # Verify password
        if not PasswordHandler.verify_password(password, user.password_hash):
            logger.warning(f"Login failed: invalid password - {username}")
            return AuthResult(success=False, error_message="Invalid username or password")

        # Update last login
        user.update_last_login()
        self._user_repository.save(user)

        # Create or retrieve session
        session = self._session_repository.find_by_user_id(user.id)
        if not session:
            session = UserSession(user_id=user.id, settings=user.settings)
        self._session_repository.save(session)

        # Generate token
        token = self._jwt_handler.create_access_token(user_id=user.id, username=user.username)

        logger.info(f"User logged in: {username}")

        return AuthResult(
            success=True,
            user=user,
            token=token,
            session=session,
        )

    def logout(self, user_id: str) -> bool:
        """
        Log out a user by invalidating their session.

        Args:
            user_id: The user's unique identifier

        Returns:
            True if logout successful, False otherwise
        """
        try:
            self._session_repository.delete_by_user_id(user_id)
            logger.info(f"User logged out: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Logout failed for user {user_id}: {e}")
            return False

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a JWT token.

        Args:
            token: JWT token string

        Returns:
            Token payload if valid, None otherwise
        """
        return self._jwt_handler.validate_token(token)

    def refresh_token(self, refresh_token: str) -> Optional[AuthToken]:
        """
        Refresh an access token using a refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New AuthToken if successful, None otherwise
        """
        return self._jwt_handler.refresh_access_token(refresh_token)

    def get_current_user(self, user_id: str) -> Optional[User]:
        """
        Get the current user by ID.

        Args:
            user_id: The user's unique identifier

        Returns:
            User entity if found, None otherwise
        """
        return self._user_repository.find_by_id(user_id)

    def get_current_session(self, user_id: str) -> Optional[UserSession]:
        """
        Get the current session for a user.

        Args:
            user_id: The user's unique identifier

        Returns:
            UserSession if found, None otherwise
        """
        return self._session_repository.find_by_user_id(user_id)

    def update_user_settings(self, user_id: str, settings: Dict[str, Any]) -> bool:
        """
        Update user settings.

        Args:
            user_id: The user's unique identifier
            settings: New settings to merge

        Returns:
            True if successful, False otherwise
        """
        user = self._user_repository.find_by_id(user_id)
        if not user:
            return False

        user.update_settings(settings)
        return self._user_repository.save(user)

    def change_password(self, user_id: str, current_password: str, new_password: str) -> AuthResult:
        """
        Change a user's password.

        Args:
            user_id: The user's unique identifier
            current_password: Current password for verification
            new_password: New password to set

        Returns:
            AuthResult with operation outcome
        """
        user = self._user_repository.find_by_id(user_id)
        if not user:
            return AuthResult(success=False, error_message="User not found")

        # Verify current password
        if not PasswordHandler.verify_password(current_password, user.password_hash):
            return AuthResult(success=False, error_message="Current password is incorrect")

        # Validate new password
        credentials = Credentials(username=user.username, password=new_password)
        if not credentials.is_valid():
            return AuthResult(
                success=False,
                error_message="New password must be at least 6 characters",
            )

        # Update password
        user.password_hash = PasswordHandler.hash_password(new_password)
        self._user_repository.save(user)

        logger.info(f"Password changed for user: {user.username}")

        return AuthResult(success=True)

    def delete_account(self, user_id: str, password: str) -> bool:
        """
        Delete a user account after password verification.

        Args:
            user_id: The user's unique identifier
            password: Password for verification

        Returns:
            True if deleted, False otherwise
        """
        user = self._user_repository.find_by_id(user_id)
        if not user:
            return False

        # Verify password
        if not PasswordHandler.verify_password(password, user.password_hash):
            return False

        # Delete sessions first
        self._session_repository.delete_by_user_id(user_id)

        # Delete user
        result = self._user_repository.delete(user_id)

        if result:
            logger.info(f"Account deleted: {user.username}")

        return result
