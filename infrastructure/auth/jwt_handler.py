"""
JWT Handler - Handles JWT token creation, validation, and refresh.
Implements secure token management for authentication.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import secrets
import hashlib
import jwt
import logging
import os

logger = logging.getLogger(__name__)


@dataclass
class AuthToken:
    """
    Value object representing an authentication token pair.
    Contains both access and refresh tokens.
    """

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600  # 1 hour in seconds

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
        }


class JWTHandler:
    """
    Handles JWT token operations following security best practices.
    Implements access/refresh token pattern with token rotation.
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 60,
        refresh_token_expire_days: int = 7,
    ):
        """
        Initialize the JWT handler.

        Args:
            secret_key: Secret key for signing tokens. Uses JWT_SECRET_KEY env var if not provided.
            algorithm: JWT signing algorithm
            access_token_expire_minutes: Access token expiration time in minutes
            refresh_token_expire_days: Refresh token expiration time in days
        """
        self.secret_key = secret_key or os.getenv(
            "JWT_SECRET_KEY", "your-super-secret-key-change-in-production"
        )
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days

    def create_access_token(
        self,
        user_id: str,
        username: str,
        additional_claims: Optional[Dict[str, Any]] = None,
    ) -> AuthToken:
        """
        Create a new access token and refresh token pair.

        Args:
            user_id: The unique identifier of the user
            username: The username of the user
            additional_claims: Optional additional claims to include in the token

        Returns:
            AuthToken object with access and refresh tokens
        """
        now = datetime.utcnow()

        # Create access token
        access_payload = {
            "sub": user_id,
            "username": username,
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=self.access_token_expire_minutes),
            "jti": secrets.token_urlsafe(16),  # Unique token ID
        }

        if additional_claims:
            access_payload.update(additional_claims)

        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)

        # Create refresh token
        refresh_payload = {
            "sub": user_id,
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(days=self.refresh_token_expire_days),
            "jti": secrets.token_urlsafe(16),
        }

        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)

        return AuthToken(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.access_token_expire_minutes * 60,
        )

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a JWT token and return its payload.

        Args:
            token: The JWT token to validate

        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"require": ["sub", "exp", "iat"]},
            )

            # Check if token is expired
            if datetime.utcnow() > datetime.fromtimestamp(payload["exp"]):
                logger.debug("Token has expired")
                return None

            return payload

        except jwt.ExpiredSignatureError:
            logger.debug("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.debug(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[AuthToken]:
        """
        Create a new access token using a valid refresh token.

        Args:
            refresh_token: The refresh token to use

        Returns:
            New AuthToken if refresh token is valid, None otherwise
        """
        payload = self.validate_token(refresh_token)

        if not payload:
            return None

        # Verify this is a refresh token
        if payload.get("type") != "refresh":
            logger.warning("Attempted to refresh with non-refresh token")
            return None

        # Create new token pair
        user_id = payload.get("sub")
        if not user_id:
            return None

        return self.create_access_token(
            user_id=user_id,
            username=payload.get("username", ""),
        )

    def get_token_hash(self, token: str) -> str:
        """
        Generate a hash of the token for storage.

        Args:
            token: The token to hash

        Returns:
            SHA-256 hash of the token
        """
        return hashlib.sha256(token.encode()).hexdigest()

    def extract_user_id(self, token: str) -> Optional[str]:
        """
        Extract user ID from a token without full validation.

        Useful for logging and quick identification.

        Args:
            token: The JWT token

        Returns:
            User ID if present in token, None otherwise
        """
        try:
            # Decode without verification (for ID extraction only)
            payload = jwt.decode(
                token,
                options={"verify_signature": False},
            )
            return payload.get("sub")
        except Exception:
            return None

    def decode_token_unsafe(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode a token without verification.
        WARNING: Only use for debugging or logging, never for authentication!

        Args:
            token: The JWT token

        Returns:
            Token payload without verification
        """
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception:
            return None
