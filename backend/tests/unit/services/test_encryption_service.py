"""
Tests for EncryptionService
"""

from unittest.mock import Mock, patch

import pytest
from cryptography.fernet import Fernet

from app.services.encryption_service import EncryptionService


class TestEncryptionService:
    """Test cases for EncryptionService."""

    @pytest.fixture
    def encryption_service(self):
        """Create encryption service instance with mocked settings."""
        with patch("app.services.encryption_service.get_settings") as mock_settings:
            mock_settings.return_value.encryption_key = Fernet.generate_key().decode()
            service = EncryptionService()
            return service

    def test_encrypt_decrypt_string(self, encryption_service):
        """Test encrypting and decrypting a string."""
        original_text = "This is a secret API key"

        # Encrypt
        encrypted = encryption_service.encrypt(original_text)
        assert encrypted != original_text
        assert isinstance(encrypted, str)
        assert len(encrypted) > 0

        # Decrypt
        decrypted = encryption_service.decrypt(encrypted)
        assert decrypted == original_text

    def test_encrypt_empty_string(self, encryption_service):
        """Test encrypting empty string."""
        encrypted = encryption_service.encrypt("")
        assert encrypted == ""

    def test_decrypt_empty_string(self, encryption_service):
        """Test decrypting empty string."""
        decrypted = encryption_service.decrypt("")
        assert decrypted == ""

    def test_encrypt_unicode_string(self, encryption_service):
        """Test encrypting string with unicode characters."""
        original_text = "API key with émojis 🔐🔑"

        encrypted = encryption_service.encrypt(original_text)
        decrypted = encryption_service.decrypt(encrypted)

        assert decrypted == original_text

    def test_decrypt_invalid_ciphertext(self, encryption_service):
        """Test decrypting invalid ciphertext."""
        # Invalid ciphertext should return empty string (as per implementation)
        decrypted = encryption_service.decrypt("invalid-ciphertext")
        assert decrypted == ""

    def test_encrypt_dict(self, encryption_service):
        """Test encrypting dictionary values."""
        original_dict = {
            "api_key": "secret-key-123",
            "password": "secret-password",
            "token": "bearer-token-456",
        }

        encrypted_dict = encryption_service.encrypt_dict(original_dict)

        # All values should be encrypted
        assert all(encrypted_dict[key] != original_dict[key] for key in original_dict)
        assert all(isinstance(value, str) for value in encrypted_dict.values())

        # Should be able to decrypt each value
        for key in original_dict:
            decrypted = encryption_service.decrypt(encrypted_dict[key])
            assert decrypted == original_dict[key]

    def test_encrypt_dict_with_non_string_values(self, encryption_service):
        """Test encrypting dictionary with non-string values."""
        original_dict = {
            "string_value": "test",
            "int_value": 42,
            "float_value": 3.14,
            "bool_value": True,
        }

        encrypted_dict = encryption_service.encrypt_dict(original_dict)

        # All values should be converted to string and encrypted
        assert all(isinstance(value, str) for value in encrypted_dict.values())

        # Decrypt and verify
        decrypted_values = {
            key: encryption_service.decrypt(value)
            for key, value in encrypted_dict.items()
        }

        assert decrypted_values["string_value"] == "test"
        assert decrypted_values["int_value"] == "42"
        assert decrypted_values["float_value"] == "3.14"
        assert decrypted_values["bool_value"] == "True"

    def test_decrypt_dict(self, encryption_service):
        """Test decrypting dictionary values."""
        # First encrypt a dict
        original_dict = {"api_key": "secret-key-123", "password": "secret-password"}
        encrypted_dict = encryption_service.encrypt_dict(original_dict)

        # Now decrypt it
        decrypted_dict = encryption_service.decrypt_dict(encrypted_dict)

        assert decrypted_dict == original_dict

    def test_get_encryption_key_invalid(self):
        """Test handling invalid encryption key in environment."""
        # Create a mock settings object
        mock_settings_obj = Mock()
        mock_settings_obj.encryption_key = "invalid-key-not-base64"

        # Patch the actual location where get_settings is imported in encryption_service
        with patch(
            "app.services.encryption_service.get_settings",
            return_value=mock_settings_obj,
        ):
            # Should raise ValueError for invalid key format
            with pytest.raises(ValueError, match="Invalid encryption key format"):
                from app.services.encryption_service import EncryptionService

                EncryptionService()

    def test_get_encryption_key_missing(self):
        """Test handling missing encryption key in environment."""
        # Create a mock settings object
        mock_settings_obj = Mock()
        mock_settings_obj.encryption_key = None

        # Patch the actual location where get_settings is imported
        with patch(
            "app.services.encryption_service.get_settings",
            return_value=mock_settings_obj,
        ):
            # Should raise ValueError for missing key
            with pytest.raises(ValueError, match="Encryption key not found"):
                from app.services.encryption_service import EncryptionService

                EncryptionService()

    def test_encrypt_large_string(self, encryption_service):
        """Test encrypting large string."""
        # Create a large string (1MB)
        large_text = "A" * (1024 * 1024)

        encrypted = encryption_service.encrypt(large_text)
        decrypted = encryption_service.decrypt(encrypted)

        assert decrypted == large_text

    def test_multiple_encrypt_decrypt_cycles(self, encryption_service):
        """Test multiple encryption/decryption cycles."""
        original_text = "test-api-key"

        # Multiple cycles should work correctly
        current_text = original_text
        for _ in range(5):
            encrypted = encryption_service.encrypt(current_text)
            current_text = encryption_service.decrypt(encrypted)

        assert current_text == original_text
