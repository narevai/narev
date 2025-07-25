"""
Unit tests for Azure Provider Authentication Module
"""

from unittest.mock import Mock, patch

import pytest
from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobServiceClient

from app.models.auth import AuthMethod
from providers.azure.auth import AzureAuth


class TestAzureAuth:
    """Test suite for AzureAuth class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.valid_api_key_config = {
            "method": AuthMethod.API_KEY,
            "key": "test-storage-key-123456789abcdef",
        }

        self.valid_oauth_config = {
            "method": AuthMethod.OAUTH2_CLIENT_CREDENTIALS,
            "tenant_id": "12345678-1234-1234-1234-123456789012",
            "client_id": "87654321-4321-4321-4321-210987654321",
            "client_secret": "test-client-secret-value",
        }

    def test_supported_methods(self):
        """Test supported authentication methods."""
        assert AuthMethod.API_KEY in AzureAuth.SUPPORTED_METHODS
        assert AuthMethod.OAUTH2_CLIENT_CREDENTIALS in AzureAuth.SUPPORTED_METHODS
        assert AzureAuth.DEFAULT_METHOD == AuthMethod.API_KEY

    def test_auth_fields_structure(self):
        """Test auth fields structure for UI."""
        # API Key fields
        api_key_fields = AzureAuth.AUTH_FIELDS[AuthMethod.API_KEY]
        assert "key" in api_key_fields
        assert api_key_fields["key"]["required"] is True
        assert api_key_fields["key"]["type"] == "password"

        # OAuth fields
        oauth_fields = AzureAuth.AUTH_FIELDS[AuthMethod.OAUTH2_CLIENT_CREDENTIALS]
        assert "tenant_id" in oauth_fields
        assert "client_id" in oauth_fields
        assert "client_secret" in oauth_fields
        assert oauth_fields["tenant_id"]["required"] is True

    def test_init_with_api_key(self):
        """Test initialization with API key authentication."""
        auth = AzureAuth(self.valid_api_key_config, "teststorage")

        assert auth.auth_config == self.valid_api_key_config
        assert auth.method == AuthMethod.API_KEY
        assert auth.storage_account == "teststorage"

    def test_init_with_oauth(self):
        """Test initialization with OAuth authentication."""
        auth = AzureAuth(self.valid_oauth_config)

        assert auth.auth_config == self.valid_oauth_config
        assert auth.method == AuthMethod.OAUTH2_CLIENT_CREDENTIALS
        assert auth.storage_account is None

    def test_init_default_method(self):
        """Test initialization with default method."""
        config = {"key": "test-key"}
        auth = AzureAuth(config)

        assert auth.method == AzureAuth.DEFAULT_METHOD

    def test_get_storage_key_success(self):
        """Test successful storage key retrieval."""
        auth = AzureAuth(self.valid_api_key_config)
        key = auth.get_storage_key()

        assert key == "test-storage-key-123456789abcdef"

    def test_get_storage_key_wrong_method(self):
        """Test storage key retrieval with wrong method."""
        auth = AzureAuth(self.valid_oauth_config)
        key = auth.get_storage_key()

        assert key is None

    def test_get_storage_key_missing(self):
        """Test storage key retrieval when key is missing."""
        config = {"method": AuthMethod.API_KEY}
        auth = AzureAuth(config)
        key = auth.get_storage_key()

        assert key is None

    @patch("providers.azure.auth.ClientSecretCredential")
    def test_get_credential_success(self, mock_credential_class):
        """Test successful credential creation."""
        mock_credential = Mock(spec=ClientSecretCredential)
        mock_credential_class.return_value = mock_credential

        auth = AzureAuth(self.valid_oauth_config)
        credential = auth.get_credential()

        assert credential == mock_credential
        mock_credential_class.assert_called_once_with(
            tenant_id="12345678-1234-1234-1234-123456789012",
            client_id="87654321-4321-4321-4321-210987654321",
            client_secret="test-client-secret-value",
        )

    @patch("providers.azure.auth.ClientSecretCredential")
    def test_get_credential_cached(self, mock_credential_class):
        """Test credential caching."""
        mock_credential = Mock(spec=ClientSecretCredential)
        mock_credential_class.return_value = mock_credential

        auth = AzureAuth(self.valid_oauth_config)

        # First call
        credential1 = auth.get_credential()
        # Second call should return cached credential
        credential2 = auth.get_credential()

        assert credential1 == credential2
        mock_credential_class.assert_called_once()

    def test_get_credential_wrong_method(self):
        """Test credential retrieval with wrong method."""
        auth = AzureAuth(self.valid_api_key_config)
        credential = auth.get_credential()

        assert credential is None

    def test_get_credential_missing_fields(self):
        """Test credential creation with missing fields."""
        incomplete_config = {
            "method": AuthMethod.OAUTH2_CLIENT_CREDENTIALS,
            "tenant_id": "12345678-1234-1234-1234-123456789012",
            "client_id": "87654321-4321-4321-4321-210987654321",
            # missing client_secret
        }
        auth = AzureAuth(incomplete_config)

        with pytest.raises(
            ValueError, match="tenant_id, client_id, and client_secret are required"
        ):
            auth.get_credential()

    @patch("providers.azure.auth.BlobServiceClient")
    def test_create_blob_service_client_with_key(self, mock_blob_client_class):
        """Test blob service client creation with API key."""
        mock_client = Mock(spec=BlobServiceClient)
        mock_blob_client_class.return_value = mock_client

        auth = AzureAuth(self.valid_api_key_config, "teststorage")
        client = auth.create_blob_service_client()

        assert client == mock_client
        mock_blob_client_class.assert_called_once_with(
            account_url="https://teststorage.blob.core.windows.net",
            credential="test-storage-key-123456789abcdef",
        )

    @patch("providers.azure.auth.BlobServiceClient")
    @patch("providers.azure.auth.ClientSecretCredential")
    def test_create_blob_service_client_with_oauth(
        self, mock_credential_class, mock_blob_client_class
    ):
        """Test blob service client creation with OAuth."""
        mock_credential = Mock(spec=ClientSecretCredential)
        mock_credential_class.return_value = mock_credential
        mock_client = Mock(spec=BlobServiceClient)
        mock_blob_client_class.return_value = mock_client

        auth = AzureAuth(self.valid_oauth_config, "teststorage")
        client = auth.create_blob_service_client()

        assert client == mock_client
        mock_blob_client_class.assert_called_once_with(
            account_url="https://teststorage.blob.core.windows.net",
            credential=mock_credential,
        )

    @patch("providers.azure.auth.BlobServiceClient")
    def test_create_blob_service_client_override_storage(self, mock_blob_client_class):
        """Test blob service client creation with storage account override."""
        mock_client = Mock(spec=BlobServiceClient)
        mock_blob_client_class.return_value = mock_client

        auth = AzureAuth(self.valid_api_key_config, "defaultstorage")
        auth.create_blob_service_client("overridestorage")

        mock_blob_client_class.assert_called_once_with(
            account_url="https://overridestorage.blob.core.windows.net",
            credential="test-storage-key-123456789abcdef",
        )

    def test_create_blob_service_client_no_storage_account(self):
        """Test blob service client creation without storage account."""
        auth = AzureAuth(self.valid_api_key_config)

        with pytest.raises(ValueError, match="Storage account name is required"):
            auth.create_blob_service_client()

    def test_create_blob_service_client_no_key(self):
        """Test blob service client creation without storage key."""
        config = {"method": AuthMethod.API_KEY}
        auth = AzureAuth(config, "teststorage")

        with pytest.raises(ValueError, match="Storage account key is required"):
            auth.create_blob_service_client()

    def test_create_blob_service_client_unsupported_method(self):
        """Test blob service client creation with unsupported method."""
        config = {"method": "UNSUPPORTED_METHOD"}
        auth = AzureAuth(config, "teststorage")

        with pytest.raises(ValueError, match="Unsupported auth method"):
            auth.create_blob_service_client()

    def test_validate_success_api_key(self):
        """Test successful validation with API key."""
        auth = AzureAuth(self.valid_api_key_config)
        auth.validate()  # Should not raise

    def test_validate_success_oauth(self):
        """Test successful validation with OAuth."""
        auth = AzureAuth(self.valid_oauth_config)
        auth.validate()  # Should not raise

    def test_validate_no_config(self):
        """Test validation with no config."""
        auth = AzureAuth({})

        with pytest.raises(
            ValueError, match="Authentication configuration is required"
        ):
            auth.validate()

    def test_validate_unsupported_method(self):
        """Test validation with unsupported method."""
        config = {"method": "UNSUPPORTED_METHOD", "key": "test"}
        auth = AzureAuth(config)

        with pytest.raises(ValueError, match="Unsupported auth method"):
            auth.validate()

    def test_validate_api_key_missing_key(self):
        """Test validation with API key method but missing key."""
        config = {"method": AuthMethod.API_KEY}
        auth = AzureAuth(config)

        with pytest.raises(ValueError, match="Storage account key is required"):
            auth.validate()

    def test_validate_oauth_missing_fields(self):
        """Test validation with OAuth method but missing fields."""
        config = {
            "method": AuthMethod.OAUTH2_CLIENT_CREDENTIALS,
            "tenant_id": "12345678-1234-1234-1234-123456789012",
            # missing client_id and client_secret
        }
        auth = AzureAuth(config)

        with pytest.raises(
            ValueError, match="Missing required fields: client_id, client_secret"
        ):
            auth.validate()

    def test_get_filesystem_config_api_key(self):
        """Test filesystem config generation for API key."""
        auth = AzureAuth(self.valid_api_key_config, "teststorage")
        config = auth.get_filesystem_config()

        expected = {
            "azure_storage_account_key": "test-storage-key-123456789abcdef",
            "azure_storage_account_name": "teststorage",
        }
        assert config == expected

    def test_get_filesystem_config_api_key_no_storage_account(self):
        """Test filesystem config without storage account name."""
        auth = AzureAuth(self.valid_api_key_config)
        config = auth.get_filesystem_config()

        expected = {"azure_storage_account_key": "test-storage-key-123456789abcdef"}
        assert config == expected

    def test_get_filesystem_config_api_key_no_key(self):
        """Test filesystem config with API key method but no key."""
        config = {"method": AuthMethod.API_KEY}
        auth = AzureAuth(config, "teststorage")
        fs_config = auth.get_filesystem_config()

        assert fs_config == {}

    @patch("providers.azure.auth.logger")
    def test_get_filesystem_config_oauth_warning(self, mock_logger):
        """Test filesystem config with OAuth method shows warning."""
        auth = AzureAuth(self.valid_oauth_config)
        config = auth.get_filesystem_config()

        assert config == {}
        mock_logger.warning.assert_called_once_with(
            "Service Principal auth for filesystem operations may require custom implementation"
        )
