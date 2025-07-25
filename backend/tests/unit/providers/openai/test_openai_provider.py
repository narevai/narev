"""
Unit tests for OpenAI Provider Implementation
"""

from datetime import datetime
from unittest.mock import Mock, patch

from dlt.sources.helpers.rest_client import RESTClient
from dlt.sources.helpers.rest_client.paginators import HeaderLinkPaginator

from app.models.auth import AuthMethod
from providers.openai.provider import OpenAIProvider
from providers.openai.sources import OpenAISource


class TestOpenAIProvider:
    """Test suite for OpenAIProvider class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.valid_config = {
            "name": "openai-test",
            "provider_type": "openai",
            "auth_config": {
                "method": AuthMethod.BEARER_TOKEN,
                "token": "sk-admin-1234567890abcdef",
            },
            "additional_config": {"organization_id": "org-1234567890abcdef"},
        }

        self.minimal_config = {
            "name": "openai-minimal",
            "provider_type": "openai",
            "auth_config": {
                "method": AuthMethod.BEARER_TOKEN,
                "token": "sk-test-token",
            },
        }

    def test_provider_registration(self):
        """Test that provider is properly registered."""
        from providers.registry import ProviderRegistry

        provider_class = ProviderRegistry.get_provider_class("openai")
        assert provider_class is not None
        assert provider_class == OpenAIProvider

    @patch("providers.openai.provider.OpenAIAuth")
    def test_init_success(self, mock_auth_class):
        """Test successful provider initialization."""
        mock_auth_class.return_value = Mock()

        provider = OpenAIProvider(self.valid_config)

        assert provider.provider_type == "openai"
        assert provider.api_endpoint == "https://api.openai.com/v1"
        assert provider.organization_id == "org-1234567890abcdef"
        assert isinstance(provider.auth_handler, Mock)  # Mocked
        assert provider.source_class == OpenAISource

    @patch("providers.openai.provider.OpenAIAuth")
    def test_init_minimal_config(self, mock_auth_class):
        """Test provider initialization with minimal config."""
        mock_auth_class.return_value = Mock()

        provider = OpenAIProvider(self.minimal_config)

        assert provider.api_endpoint == "https://api.openai.com/v1"
        assert provider.organization_id is None

    @patch("providers.openai.provider.OpenAIAuth")
    def test_init_custom_endpoint(self, mock_auth_class):
        """Test initialization with custom API endpoint."""
        mock_auth_class.return_value = Mock()
        config = dict(self.valid_config)
        config["api_endpoint"] = "https://custom.openai.com/v1"

        provider = OpenAIProvider(config)

        assert provider.api_endpoint == "https://custom.openai.com/v1"

    @patch("providers.openai.provider.OpenAIAuth")
    def test_init_no_endpoint_sets_default(self, mock_auth_class):
        """Test that default endpoint is set when not provided."""
        mock_auth_class.return_value = Mock()

        provider = OpenAIProvider(self.minimal_config)

        assert provider.api_endpoint == "https://api.openai.com/v1"

    @patch("providers.openai.provider.RESTClient")
    @patch("providers.openai.provider.OpenAIAuth")
    def test_get_rest_client_lazy_loading(
        self, mock_auth_class, mock_rest_client_class
    ):
        """Test REST client lazy loading."""
        mock_auth = Mock()
        mock_auth.get_dlt_auth.return_value = "mock_auth"
        mock_auth.get_headers.return_value = {"Authorization": "Bearer sk-test"}
        mock_auth_class.return_value = mock_auth

        mock_client = Mock(spec=RESTClient)
        mock_rest_client_class.return_value = mock_client

        provider = OpenAIProvider(self.valid_config)

        client1 = provider.get_rest_client()
        assert client1 == mock_client
        mock_rest_client_class.assert_called_once()

        client2 = provider.get_rest_client()
        assert client2 == mock_client
        assert mock_rest_client_class.call_count == 1

    @patch("providers.openai.provider.OpenAIAuth")
    def test_get_auth(self, mock_auth_class):
        """Test auth configuration retrieval."""
        mock_auth = Mock()
        mock_auth.get_dlt_auth.return_value = "test_auth"
        mock_auth_class.return_value = mock_auth

        provider = OpenAIProvider(self.valid_config)
        auth = provider.get_auth()

        assert auth == "test_auth"
        mock_auth.get_dlt_auth.assert_called_once()

    @patch("providers.openai.provider.OpenAIAuth")
    def test_get_paginator(self, mock_auth_class):
        """Test paginator creation."""
        mock_auth_class.return_value = Mock()

        provider = OpenAIProvider(self.valid_config)
        paginator = provider.get_paginator()

        assert isinstance(paginator, HeaderLinkPaginator)

    @patch("providers.openai.provider.OpenAIAuth")
    def test_get_request_headers_with_organization(self, mock_auth_class):
        """Test request headers with organization."""
        mock_auth = Mock()
        mock_auth.get_headers.return_value = {"Authorization": "Bearer sk-test"}
        mock_auth_class.return_value = mock_auth

        provider = OpenAIProvider(self.valid_config)
        headers = provider.get_request_headers()

        expected = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "OpenAI-Organization": "org-1234567890abcdef",
            "Authorization": "Bearer sk-test",
        }
        assert headers == expected

    @patch("providers.openai.provider.OpenAIAuth")
    def test_get_request_headers_no_organization(self, mock_auth_class):
        """Test request headers without organization."""
        mock_auth = Mock()
        mock_auth.get_headers.return_value = {"Authorization": "Bearer sk-test"}
        mock_auth_class.return_value = mock_auth

        provider = OpenAIProvider(self.minimal_config)
        headers = provider.get_request_headers()

        expected = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer sk-test",
        }
        assert headers == expected

    @patch("providers.openai.provider.OpenAIAuth")
    def test_get_sources_success(self, mock_auth_class):
        """Test successful source retrieval."""
        mock_auth_class.return_value = Mock()

        with patch.object(OpenAISource, "get_sources") as mock_get_sources:
            mock_sources = [{"name": "completions_usage", "config": {}}]
            mock_get_sources.return_value = mock_sources

            provider = OpenAIProvider(self.valid_config)
            start_date = datetime(2024, 1, 1)
            end_date = datetime(2024, 1, 31)

            sources = provider.get_sources(start_date, end_date)

            assert sources == mock_sources
            mock_get_sources.assert_called_once_with(start_date, end_date)

    @patch("providers.openai.provider.logger")
    @patch("providers.openai.provider.OpenAIAuth")
    def test_get_sources_no_source_class(self, mock_auth_class, mock_logger):
        """Test source retrieval with no source class."""
        mock_auth_class.return_value = Mock()

        provider = OpenAIProvider(self.valid_config)
        provider.source_class = None

        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)

        sources = provider.get_sources(start_date, end_date)

        assert sources == []
        mock_logger.warning.assert_called_once_with(
            "No source class registered for OpenAI provider"
        )

    @patch("providers.openai.provider.httpx.Client")
    @patch("providers.openai.provider.OpenAIAuth")
    def test_test_connection_success(self, mock_auth_class, mock_client_class):
        """Test successful connection test."""
        mock_auth = Mock()
        mock_auth.get_headers.return_value = {"Authorization": "Bearer sk-test"}
        mock_auth_class.return_value = mock_auth

        mock_response = Mock()
        mock_response.status_code = 200

        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        provider = OpenAIProvider(self.valid_config)
        result = provider.test_connection()

        assert result["success"] is True
        assert "Successfully connected to OpenAI API" in result["message"]
        assert result["details"]["endpoint"] == "https://api.openai.com/v1"
        assert result["details"]["organization"] == "org-1234567890abcdef"

    @patch("providers.openai.provider.httpx.Client")
    @patch("providers.openai.provider.OpenAIAuth")
    def test_test_connection_auth_failed(self, mock_auth_class, mock_client_class):
        """Test connection test with authentication failure."""
        mock_auth = Mock()
        mock_auth.get_headers.return_value = {"Authorization": "Bearer invalid"}
        mock_auth_class.return_value = mock_auth

        mock_response = Mock()
        mock_response.status_code = 401

        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        provider = OpenAIProvider(self.valid_config)
        result = provider.test_connection()

        assert result["success"] is False
        assert "Authentication failed" in result["message"]
        assert result["details"]["status_code"] == 401

    @patch("providers.openai.provider.httpx.Client")
    @patch("providers.openai.provider.OpenAIAuth")
    def test_test_connection_other_error(self, mock_auth_class, mock_client_class):
        """Test connection test with other HTTP error."""
        mock_auth = Mock()
        mock_auth.get_headers.return_value = {"Authorization": "Bearer sk-test"}
        mock_auth_class.return_value = mock_auth

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        provider = OpenAIProvider(self.valid_config)
        result = provider.test_connection()

        assert result["success"] is False
        assert "Connection failed with status 500" in result["message"]
        assert result["details"]["status_code"] == 500

    @patch("providers.openai.provider.OpenAIAuth")
    def test_test_connection_auth_validation_error(self, mock_auth_class):
        """Test connection test with auth validation error."""
        mock_auth = Mock()
        mock_auth.validate.side_effect = ValueError("Invalid token")
        mock_auth_class.return_value = mock_auth

        provider = OpenAIProvider(self.valid_config)
        result = provider.test_connection()

        assert result["success"] is False
        assert (
            "Invalid authentication configuration: Invalid token" in result["message"]
        )

    @patch("providers.openai.provider.httpx.Client")
    @patch("providers.openai.provider.OpenAIAuth")
    def test_test_connection_network_error(self, mock_auth_class, mock_client_class):
        """Test connection test with network error."""
        mock_auth = Mock()
        mock_auth.get_headers.return_value = {"Authorization": "Bearer sk-test"}
        mock_auth_class.return_value = mock_auth

        mock_client = Mock()
        mock_client.get.side_effect = Exception("Network error")
        mock_client_class.return_value.__enter__.return_value = mock_client

        provider = OpenAIProvider(self.valid_config)
        result = provider.test_connection()

        assert result["success"] is False
        assert "Connection test failed: Network error" in result["message"]
        assert result["details"]["error_type"] == "Exception"

    @patch("providers.openai.provider.OpenAIAuth")
    def test_test_connection_endpoint_construction(self, mock_auth_class):
        """Test that test_connection uses correct endpoint."""
        mock_auth = Mock()
        mock_auth.get_headers.return_value = {"Authorization": "Bearer sk-test"}
        mock_auth_class.return_value = mock_auth

        with patch("providers.openai.provider.httpx.Client") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200

            mock_client = Mock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            provider = OpenAIProvider(self.valid_config)
            provider.test_connection()

            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args

            assert (
                "https://api.openai.com/v1/organization/usage/completions?start_time="
                in call_args[0][0]
            )
            assert call_args[1]["headers"]["Authorization"] == "Bearer sk-test"
            assert (
                call_args[1]["headers"]["OpenAI-Organization"] == "org-1234567890abcdef"
            )
            assert call_args[1]["timeout"] == 10.0

    @patch("providers.openai.provider.OpenAIAuth")
    def test_auth_handler_initialization(self, mock_auth_class):
        """Test auth handler is properly initialized."""
        mock_auth_class.return_value = Mock()

        provider = OpenAIProvider(self.valid_config)

        mock_auth_class.assert_called_once_with(self.valid_config["auth_config"])
        assert provider.auth_handler is not None

    @patch("providers.openai.provider.OpenAIAuth")
    def test_organization_id_extraction(self, mock_auth_class):
        """Test organization ID is extracted from additional_config."""
        mock_auth_class.return_value = Mock()

        provider = OpenAIProvider(self.valid_config)

        assert provider.organization_id == "org-1234567890abcdef"

    @patch("providers.openai.provider.OpenAIAuth")
    def test_organization_id_missing(self, mock_auth_class):
        """Test handling when organization ID is missing."""
        mock_auth_class.return_value = Mock()

        provider = OpenAIProvider(self.minimal_config)

        assert provider.organization_id is None

    @patch("providers.openai.provider.RESTClient")
    @patch("providers.openai.provider.OpenAIAuth")
    def test_rest_client_configuration(self, mock_auth_class, mock_rest_client_class):
        """Test REST client is configured correctly."""
        mock_auth = Mock()
        mock_auth.get_dlt_auth.return_value = "mock_auth"
        mock_auth.get_headers.return_value = {"Authorization": "Bearer sk-test"}
        mock_auth_class.return_value = mock_auth

        provider = OpenAIProvider(self.valid_config)
        provider.get_rest_client()

        mock_rest_client_class.assert_called_once()
        call_args = mock_rest_client_class.call_args

        assert call_args[1]["base_url"] == "https://api.openai.com/v1"
        assert "Authorization" in call_args[1]["headers"]
        assert "Accept" in call_args[1]["headers"]
        assert "OpenAI-Organization" in call_args[1]["headers"]
        assert call_args[1]["auth"] == "mock_auth"
        assert isinstance(call_args[1]["paginator"], HeaderLinkPaginator)

    @patch("providers.openai.provider.OpenAIAuth")
    def test_source_class_assignment(self, mock_auth_class):
        """Test that source class is properly assigned."""
        mock_auth_class.return_value = Mock()

        provider = OpenAIProvider(self.valid_config)

        assert provider.source_class == OpenAISource

    @patch("providers.openai.provider.OpenAIAuth")
    def test_config_inheritance(self, mock_auth_class):
        """Test that provider inherits from BaseProvider correctly."""
        mock_auth_class.return_value = Mock()

        provider = OpenAIProvider(self.valid_config)

        assert hasattr(provider, "config")
        assert hasattr(provider, "provider_type")
        assert hasattr(provider, "auth_config")
        assert provider.provider_type == "openai"
        assert provider.auth_config == self.valid_config["auth_config"]
