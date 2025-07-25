"""
Unit tests for OpenAI Provider Authentication Module
"""

import pytest
from dlt.sources.helpers.rest_client.auth import BearerTokenAuth

from app.models.auth import AuthMethod
from providers.openai.auth import OpenAIAuth


class TestOpenAIAuth:
    """Test suite for OpenAIAuth class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.valid_config = {
            "method": AuthMethod.BEARER_TOKEN,
            "token": "sk-admin-1234567890abcdef1234567890abcdef",
        }

        self.minimal_config = {"token": "sk-1234567890abcdef"}

    def test_supported_methods(self):
        """Test supported authentication methods."""
        assert AuthMethod.BEARER_TOKEN in OpenAIAuth.SUPPORTED_METHODS
        assert len(OpenAIAuth.SUPPORTED_METHODS) == 1
        assert OpenAIAuth.DEFAULT_METHOD == AuthMethod.BEARER_TOKEN

    def test_auth_fields_structure(self):
        """Test auth fields structure for UI."""
        bearer_fields = OpenAIAuth.AUTH_FIELDS[AuthMethod.BEARER_TOKEN]
        assert "token" in bearer_fields
        assert bearer_fields["token"]["required"] is True
        assert bearer_fields["token"]["type"] == "password"
        assert "sk-admin" in bearer_fields["token"]["placeholder"]

    def test_init_with_bearer_token(self):
        """Test initialization with bearer token."""
        auth = OpenAIAuth(self.valid_config)

        assert auth.auth_config == self.valid_config
        assert auth.method == AuthMethod.BEARER_TOKEN

    def test_init_default_method(self):
        """Test initialization with default method."""
        config = {"token": "sk-test"}
        auth = OpenAIAuth(config)

        assert auth.method == OpenAIAuth.DEFAULT_METHOD

    def test_get_dlt_auth_success(self):
        """Test successful DLT auth object creation."""
        auth = OpenAIAuth(self.valid_config)
        dlt_auth = auth.get_dlt_auth()

        assert isinstance(dlt_auth, BearerTokenAuth)
        assert dlt_auth.token == "sk-admin-1234567890abcdef1234567890abcdef"

    def test_get_dlt_auth_no_token(self):
        """Test DLT auth creation with no token."""
        config = {"method": AuthMethod.BEARER_TOKEN}
        auth = OpenAIAuth(config)
        dlt_auth = auth.get_dlt_auth()

        assert dlt_auth is None

    def test_get_dlt_auth_empty_token(self):
        """Test DLT auth creation with empty token."""
        config = {"method": AuthMethod.BEARER_TOKEN, "token": ""}
        auth = OpenAIAuth(config)
        dlt_auth = auth.get_dlt_auth()

        assert dlt_auth is None

    def test_get_headers_success(self):
        """Test successful header generation."""
        auth = OpenAIAuth(self.valid_config)
        headers = auth.get_headers()

        expected = {"Authorization": "Bearer sk-admin-1234567890abcdef1234567890abcdef"}
        assert headers == expected

    def test_get_headers_no_token(self):
        """Test header generation with no token."""
        config = {"method": AuthMethod.BEARER_TOKEN}
        auth = OpenAIAuth(config)
        headers = auth.get_headers()

        assert headers == {}

    def test_get_headers_empty_token(self):
        """Test header generation with empty token."""
        config = {"method": AuthMethod.BEARER_TOKEN, "token": ""}
        auth = OpenAIAuth(config)
        headers = auth.get_headers()

        assert headers == {}

    def test_validate_success(self):
        """Test successful validation."""
        auth = OpenAIAuth(self.valid_config)
        auth.validate()  # Should not raise

    def test_validate_minimal_config(self):
        """Test validation with minimal config."""
        auth = OpenAIAuth(self.minimal_config)
        auth.validate()  # Should not raise

    def test_validate_no_config(self):
        """Test validation with no config."""
        auth = OpenAIAuth({})

        with pytest.raises(
            ValueError, match="Authentication configuration is required"
        ):
            auth.validate()

    def test_validate_none_config(self):
        """Test validation with None config."""
        with pytest.raises(AttributeError):
            OpenAIAuth(None)

    def test_validate_unsupported_method(self):
        """Test validation with unsupported method."""
        config = {"method": "UNSUPPORTED_METHOD", "token": "sk-test"}
        auth = OpenAIAuth(config)

        with pytest.raises(
            ValueError,
            match="OpenAI only supports AuthMethod.BEARER_TOKEN authentication",
        ):
            auth.validate()

    def test_validate_missing_token(self):
        """Test validation with missing token."""
        config = {"method": AuthMethod.BEARER_TOKEN}
        auth = OpenAIAuth(config)

        with pytest.raises(ValueError, match="Bearer token is required"):
            auth.validate()

    def test_validate_empty_token(self):
        """Test validation with empty token."""
        config = {"method": AuthMethod.BEARER_TOKEN, "token": ""}
        auth = OpenAIAuth(config)

        with pytest.raises(ValueError, match="Bearer token is required"):
            auth.validate()

    def test_validate_whitespace_token(self):
        """Test validation with whitespace-only token."""
        config = {"method": AuthMethod.BEARER_TOKEN, "token": "   "}
        auth = OpenAIAuth(config)

        auth.validate()

    def test_auth_config_immutability(self):
        """Test that auth_config is stored correctly."""
        original_config = self.valid_config.copy()
        auth = OpenAIAuth(original_config)

        original_config["token"] = "modified"
        assert auth.auth_config["token"] == "modified"

    @pytest.mark.parametrize(
        "token,expected_auth_type",
        [
            ("sk-1234567890abcdef", BearerTokenAuth),
            ("sk-admin-abcdef1234567890", BearerTokenAuth),
            ("sk-proj-1234567890abcdef", BearerTokenAuth),
        ],
    )
    def test_different_token_formats(self, token, expected_auth_type):
        """Test different OpenAI token formats."""
        config = {"method": AuthMethod.BEARER_TOKEN, "token": token}
        auth = OpenAIAuth(config)

        dlt_auth = auth.get_dlt_auth()
        assert isinstance(dlt_auth, expected_auth_type)
        assert dlt_auth.token == token

        headers = auth.get_headers()
        assert headers == {"Authorization": f"Bearer {token}"}

    def test_valid_method_validation(self):
        """Test that valid method passes validation."""
        config = {"method": AuthMethod.BEARER_TOKEN, "token": "sk-test"}
        auth = OpenAIAuth(config)
        auth.validate()  # Should not raise

    def test_bearer_token_auth_creation(self):
        """Test that BearerTokenAuth is created with correct token."""
        auth = OpenAIAuth(self.valid_config)
        dlt_auth = auth.get_dlt_auth()

        assert isinstance(dlt_auth, BearerTokenAuth)
        assert hasattr(dlt_auth, "token")
        assert dlt_auth.token == self.valid_config["token"]

    def test_config_access_patterns(self):
        """Test different ways of accessing config values."""
        config = {"method": AuthMethod.BEARER_TOKEN, "token": "sk-test-token"}
        auth = OpenAIAuth(config)

        assert auth.auth_config.get("token") == "sk-test-token"
        assert auth.auth_config.get("missing_key") is None
        assert auth.auth_config["token"] == "sk-test-token"
        assert auth.method == AuthMethod.BEARER_TOKEN
