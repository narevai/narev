"""
Encryption Service for API keys and sensitive data
"""

import logging
from typing import Any

from cryptography.fernet import Fernet

from app.config import get_settings

logger = logging.getLogger(__name__)


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""

    def __init__(self):
        """Initialize encryption service."""
        self._encryption_key = self._get_encryption_key()
        self._fernet = Fernet(self._encryption_key)

    def _get_encryption_key(self) -> bytes:
        """Get encryption key from settings."""
        settings = get_settings()

        # Get key from environment
        key_from_env = settings.encryption_key
        if not key_from_env:
            raise ValueError(
                "Encryption key not found in settings. Please set ENCRYPTION_KEY environment variable."
            )

        try:
            # Encode the key
            key_bytes = key_from_env.encode()

            # Validate it's a valid Fernet key by trying to create Fernet instance
            # This will raise ValueError if the key is not valid
            Fernet(key_bytes)

            return key_bytes
        except Exception as e:
            logger.error(f"Invalid encryption key in environment: {e}")
            raise ValueError(f"Invalid encryption key format: {e}") from e

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string.

        Args:
            plaintext: String to encrypt

        Returns:
            Encrypted string
        """
        if not plaintext:
            return ""

        try:
            return self._fernet.encrypt(plaintext.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt data: {e}")
            raise

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext string.

        Args:
            ciphertext: Encrypted string

        Returns:
            Decrypted string
        """
        if not ciphertext:
            return ""

        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            return ""

    def encrypt_dict(self, data: dict[str, Any]) -> dict[str, str]:
        """
        Encrypt dictionary values.

        Args:
            data: Dictionary with values to encrypt

        Returns:
            Dictionary with encrypted values
        """
        encrypted = {}
        for key, value in data.items():
            if isinstance(value, str):
                encrypted[key] = self.encrypt(value)
            else:
                # Convert to string and encrypt
                encrypted[key] = self.encrypt(str(value))
        return encrypted

    def decrypt_dict(self, data: dict[str, str]) -> dict[str, str]:
        """
        Decrypt dictionary values.

        Args:
            data: Dictionary with encrypted values

        Returns:
            Dictionary with decrypted values
        """
        decrypted = {}
        for key, value in data.items():
            decrypted[key] = self.decrypt(value)
        return decrypted
