"""
Unit tests for Azure Provider Implementation
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from azure.core.exceptions import AzureError
from azure.storage.blob import BlobServiceClient, ContainerClient

from app.models.auth import AuthMethod
from providers.azure.auth import AzureAuth
from providers.azure.provider import AzureProvider
from providers.azure.sources import AzureSource


class TestAzureProvider:
    """Test suite for AzureProvider class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.valid_config = {
            "name": "azure-test",
            "provider_type": "azure",
            "storage_account": "teststorage",
            "container_name": "billing-exports",
            "export_path": "exports/daily",
            "auth_config": {"method": AuthMethod.API_KEY, "key": "test-storage-key"},
        }

        self.minimal_config = {
            "name": "azure-minimal",
            "provider_type": "azure",
            "storage_account": "teststorage",
            "container_name": "billing-exports",
            "auth_config": {"method": AuthMethod.API_KEY, "key": "test-storage-key"},
        }

    def test_provider_registration(self):
        """Test that provider is properly registered."""
        from providers.registry import ProviderRegistry

        provider_class = ProviderRegistry.get_provider_class("azure")
        assert provider_class is not None
        assert provider_class == AzureProvider

    def test_init_success(self):
        """Test successful provider initialization."""
        provider = AzureProvider(self.valid_config)

        assert provider.provider_type == "azure"
        assert provider.storage_account == "teststorage"
        assert provider.container_name == "billing-exports"
        assert provider.export_path == "exports/daily"
        assert isinstance(provider.auth_handler, AzureAuth)
        assert provider.source_class == AzureSource

    def test_init_minimal_config(self):
        """Test provider initialization with minimal config."""
        provider = AzureProvider(self.minimal_config)

        assert provider.storage_account == "teststorage"
        assert provider.container_name == "billing-exports"
        assert provider.export_path == ""  # Default empty string

    def test_init_missing_storage_account(self):
        """Test initialization failure with missing storage account."""
        config = dict(self.valid_config)
        del config["storage_account"]

        with pytest.raises(ValueError, match="storage_account is required"):
            AzureProvider(config)

    def test_init_missing_container_name(self):
        """Test initialization failure with missing container name."""
        config = dict(self.valid_config)
        del config["container_name"]

        with pytest.raises(ValueError, match="container_name is required"):
            AzureProvider(config)

    def test_init_additional_config(self):
        """Test initialization with additional_config structure."""
        config = {
            "name": "azure-test",
            "provider_type": "azure",
            "auth_config": {"method": AuthMethod.API_KEY, "key": "test-key"},
            "additional_config": {
                "storage_account": "additionalstorage",
                "container_name": "additional-container",
                "export_path": "additional/path",
            },
        }
        provider = AzureProvider(config)

        assert provider.storage_account == "additionalstorage"
        assert provider.container_name == "additional-container"
        assert provider.export_path == "additional/path"

    def test_get_config_value_priority(self):
        """Test config value retrieval priority (root over additional_config)."""
        config = {
            "name": "test",
            "storage_account": "root-storage",
            "additional_config": {
                "storage_account": "additional-storage",
                "container_name": "additional-container",
            },
            "auth_config": {"method": AuthMethod.API_KEY, "key": "test"},
        }
        provider = AzureProvider(config)

        assert provider.storage_account == "root-storage"  # Root takes priority

    @patch("providers.azure.provider.AzureAuth")
    def test_get_blob_service_client_lazy_loading(self, mock_auth_class):
        """Test blob service client lazy loading."""
        mock_auth = Mock()
        mock_client = Mock(spec=BlobServiceClient)
        mock_auth.create_blob_service_client.return_value = mock_client
        mock_auth_class.return_value = mock_auth

        provider = AzureProvider(self.valid_config)

        # First call should create client
        client1 = provider.get_blob_service_client()
        assert client1 == mock_client
        mock_auth.create_blob_service_client.assert_called_once()

        # Second call should return cached client
        client2 = provider.get_blob_service_client()
        assert client2 == mock_client
        assert mock_auth.create_blob_service_client.call_count == 1

    @patch("providers.azure.provider.AzureAuth")
    def test_get_sources_success(self, mock_auth_class):
        """Test successful source retrieval."""
        mock_auth_class.return_value = Mock()

        with patch.object(AzureSource, "get_sources") as mock_get_sources:
            mock_sources = [{"name": "test_source", "config": {}}]
            mock_get_sources.return_value = mock_sources

            provider = AzureProvider(self.valid_config)
            start_date = datetime(2024, 1, 1)
            end_date = datetime(2024, 1, 31)

            sources = provider.get_sources(start_date, end_date)

            assert sources == mock_sources
            mock_get_sources.assert_called_once_with(start_date, end_date)

    @patch("providers.azure.provider.logger")
    @patch("providers.azure.provider.AzureAuth")
    def test_get_sources_no_source_class(self, mock_auth_class, mock_logger):
        """Test source retrieval with no source class."""
        mock_auth_class.return_value = Mock()
        provider = AzureProvider(self.valid_config)
        provider.source_class = None

        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)

        sources = provider.get_sources(start_date, end_date)

        assert sources == []
        mock_logger.warning.assert_called_once_with(
            "No source class registered for Azure provider"
        )

    @patch("providers.azure.provider.AzureAuth")
    def test_test_connection_success(self, mock_auth_class):
        """Test successful connection test."""
        # Mock auth handler
        mock_auth = Mock()
        mock_auth.method = AuthMethod.API_KEY
        mock_auth_class.return_value = mock_auth

        # Mock blob service client and container
        mock_blob_client = Mock(spec=BlobServiceClient)
        mock_container_client = Mock(spec=ContainerClient)
        mock_auth.create_blob_service_client.return_value = mock_blob_client
        mock_blob_client.get_container_client.return_value = mock_container_client

        # Mock container exists and blob listing
        mock_container_client.exists.return_value = True
        mock_blobs = [Mock() for _ in range(5)]  # 5 mock blobs
        mock_container_client.list_blobs.return_value = iter(mock_blobs)

        provider = AzureProvider(self.valid_config)
        result = provider.test_connection()

        assert result["success"] is True
        assert "Successfully connected" in result["message"]
        assert result["details"]["storage_account"] == "teststorage"
        assert result["details"]["container"] == "billing-exports"
        assert result["details"]["files_found"] == 5
        assert result["details"]["auth_method"] == str(AuthMethod.API_KEY)

    @patch("providers.azure.provider.AzureAuth")
    def test_test_connection_container_not_found(self, mock_auth_class):
        """Test connection test with container not found."""
        # Mock auth handler
        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        # Mock blob service client and container
        mock_blob_client = Mock(spec=BlobServiceClient)
        mock_container_client = Mock(spec=ContainerClient)
        mock_auth.create_blob_service_client.return_value = mock_blob_client
        mock_blob_client.get_container_client.return_value = mock_container_client

        # Mock container does not exist
        mock_container_client.exists.return_value = False

        provider = AzureProvider(self.valid_config)
        result = provider.test_connection()

        assert result["success"] is False
        assert "Container 'billing-exports' not found" in result["message"]
        assert result["details"]["storage_account"] == "teststorage"

    @patch("providers.azure.provider.AzureAuth")
    def test_test_connection_auth_validation_error(self, mock_auth_class):
        """Test connection test with authentication validation error."""
        mock_auth = Mock()
        mock_auth.validate.side_effect = ValueError("Invalid auth config")
        mock_auth_class.return_value = mock_auth

        provider = AzureProvider(self.valid_config)
        result = provider.test_connection()

        assert result["success"] is False
        assert "Invalid configuration: Invalid auth config" in result["message"]

    @patch("providers.azure.provider.AzureAuth")
    def test_test_connection_azure_error(self, mock_auth_class):
        """Test connection test with Azure service error."""
        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        # Mock Azure error
        azure_error = AzureError("Service unavailable")
        azure_error.error_code = "ServiceUnavailable"
        mock_auth.create_blob_service_client.side_effect = azure_error

        provider = AzureProvider(self.valid_config)
        result = provider.test_connection()

        assert result["success"] is False
        assert "Azure Error: ServiceUnavailable" in result["message"]
        assert result["details"]["error_code"] == "ServiceUnavailable"

    @patch("providers.azure.provider.AzureAuth")
    def test_test_connection_generic_error(self, mock_auth_class):
        """Test connection test with generic error."""
        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth
        mock_auth.create_blob_service_client.side_effect = Exception("Generic error")

        provider = AzureProvider(self.valid_config)
        result = provider.test_connection()

        assert result["success"] is False
        assert "Connection test failed: Generic error" in result["message"]
        assert result["details"]["error_type"] == "Exception"

    @patch("providers.azure.provider.AzureAuth")
    def test_test_connection_blob_count_limit(self, mock_auth_class):
        """Test connection test with blob count limiting."""
        # Mock auth handler
        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        # Mock blob service client and container
        mock_blob_client = Mock(spec=BlobServiceClient)
        mock_container_client = Mock(spec=ContainerClient)
        mock_auth.create_blob_service_client.return_value = mock_blob_client
        mock_blob_client.get_container_client.return_value = mock_container_client

        # Mock container exists and many blobs
        mock_container_client.exists.return_value = True
        mock_blobs = [Mock() for _ in range(20)]  # 20 mock blobs
        mock_container_client.list_blobs.return_value = iter(mock_blobs)

        provider = AzureProvider(self.valid_config)
        result = provider.test_connection()

        assert result["success"] is True
        assert result["details"]["files_found"] == 10  # Should be limited to 10

    @patch("providers.azure.provider.AzureAuth")
    def test_test_connection_with_export_path(self, mock_auth_class):
        """Test connection test uses export path in blob listing."""
        # Mock auth handler
        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        # Mock blob service client and container
        mock_blob_client = Mock(spec=BlobServiceClient)
        mock_container_client = Mock(spec=ContainerClient)
        mock_auth.create_blob_service_client.return_value = mock_blob_client
        mock_blob_client.get_container_client.return_value = mock_container_client

        # Mock container exists
        mock_container_client.exists.return_value = True
        mock_container_client.list_blobs.return_value = iter([])

        provider = AzureProvider(self.valid_config)
        provider.test_connection()

        # Verify list_blobs was called with export path
        mock_container_client.list_blobs.assert_called_once_with(
            name_starts_with="exports/daily"
        )

    @patch("providers.azure.provider.AzureAuth")
    def test_get_filesystem_config(self, mock_auth_class):
        """Test filesystem config generation."""
        mock_auth = Mock()
        mock_auth.get_filesystem_config.return_value = {
            "azure_storage_account_key": "test-key",
            "azure_storage_account_name": "teststorage",
        }
        mock_auth_class.return_value = mock_auth

        provider = AzureProvider(self.valid_config)
        config = provider.get_filesystem_config()

        expected = {
            "bucket_url": "az://billing-exports/exports/daily",
            "azure_storage_account_key": "test-key",
            "azure_storage_account_name": "teststorage",
        }
        assert config == expected

    @patch("providers.azure.provider.AzureAuth")
    def test_get_filesystem_config_no_export_path(self, mock_auth_class):
        """Test filesystem config without export path."""
        mock_auth = Mock()
        mock_auth.get_filesystem_config.return_value = {
            "azure_storage_account_key": "test-key"
        }
        mock_auth_class.return_value = mock_auth

        provider = AzureProvider(self.minimal_config)
        config = provider.get_filesystem_config()

        expected = {
            "bucket_url": "az://billing-exports",
            "azure_storage_account_key": "test-key",
        }
        assert config == expected

    def test_config_validation_in_init(self):
        """Test config validation during initialization."""
        # Test empty storage account
        config = dict(self.valid_config)
        config["storage_account"] = ""

        with pytest.raises(ValueError, match="storage_account is required"):
            AzureProvider(config)

        # Test empty container name
        config = dict(self.valid_config)
        config["container_name"] = ""

        with pytest.raises(ValueError, match="container_name is required"):
            AzureProvider(config)

    def test_auth_handler_initialization(self):
        """Test auth handler is properly initialized."""
        provider = AzureProvider(self.valid_config)

        assert isinstance(provider.auth_handler, AzureAuth)
        assert provider.auth_handler.auth_config == self.valid_config["auth_config"]
        assert provider.auth_handler.storage_account == "teststorage"
