"""
JWT Handler - JWT token generation and validation with password hashing.
Provides secure authentication using industry-standard algorithms.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib
import secrets
import hmac
import base64
import json
import os
import logging

logger = logging.getLogger(__name__)


@dataclass
class AuthToken:
    """
    Value object representing an authentication token.
    Contains the token string and metadata.
    """

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # 1 hour
    refresh_token: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize token to dictionary."""
        return {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
            "refresh_token": self.refresh_token,
        }


class PasswordHandler:
    """
    Handles secure password hashing and verification.
    Uses PBKDF2 with SHA-256 for password hashing.
    """

    ITERATIONS = 100000
    SALT_LENGTH = 32
    HASH_LENGTH = 64

    @classmethod
    def hash_password(cls, password: str) -> str:
        """
        Hash a password using PBKDF2-SHA256.

        Args:
            password: Plain text password

        Returns:
            Hashed password string (format: iterations$salt$hash)
        """
        salt = secrets.token_bytes(cls.SALT_LENGTH)
        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            cls.ITERATIONS,
            dklen=cls.HASH_LENGTH,
        )
        # Format: iterations$salt$hash (all hex encoded)
        return f"{cls.ITERATIONS}${salt.hex()}${key.hex()}"

    @classmethod
    def verify_password(cls, password: str, hashed: str) -> bool:
        """
        Verify a password against a stored hash.

        Args:
            password: Plain text password to verify
            hashed: Stored password hash

        Returns:
            True if password matches, False otherwise
        """
        try:
            parts = hashed.split("$")
            if len(parts) != 3:
                logger.warning("Invalid hash format")
                return False

            iterations = int(parts[0])
            salt = bytes.fromhex(parts[1])
            stored_key = bytes.fromhex(parts[2])

            # Compute hash with same parameters
            computed_key = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt,
                iterations,
                dklen=len(stored_key),
            )

            # Use constant-time comparison
            return hmac.compare_digest(computed_key, stored_key)

        except (ValueError, TypeError) as e:
            logger.error(f"Error verifying password: {e}")
            return False


class JWTHandler:
    """
    Handles JWT token generation and validation.
    Implements a simple JWT implementation without external dependencies.
    """

    ACCESS_TOKEN_EXPIRY_HOURS = 1
    REFRESH_TOKEN_EXPIRY_DAYS = 7

    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize the JWT handler.

        Args:
            secret_key: Secret key for signing tokens. If not provided,
                       uses environment variable JWT_SECRET_KEY or generates one.
        """
        self.secret_key = secret_key or os.getenv(
            "JWT_SECRET_KEY", secrets.token_urlsafe(64)
        )
        self.algorithm = "HS256"

    def create_access_token(
        self,
        user_id: str,
        username: str,
        additional_claims: Optional[Dict[str, Any]] = None,
    ) -> AuthToken:
        """
        Create a new access token for a user.

        Args:
            user_id: The user's unique identifier
            username: The user's username
            additional_claims: Optional additional claims to include

        Returns:
            AuthToken with the generated token
        """
        now = datetime.utcnow()
        expiry = now + timedelta(hours=self.ACCESS_TOKEN_EXPIRY_HOURS)

        payload = {
            "sub": user_id,
            "username": username,
            "iat": int(now.timestamp()),
            "exp": int(expiry.timestamp()),
            "type": "access",
        }

        if additional_claims:
            payload.update(additional_claims)

        token = self._encode(payload)

        refresh_token = self._create_refresh_token(user_id)

        return AuthToken(
            access_token=token,
            expires_in=self.ACCESS_TOKEN_EXPIRY_HOURS * 3600,
            refresh_token=refresh_token,
        )

    def _create_refresh_token(self, user_id: str) -> str:
        """
        Create a refresh token for a user.

        Args:
            user_id: The user's unique identifier

        Returns:
            Refresh token string
        """
        now = datetime.utcnow()
        expiry = now + timedelta(days=self.REFRESH_TOKEN_EXPIRY_DAYS)

        payload = {
            "sub": user_id,
            "iat": int(now.timestamp()),
            "exp": int(expiry.timestamp()),
            "type": "refresh",
        }

        return self._encode(payload)

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a JWT token and return its payload.

        Args:
            token: JWT token string

        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = self._decode(token)

            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.utcnow().timestamp() > exp:
                logger.debug("Token has expired")
                return None

            return payload

        except Exception as e:
            logger.debug(f"Token validation failed: {e}")
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[AuthToken]:
        """
        Create a new access token using a refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New AuthToken if refresh token is valid, None otherwise
        """
        payload = self.validate_token(refresh_token)

        if not payload or payload.get("type") != "refresh":
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        return self.create_access_token(
            user_id=user_id,
            username=payload.get("username", ""),
        )

    def revoke_token(self, token: str) -> bool:
        """
        Mark a token as revoked (for future invalidation).
        In a production system, this would store revoked tokens in a database.

        Args:
            token: Token to revoke

        Returns:
            True if successful
        """
        # In a full implementation, store the token in a revocation list
        # For now, we rely on expiration
        return True

    def _encode(self, payload: Dict[str, Any]) -> str:
        """
        Encode a payload into a JWT token.

        Args:
            payload: Data to encode

        Returns:
            JWT token string
        """
        # Create header
        header = {"alg": self.algorithm, "typ": "JWT"}
        header_b64 = self._base64_encode(json.dumps(header))
        payload_b64 = self._base64_encode(json.dumps(payload))

        # Create signature
        message = f"{header_b64}.{payload_b64}"
        signature = self._sign(message)

        return f"{message}.{signature}"

    def _decode(self, token: str) -> Dict[str, Any]:
        """
        Decode and verify a JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded payload

        Raises:
            ValueError: If token is invalid or signature doesn't match
        """
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid token format")

        header_b64, payload_b64, signature = parts

        # Verify signature
        message = f"{header_b64}.{payload_b64}"
        expected_signature = self._sign(message)

        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid signature")

        # Decode payload
        payload_json = self._base64_decode(payload_b64)
        return json.loads(payload_json)

    def _sign(self, message: str) -> str:
        """
        Sign a message using HMAC-SHA256.

        Args:
            message: Message to sign

        Returns:
            Base64-encoded signature
        """
        signature = hmac.new(
            self.secret_key.encode(), message.encode(), hashlib.sha256
        ).digest()
        return self._base64_encode_bytes(signature)

    def _base64_encode(self, data: str) -> str:
        """Encode string data to base64url."""
        return self._base64_encode_bytes(data.encode())

    def _base64_encode_bytes(self, data: bytes) -> str:
        """Encode bytes to base64url."""
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    def _base64_decode(self, data: str) -> str:
        """Decode base64url to string."""
        # Add padding if needed
        padding = 4 - len(data) % 4
        if padding != 4:
            data += "=" * padding

        return base64.urlsafe_b64decode(data).decode()
