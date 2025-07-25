"""
Unit tests for Provider Registry
"""

from typing import Any
from unittest.mock import Mock, patch

import pytest

from app.models.auth import AuthMethod
from focus.mappers.base import BaseFocusMapper
from pipeline.sources.base import BaseSource
from providers.base import BaseProvider
from providers.registry import ProviderRegistry, get_mapper, get_provider


# Mock classes for testing
class MockProvider(BaseProvider):
    """Mock provider for testing."""

    def get_sources(self, start_date, end_date):
        return [
            {"source": "mock_source", "start_date": start_date, "end_date": end_date}
        ]

    def test_connection(self):
        return {"success": True, "message": "Mock connection successful"}


class MockMapper(BaseFocusMapper):
    """Mock mapper for testing."""

    def __init__(self, config: dict[str, Any]):
        # Add required provider_id for BaseFocusMapper
        if "provider_id" not in config and "id" not in config:
            config["provider_id"] = "test-provider-id"
        super().__init__(config)

    def map_data(self, data):
        return {"mapped": True, "data": data}


class MockSource(BaseSource):
    """Mock source for testing."""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)

    def get_data(self):
        return {"mock": "data"}


class TestProviderRegistry:
    """Test suite for ProviderRegistry class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Clear registry before each test
        ProviderRegistry.clear()

        self.test_provider_type = "test_provider"
        self.test_display_name = "Test Provider"
        self.test_description = "Test provider for unit testing"
        self.test_config = {
            "provider_type": self.test_provider_type,
            "auth_config": {"api_key": "test-key"},
            "api_endpoint": "https://api.test.com",
        }

    def teardown_method(self):
        """Clean up after each test."""
        ProviderRegistry.clear()

    def test_register_basic_provider(self):
        """Test basic provider registration."""

        # Register a provider using decorator
        @ProviderRegistry.register(
            provider_type=self.test_provider_type,
            display_name=self.test_display_name,
            description=self.test_description,
        )
        class TestProvider(BaseProvider):
            def get_sources(self, start_date, end_date):
                return []

            def test_connection(self):
                return {"success": True}

        # Verify registration
        provider_class = ProviderRegistry.get_provider_class(self.test_provider_type)
        assert provider_class is not None
        assert provider_class == TestProvider

        # Verify metadata
        metadata = ProviderRegistry.get_provider_metadata(self.test_provider_type)
        assert metadata is not None
        assert metadata["display_name"] == self.test_display_name
        assert metadata["description"] == self.test_description
        assert metadata["provider_type"] == self.test_provider_type

    def test_register_provider_with_full_metadata(self):
        """Test provider registration with complete metadata."""
        required_config = ["api_key", "region"]
        optional_config = ["timeout", "retry_count"]
        supported_features = ["billing", "cost_analysis"]
        auth_fields = {
            "api_key": {
                "api_key": {"type": "password", "required": True, "label": "API Key"}
            }
        }

        @ProviderRegistry.register(
            provider_type=self.test_provider_type,
            display_name=self.test_display_name,
            description=self.test_description,
            required_config=required_config,
            optional_config=optional_config,
            supported_features=supported_features,
            version="2.0.0",
            supported_auth_methods=[AuthMethod.API_KEY],
            default_auth_method=AuthMethod.API_KEY,
            auth_fields=auth_fields,
            mapper_class=MockMapper,
            source_class=MockSource,
            default_source_type="filesystem",
        )
        class AdvancedTestProvider(BaseProvider):
            def get_sources(self, start_date, end_date):
                return []

            def test_connection(self):
                return {"success": True}

        metadata = ProviderRegistry.get_provider_metadata(self.test_provider_type)
        assert metadata["required_config"] == required_config
        assert metadata["optional_config"] == optional_config
        assert metadata["supported_features"] == supported_features
        assert metadata["version"] == "2.0.0"
        assert metadata["supported_auth_methods"] == [AuthMethod.API_KEY]
        assert metadata["default_auth_method"] == AuthMethod.API_KEY
        assert metadata["auth_fields"] == auth_fields
        assert metadata["default_source_type"] == "filesystem"

        # Verify mapper and source registration
        mapper_class = ProviderRegistry.get_mapper_class(self.test_provider_type)
        source_class = ProviderRegistry.get_source_class(self.test_provider_type)
        assert mapper_class == MockMapper
        assert source_class == MockSource

    def test_register_invalid_provider_class(self):
        """Test registration with invalid provider class."""

        class InvalidProvider:
            pass

        with pytest.raises(TypeError, match="must inherit from BaseProvider"):

            @ProviderRegistry.register(
                provider_type=self.test_provider_type,
                display_name=self.test_display_name,
            )
            class TestInvalidProvider(InvalidProvider):
                pass

    def test_register_invalid_mapper_class(self):
        """Test registration with invalid mapper class."""

        class InvalidMapper:
            pass

        with pytest.raises(TypeError, match="must inherit from BaseFocusMapper"):

            @ProviderRegistry.register(
                provider_type=self.test_provider_type,
                display_name=self.test_display_name,
                mapper_class=InvalidMapper,
            )
            class TestProvider(BaseProvider):
                def get_sources(self, start_date, end_date):
                    return []

                def test_connection(self):
                    return {"success": True}

    def test_register_invalid_source_class(self):
        """Test registration with invalid source class."""

        class InvalidSource:
            pass

        with pytest.raises(TypeError, match="must inherit from BaseSource"):

            @ProviderRegistry.register(
                provider_type=self.test_provider_type,
                display_name=self.test_display_name,
                source_class=InvalidSource,
            )
            class TestProvider(BaseProvider):
                def get_sources(self, start_date, end_date):
                    return []

                def test_connection(self):
                    return {"success": True}

    def test_get_provider_class_not_found(self):
        """Test getting non-existent provider class."""
        provider_class = ProviderRegistry.get_provider_class("nonexistent")
        assert provider_class is None

    def test_get_mapper_class_not_found(self):
        """Test getting mapper for provider without mapper."""

        @ProviderRegistry.register(
            provider_type=self.test_provider_type, display_name=self.test_display_name
        )
        class TestProvider(BaseProvider):
            def get_sources(self, start_date, end_date):
                return []

            def test_connection(self):
                return {"success": True}

        mapper_class = ProviderRegistry.get_mapper_class(self.test_provider_type)
        assert mapper_class is None

    def test_get_source_class_not_found(self):
        """Test getting source for provider without source."""

        @ProviderRegistry.register(
            provider_type=self.test_provider_type, display_name=self.test_display_name
        )
        class TestProvider(BaseProvider):
            def get_sources(self, start_date, end_date):
                return []

            def test_connection(self):
                return {"success": True}

        source_class = ProviderRegistry.get_source_class(self.test_provider_type)
        assert source_class is None

    def test_get_default_source_type(self):
        """Test getting default source type."""

        @ProviderRegistry.register(
            provider_type=self.test_provider_type,
            display_name=self.test_display_name,
            default_source_type="sql_database",
        )
        class TestProvider(BaseProvider):
            def get_sources(self, start_date, end_date):
                return []

            def test_connection(self):
                return {"success": True}

        source_type = ProviderRegistry.get_default_source_type(self.test_provider_type)
        assert source_type == "sql_database"

        # Test default fallback
        source_type = ProviderRegistry.get_default_source_type("nonexistent")
        assert source_type == "rest_api"

    def test_create_provider_success(self):
        """Test successful provider creation."""

        @ProviderRegistry.register(
            provider_type=self.test_provider_type,
            display_name=self.test_display_name,
            source_class=MockSource,
        )
        class TestProvider(BaseProvider):
            def get_sources(self, start_date, end_date):
                return []

            def test_connection(self):
                return {"success": True}

        provider = ProviderRegistry.create_provider(
            self.test_provider_type, self.test_config
        )

        assert provider is not None
        assert isinstance(provider, TestProvider)
        assert provider.provider_type == self.test_provider_type
        assert provider.source_class == MockSource

    def test_create_provider_not_found(self):
        """Test creating non-existent provider."""
        provider = ProviderRegistry.create_provider("nonexistent", self.test_config)
        assert provider is None

    def test_get_mapper_success(self):
        """Test successful mapper creation."""

        @ProviderRegistry.register(
            provider_type=self.test_provider_type,
            display_name=self.test_display_name,
            mapper_class=MockMapper,
        )
        class TestProvider(BaseProvider):
            def get_sources(self, start_date, end_date):
                return []

            def test_connection(self):
                return {"success": True}

        mapper = ProviderRegistry.get_mapper(self.test_provider_type, self.test_config)

        assert mapper is not None
        assert isinstance(mapper, MockMapper)

    def test_get_mapper_not_found(self):
        """Test getting mapper for provider without mapper."""

        @ProviderRegistry.register(
            provider_type=self.test_provider_type, display_name=self.test_display_name
        )
        class TestProvider(BaseProvider):
            def get_sources(self, start_date, end_date):
                return []

            def test_connection(self):
                return {"success": True}

        mapper = ProviderRegistry.get_mapper(self.test_provider_type, self.test_config)
        assert mapper is None

    def test_get_supported_types(self):
        """Test getting supported provider types."""

        @ProviderRegistry.register(
            provider_type=self.test_provider_type, display_name=self.test_display_name
        )
        class TestProvider(BaseProvider):
            def get_sources(self, start_date, end_date):
                return []

            def test_connection(self):
                return {"success": True}

        with patch.object(
            ProviderRegistry, "_discover_available_providers"
        ) as mock_discover:
            mock_discover.return_value = ["aws", "azure", "gcp"]

            supported_types = ProviderRegistry.get_supported_types()
            assert self.test_provider_type in supported_types
            assert "aws" in supported_types
            assert "azure" in supported_types
            assert "gcp" in supported_types

    def test_validate_config_success(self):
        """Test successful config validation."""

        @ProviderRegistry.register(
            provider_type=self.test_provider_type,
            display_name=self.test_display_name,
            required_config=["api_key"],
            optional_config=["timeout"],
        )
        class TestProvider(BaseProvider):
            def get_sources(self, start_date, end_date):
                return []

            def test_connection(self):
                return {"success": True}

        config = {"api_key": "test-key", "timeout": 30}

        result = ProviderRegistry.validate_config(self.test_provider_type, config)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_config_missing_required(self):
        """Test config validation with missing required fields."""

        @ProviderRegistry.register(
            provider_type=self.test_provider_type,
            display_name=self.test_display_name,
            required_config=["api_key", "region"],
            optional_config=["timeout"],
        )
        class TestProvider(BaseProvider):
            def get_sources(self, start_date, end_date):
                return []

            def test_connection(self):
                return {"success": True}

        config = {
            "timeout": 30  # Missing api_key and region
        }

        result = ProviderRegistry.validate_config(self.test_provider_type, config)
        assert result["valid"] is False
        assert len(result["errors"]) == 2
        assert "Missing required field: api_key" in result["errors"]
        assert "Missing required field: region" in result["errors"]

    def test_validate_config_unknown_fields(self):
        """Test config validation with unknown fields."""

        @ProviderRegistry.register(
            provider_type=self.test_provider_type,
            display_name=self.test_display_name,
            required_config=["api_key"],
            optional_config=["timeout"],
        )
        class TestProvider(BaseProvider):
            def get_sources(self, start_date, end_date):
                return []

            def test_connection(self):
                return {"success": True}

        config = {"api_key": "test-key", "unknown_field": "value"}

        result = ProviderRegistry.validate_config(self.test_provider_type, config)
        assert result["valid"] is True
        assert len(result["warnings"]) == 1
        assert "Unknown field: unknown_field" in result["warnings"]

    def test_validate_config_provider_not_found(self):
        """Test config validation for non-existent provider."""
        result = ProviderRegistry.validate_config("nonexistent", {})
        assert result["valid"] is False
        assert "Unknown provider type: nonexistent" in result["errors"]

    @patch("providers.registry.importlib.import_module")
    def test_load_provider_success(self, mock_import):
        """Test successful provider loading."""
        # Mock the import to succeed
        mock_import.return_value = Mock()

        result = ProviderRegistry._load_provider("test_provider")
        assert result is True
        mock_import.assert_called_once_with("providers.test_provider.provider")

    @patch("providers.registry.importlib.import_module")
    def test_load_provider_failure(self, mock_import):
        """Test provider loading failure."""
        # Mock the import to fail
        mock_import.side_effect = ImportError("Module not found")

        result = ProviderRegistry._load_provider("nonexistent_provider")
        assert result is False
        mock_import.assert_called_once_with("providers.nonexistent_provider.provider")

    @patch("providers.registry.Path")
    def test_discover_available_providers_success(self, mock_path):
        """Test successful provider discovery."""
        # Mock directory structure
        mock_providers_dir = Mock()
        mock_aws_dir = Mock()
        mock_aws_dir.is_dir.return_value = True
        mock_aws_dir.name = "aws"
        mock_provider_file = Mock()
        mock_provider_file.exists.return_value = True
        mock_aws_dir.__truediv__ = Mock(return_value=mock_provider_file)

        mock_azure_dir = Mock()
        mock_azure_dir.is_dir.return_value = True
        mock_azure_dir.name = "azure"
        mock_azure_dir.__truediv__ = Mock(return_value=mock_provider_file)

        mock_init_file = Mock()
        mock_init_file.is_dir.return_value = False
        mock_init_file.name = "__init__.py"

        mock_providers_dir.iterdir.return_value = [
            mock_aws_dir,
            mock_azure_dir,
            mock_init_file,
        ]

        mock_path.return_value.parent = mock_providers_dir

        available = ProviderRegistry._discover_available_providers()
        assert "aws" in available
        assert "azure" in available
        assert len(available) == 2

    @patch("providers.registry.Path")
    def test_discover_available_providers_error(self, mock_path):
        """Test provider discovery with error."""
        mock_path.side_effect = Exception("Path error")

        available = ProviderRegistry._discover_available_providers()
        assert available == []

    def test_clear_registry(self):
        """Test clearing the registry."""

        # Register a provider
        @ProviderRegistry.register(
            provider_type=self.test_provider_type,
            display_name=self.test_display_name,
            mapper_class=MockMapper,
            source_class=MockSource,
        )
        class TestProvider(BaseProvider):
            def get_sources(self, start_date, end_date):
                return []

            def test_connection(self):
                return {"success": True}

        # Verify it exists
        assert ProviderRegistry.get_provider_class(self.test_provider_type) is not None
        assert ProviderRegistry.get_mapper_class(self.test_provider_type) is not None
        assert ProviderRegistry.get_source_class(self.test_provider_type) is not None

        # Clear and verify it's gone
        ProviderRegistry.clear()
        assert ProviderRegistry.get_provider_class(self.test_provider_type) is None
        assert ProviderRegistry.get_mapper_class(self.test_provider_type) is None
        assert ProviderRegistry.get_source_class(self.test_provider_type) is None


class TestConvenienceFunctions:
    """Test suite for convenience functions."""

    def setup_method(self):
        """Set up test fixtures."""
        ProviderRegistry.clear()

        self.test_provider_type = "test_convenience"
        self.test_config = {
            "provider_type": self.test_provider_type,
            "auth_config": {"api_key": "test-key"},
        }

    def teardown_method(self):
        """Clean up after each test."""
        ProviderRegistry.clear()

    def test_get_provider_convenience_function(self):
        """Test get_provider convenience function."""

        @ProviderRegistry.register(
            provider_type=self.test_provider_type,
            display_name="Test Convenience Provider",
        )
        class TestProvider(BaseProvider):
            def get_sources(self, start_date, end_date):
                return []

            def test_connection(self):
                return {"success": True}

        provider = get_provider(self.test_provider_type, self.test_config)
        assert provider is not None
        assert isinstance(provider, TestProvider)

    def test_get_mapper_convenience_function(self):
        """Test get_mapper convenience function."""

        @ProviderRegistry.register(
            provider_type=self.test_provider_type,
            display_name="Test Convenience Provider",
            mapper_class=MockMapper,
        )
        class TestProvider(BaseProvider):
            def get_sources(self, start_date, end_date):
                return []

            def test_connection(self):
                return {"success": True}

        mapper = get_mapper(self.test_provider_type, self.test_config)
        assert mapper is not None
        assert isinstance(mapper, MockMapper)


class TestRegistryIntegration:
    """Integration tests for the registry."""

    def setup_method(self):
        """Set up test fixtures."""
        ProviderRegistry.clear()

    def teardown_method(self):
        """Clean up after each test."""
        ProviderRegistry.clear()

    def test_full_provider_lifecycle(self):
        """Test complete provider registration and usage lifecycle."""
        provider_type = "integration_test"

        # Register provider with all components
        @ProviderRegistry.register(
            provider_type=provider_type,
            display_name="Integration Test Provider",
            description="Provider for integration testing",
            required_config=["api_key"],
            optional_config=["timeout"],
            supported_features=["billing", "analytics"],
            version="1.0.0",
            mapper_class=MockMapper,
            source_class=MockSource,
            default_source_type="rest_api",
            supported_auth_methods=[AuthMethod.API_KEY, AuthMethod.BEARER_TOKEN],
            default_auth_method=AuthMethod.API_KEY,
        )
        class IntegrationTestProvider(BaseProvider):
            def get_sources(self, start_date, end_date):
                return [{"type": "integration_source"}]

            def test_connection(self):
                return {"success": True, "message": "Integration test connection"}

        # Test provider creation
        config = {
            "provider_type": provider_type,
            "api_key": "integration-test-key",  # Required config expects top-level api_key
            "auth_config": {"api_key": "integration-test-key"},
            "timeout": 30,  # Optional config
        }

        provider = ProviderRegistry.create_provider(provider_type, config)
        assert provider is not None
        assert isinstance(provider, IntegrationTestProvider)
        assert provider.source_class == MockSource

        # Test mapper creation
        mapper = ProviderRegistry.get_mapper(provider_type, config)
        assert mapper is not None
        assert isinstance(mapper, MockMapper)

        # Test metadata retrieval
        metadata = ProviderRegistry.get_provider_metadata(provider_type)
        assert metadata["display_name"] == "Integration Test Provider"
        assert metadata["required_config"] == ["api_key"]
        assert metadata["supported_features"] == ["billing", "analytics"]

        # Test config validation
        validation_result = ProviderRegistry.validate_config(provider_type, config)
        assert validation_result["valid"] is True

        # Test provider functionality
        connection_result = provider.test_connection()
        assert connection_result["success"] is True
