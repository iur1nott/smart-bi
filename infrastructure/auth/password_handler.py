"""
Password Handler - Secure password hashing and verification.
Implements bcrypt-based password management.
"""

from typing import Optional
import secrets
import string
import hashlib
import logging
import base64

try:
    import bcrypt

    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False
    import hashlib
    import hmac

logger = logging.getLogger(__name__)


class PasswordHandler:
    """
    Handles secure password hashing and verification.
    Uses bcrypt when available, falls back to HMAC-SHA256.
    """

    # Bcrypt work factor (cost) - higher is more secure but slower
    BCRYPT_ROUNDS = 12

    @classmethod
    def hash_password(cls, password: str) -> str:
        """
        Hash a password securely.

        Args:
            password: Plain text password to hash

        Returns:
            Hashed password string
        """
        if not password:
            raise ValueError("Password cannot be empty")

        if HAS_BCRYPT:
            # Use bcrypt for secure password hashing
            salt = bcrypt.gensalt(rounds=cls.BCRYPT_ROUNDS)
            hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
            return hashed.decode("utf-8")
        else:
            # Fallback to HMAC-SHA256 with salt
            return cls._hash_with_hmac(password)

    @classmethod
    def verify_password(cls, password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            password: Plain text password to verify
            hashed_password: Stored password hash

        Returns:
            True if password matches, False otherwise
        """
        if not password or not hashed_password:
            return False

        try:
            if HAS_BCRYPT:
                # Check if it's a bcrypt hash
                if hashed_password.startswith("$2"):
                    return bcrypt.checkpw(
                        password.encode("utf-8"),
                        hashed_password.encode("utf-8"),
                    )

            # Try HMAC verification for fallback hashes
            return cls._verify_hmac(password, hashed_password)

        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False

    @classmethod
    def generate_random_password(cls, length: int = 16) -> str:
        """
        Generate a secure random password.

        Args:
            length: Desired password length

        Returns:
            Random password string
        """
        if length < 8:
            length = 8

        # Use alphanumeric characters
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"

        # Ensure at least one of each character type
        password = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
            secrets.choice("!@#$%^&*"),
        ]

        # Fill remaining length
        for _ in range(length - 4):
            password.append(secrets.choice(alphabet))

        # Shuffle the password
        secrets.SystemRandom().shuffle(password)
        return "".join(password)

    @classmethod
    def generate_reset_token(cls) -> str:
        """
        Generate a secure token for password reset.

        Returns:
            URL-safe random token
        """
        return secrets.token_urlsafe(32)

    @classmethod
    def validate_password_strength(cls, password: str) -> dict:
        """
        Validate password strength and return feedback.

        Args:
            password: Password to validate

        Returns:
            Dictionary with validation results
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "strength": "strong",
        }

        # Check minimum length
        if len(password) < 8:
            result["valid"] = False
            result["errors"].append("Password must be at least 8 characters long")

        # Check for uppercase
        if not any(c.isupper() for c in password):
            result["warnings"].append("Consider adding uppercase letters for better security")

        # Check for lowercase
        if not any(c.islower() for c in password):
            result["warnings"].append("Consider adding lowercase letters for better security")

        # Check for digits
        if not any(c.isdigit() for c in password):
            result["warnings"].append("Consider adding numbers for better security")

        # Check for special characters
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            result["warnings"].append("Consider adding special characters for better security")

        # Determine strength
        if len(result["warnings"]) >= 3:
            result["strength"] = "weak"
        elif len(result["warnings"]) >= 1:
            result["strength"] = "medium"

        return result

    @classmethod
    def _hash_with_hmac(cls, password: str) -> str:
        """
        Hash password using HMAC-SHA256 (fallback method).

        Args:
            password: Plain text password

        Returns:
            HMAC-based hash string
        """
        # Generate a random salt
        salt = secrets.token_hex(16)

        # Create HMAC hash
        key = hashlib.sha256(salt.encode()).digest()
        hashed = hmac.new(key, password.encode(), hashlib.sha256).hexdigest()

        # Format: $hmac$<salt>$<hash>
        return f"$hmac${salt}${hashed}"

    @classmethod
    def _verify_hmac(cls, password: str, hashed_password: str) -> bool:
        """
        Verify password against HMAC hash.

        Args:
            password: Plain text password
            hashed_password: Stored HMAC hash

        Returns:
            True if valid, False otherwise
        """
        try:
            # Parse the hash format
            parts = hashed_password.split("$")
            if len(parts) != 4 or parts[1] != "hmac":
                return False

            salt = parts[2]
            stored_hash = parts[3]

            # Recompute hash
            key = hashlib.sha256(salt.encode()).digest()
            computed_hash = hmac.new(key, password.encode(), hashlib.sha256).hexdigest()

            # Use constant-time comparison
            return secrets.compare_digest(stored_hash, computed_hash)

        except Exception:
            return False

    @classmethod
    def needs_rehash(cls, hashed_password: str) -> bool:
        """
        Check if a password hash needs to be rehashed.

        This is useful when upgrading hashing algorithms or parameters.

        Args:
            hashed_password: Current password hash

        Returns:
            True if rehashing is recommended
        """
        if HAS_BCRYPT and not hashed_password.startswith("$2"):
            return True

        # Check bcrypt rounds
        if hashed_password.startswith("$2"):
            try:
                # Extract rounds from bcrypt hash
                parts = hashed_password.split("$")
                if len(parts) >= 3:
                    rounds = int(parts[2])
                    return rounds < cls.BCRYPT_ROUNDS
            except (ValueError, IndexError):
                return True

        return False
