"""
Tests for provider service
"""

from unittest.mock import Mock, patch

import pytest

from app.services.provider_service import ProviderService


@pytest.fixture
def provider_service(test_db_session, mock_encryption_service):
    """Create provider service instance with test database."""
    with patch(
        "app.services.provider_service.EncryptionService",
        return_value=mock_encryption_service,
    ):
        return ProviderService(test_db_session)


@pytest.fixture
def sample_provider_create_data():
    """Sample data for creating a provider."""
    return {
        "name": "test-openai-provider",
        "provider_type": "openai",
        "display_name": "Test OpenAI Provider",
        "auth_config": {"method": "bearer_token", "api_key": "sk-test-key-123"},
        "api_endpoint": "https://api.openai.com",
        "additional_config": {"organization_id": "org-123"},
    }


@pytest.mark.asyncio
async def test_create_provider(provider_service, sample_provider_create_data):
    """Test creating a new provider."""
    with (
        patch("providers.registry.ProviderRegistry.get_supported_types") as mock_types,
        patch(
            "providers.registry.ProviderRegistry.get_provider_metadata"
        ) as mock_metadata,
        patch.object(provider_service, "test_provider_connection") as mock_test,
    ):
        mock_types.return_value = ["openai"]
        mock_metadata.return_value = {
            "display_name": "OpenAI",
            "supported_auth_methods": [Mock(value="bearer_token")],
            "required_config": [],
            "default_endpoint": "https://api.openai.com",
        }
        mock_test.return_value = Mock(success=True)

        provider = await provider_service.create_provider(**sample_provider_create_data)

        assert provider.id is not None
        assert provider.name == "test-openai-provider"
        assert provider.provider_type == "openai"
        assert provider.display_name == "Test OpenAI Provider"
        assert provider.api_endpoint == "https://api.openai.com"
        assert provider.is_active is True
        assert provider.auth_config is not None


@pytest.mark.asyncio
async def test_create_provider_duplicate_name(
    provider_service, sample_provider_create_data
):
    """Test creating provider with duplicate name."""
    with (
        patch("providers.registry.ProviderRegistry.get_supported_types") as mock_types,
        patch(
            "providers.registry.ProviderRegistry.get_provider_metadata"
        ) as mock_metadata,
        patch.object(provider_service, "test_provider_connection") as mock_test,
    ):
        mock_types.return_value = ["openai"]
        mock_metadata.return_value = {
            "display_name": "OpenAI",
            "supported_auth_methods": [Mock(value="bearer_token")],
            "required_config": [],
            "default_endpoint": "https://api.openai.com",
        }
        mock_test.return_value = Mock(success=True)

        # Create first provider
        await provider_service.create_provider(**sample_provider_create_data)

        # Try to create another with same name
        with pytest.raises(ValueError, match="already exists"):
            await provider_service.create_provider(**sample_provider_create_data)


@pytest.mark.asyncio
async def test_create_provider_invalid_type(
    provider_service, sample_provider_create_data
):
    """Test creating provider with invalid type."""
    with patch("providers.registry.ProviderRegistry.get_supported_types") as mock_types:
        mock_types.return_value = ["openai"]  # Don't include invalid-type

        sample_provider_create_data["provider_type"] = "invalid-type"

        with pytest.raises(ValueError, match="Invalid provider type"):
            await provider_service.create_provider(**sample_provider_create_data)


@pytest.mark.asyncio
async def test_get_provider(provider_service, sample_provider_create_data):
    """Test getting a provider by ID."""
    with (
        patch("providers.registry.ProviderRegistry.get_supported_types") as mock_types,
        patch(
            "providers.registry.ProviderRegistry.get_provider_metadata"
        ) as mock_metadata,
        patch.object(provider_service, "test_provider_connection") as mock_test,
    ):
        mock_types.return_value = ["openai"]
        mock_metadata.return_value = {
            "display_name": "OpenAI",
            "supported_auth_methods": [Mock(value="bearer_token")],
            "required_config": [],
            "default_endpoint": "https://api.openai.com",
        }
        mock_test.return_value = Mock(success=True)

        created_provider = await provider_service.create_provider(
            **sample_provider_create_data
        )

        from uuid import UUID

        provider = provider_service.get_provider(UUID(created_provider.id))

        assert provider is not None
        assert provider.id == created_provider.id
        assert provider.name == created_provider.name


def test_get_provider_not_found(provider_service):
    """Test getting non-existent provider."""
    from uuid import uuid4

    provider = provider_service.get_provider(uuid4())
    assert provider is None


@pytest.mark.asyncio
async def test_get_all_providers(provider_service, sample_provider_create_data):
    """Test getting all providers."""
    with (
        patch("providers.registry.ProviderRegistry.get_supported_types") as mock_types,
        patch(
            "providers.registry.ProviderRegistry.get_provider_metadata"
        ) as mock_metadata,
        patch.object(provider_service, "test_provider_connection") as mock_test,
    ):
        mock_types.return_value = ["openai", "azure"]
        mock_metadata.return_value = {
            "display_name": "Test Provider",
            "supported_auth_methods": [Mock(value="bearer_token")],
            "required_config": [],
            "default_endpoint": "https://api.test.com",
        }
        mock_test.return_value = Mock(success=True)

        # Should have one default provider from conftest
        providers = provider_service.get_all_providers()
        initial_count = len(providers)

        # Create additional providers
        await provider_service.create_provider(**sample_provider_create_data)

        sample_provider_create_data["name"] = "test-azure-provider"
        sample_provider_create_data["provider_type"] = "azure"
        await provider_service.create_provider(**sample_provider_create_data)

        providers = provider_service.get_all_providers()
        assert len(providers) == initial_count + 2


@pytest.mark.asyncio
async def test_get_all_providers_active_only(
    provider_service, sample_provider_create_data
):
    """Test getting only active providers."""
    with (
        patch("providers.registry.ProviderRegistry.get_supported_types") as mock_types,
        patch(
            "providers.registry.ProviderRegistry.get_provider_metadata"
        ) as mock_metadata,
        patch.object(provider_service, "test_provider_connection") as mock_test,
    ):
        mock_types.return_value = ["openai"]
        mock_metadata.return_value = {
            "display_name": "OpenAI",
            "supported_auth_methods": [Mock(value="bearer_token")],
            "required_config": [],
            "default_endpoint": "https://api.openai.com",
        }
        mock_test.return_value = Mock(success=True)

        # Create active provider
        active_provider = await provider_service.create_provider(
            **sample_provider_create_data
        )

        # Create inactive provider
        sample_provider_create_data["name"] = "inactive-provider"
        inactive_provider = await provider_service.create_provider(
            **sample_provider_create_data
        )
        from uuid import UUID

        await provider_service.update_provider(
            UUID(inactive_provider.id), is_active=False
        )

        # Get only active providers
        active_providers = provider_service.get_all_providers(include_inactive=False)
        active_ids = [p.id for p in active_providers]

        assert active_provider.id in active_ids
        assert inactive_provider.id not in active_ids


@pytest.mark.asyncio
async def test_update_provider(provider_service, sample_provider_create_data):
    """Test updating a provider."""
    with (
        patch("providers.registry.ProviderRegistry.get_supported_types") as mock_types,
        patch(
            "providers.registry.ProviderRegistry.get_provider_metadata"
        ) as mock_metadata,
        patch.object(provider_service, "test_provider_connection") as mock_test,
    ):
        mock_types.return_value = ["openai"]
        mock_metadata.return_value = {
            "display_name": "OpenAI",
            "supported_auth_methods": [Mock(value="bearer_token")],
            "required_config": [],
            "default_endpoint": "https://api.openai.com",
        }
        mock_test.return_value = Mock(success=True)

        provider = await provider_service.create_provider(**sample_provider_create_data)

        from uuid import UUID

        updated_provider = await provider_service.update_provider(
            UUID(provider.id),
            display_name="Updated Display Name",
            api_endpoint="https://api.updated.com",
            is_active=False,
            additional_config={"organization_id": "org-456", "new_field": "value"},
        )

        assert updated_provider.display_name == "Updated Display Name"
        assert updated_provider.api_endpoint == "https://api.updated.com"
        assert updated_provider.is_active is False
        assert updated_provider.additional_config["organization_id"] == "org-456"
        assert updated_provider.additional_config["new_field"] == "value"


@pytest.mark.asyncio
async def test_update_provider_auth_config(
    provider_service, sample_provider_create_data
):
    """Test updating provider's auth config."""
    with (
        patch("providers.registry.ProviderRegistry.get_supported_types") as mock_types,
        patch(
            "providers.registry.ProviderRegistry.get_provider_metadata"
        ) as mock_metadata,
        patch.object(provider_service, "test_provider_connection") as mock_test,
    ):
        mock_types.return_value = ["openai"]
        mock_metadata.return_value = {
            "display_name": "OpenAI",
            "supported_auth_methods": [Mock(value="bearer_token")],
            "required_config": [],
            "default_endpoint": "https://api.openai.com",
        }
        mock_test.return_value = Mock(success=True)

        provider = await provider_service.create_provider(**sample_provider_create_data)
        old_auth_config = provider.auth_config

        new_auth_config = {"method": "bearer_token", "api_key": "sk-new-test-key-456"}
        from uuid import UUID

        updated_provider = await provider_service.update_provider(
            UUID(provider.id), auth_config=new_auth_config
        )

        assert updated_provider.auth_config != old_auth_config
        assert updated_provider.is_validated is False  # Should require revalidation


@pytest.mark.asyncio
async def test_update_provider_not_found(provider_service):
    """Test updating non-existent provider."""
    from uuid import uuid4

    updated = await provider_service.update_provider(uuid4(), display_name="Test")
    assert updated is None


@pytest.mark.asyncio
async def test_delete_provider(provider_service, sample_provider_create_data):
    """Test deleting a provider."""
    with (
        patch("providers.registry.ProviderRegistry.get_supported_types") as mock_types,
        patch(
            "providers.registry.ProviderRegistry.get_provider_metadata"
        ) as mock_metadata,
        patch.object(provider_service, "test_provider_connection") as mock_test,
    ):
        mock_types.return_value = ["openai"]
        mock_metadata.return_value = {
            "display_name": "OpenAI",
            "supported_auth_methods": [Mock(value="bearer_token")],
            "required_config": [],
            "default_endpoint": "https://api.openai.com",
        }
        mock_test.return_value = Mock(success=True)

        provider = await provider_service.create_provider(**sample_provider_create_data)

        from uuid import UUID

        result = await provider_service.delete_provider(UUID(provider.id))
        assert result is True

        # Provider should still exist but be inactive (soft delete)
        deleted_provider = provider_service.get_provider(UUID(provider.id))
        assert deleted_provider is not None
        assert deleted_provider.is_active is False


@pytest.mark.asyncio
async def test_delete_provider_not_found(provider_service):
    """Test deleting non-existent provider."""
    from uuid import uuid4

    result = await provider_service.delete_provider(uuid4())
    assert result is False


@pytest.mark.asyncio
async def test_test_connection_openai_success(
    provider_service, sample_provider_create_data
):
    """Test successful OpenAI provider connection test."""
    with (
        patch("providers.registry.ProviderRegistry.get_supported_types") as mock_types,
        patch(
            "providers.registry.ProviderRegistry.get_provider_metadata"
        ) as mock_metadata,
        patch("providers.registry.ProviderRegistry.get_provider_class") as mock_class,
        patch.object(
            provider_service,
            "test_provider_connection",
            wraps=provider_service.test_provider_connection,
        ),
    ):
        mock_types.return_value = ["openai"]
        mock_metadata.return_value = {
            "display_name": "OpenAI",
            "supported_auth_methods": [Mock(value="bearer_token")],
            "required_config": [],
            "default_endpoint": "https://api.openai.com",
        }

        # Mock provider class and its test_connection method
        mock_provider_instance = Mock()
        mock_provider_instance.test_connection.return_value = {
            "success": True,
            "message": "Connection successful",
        }
        mock_provider_class_obj = Mock(return_value=mock_provider_instance)
        mock_class.return_value = mock_provider_class_obj

        provider = await provider_service.create_provider(**sample_provider_create_data)

        from uuid import UUID

        result = await provider_service.test_provider_connection(UUID(provider.id))

        assert result.success is True
        assert "Connection successful" in result.message


@pytest.mark.asyncio
async def test_test_connection_failure(provider_service, sample_provider_create_data):
    """Test failed provider connection test."""
    with (
        patch("providers.registry.ProviderRegistry.get_supported_types") as mock_types,
        patch(
            "providers.registry.ProviderRegistry.get_provider_metadata"
        ) as mock_metadata,
        patch("providers.registry.ProviderRegistry.get_provider_class") as mock_class,
        patch.object(
            provider_service,
            "test_provider_connection",
            wraps=provider_service.test_provider_connection,
        ),
    ):
        mock_types.return_value = ["openai"]
        mock_metadata.return_value = {
            "display_name": "OpenAI",
            "supported_auth_methods": [Mock(value="bearer_token")],
            "required_config": [],
            "default_endpoint": "https://api.openai.com",
        }

        # Mock provider class that raises exception
        mock_provider_instance = Mock()
        mock_provider_instance.test_connection.side_effect = Exception(
            "API key invalid"
        )
        mock_provider_class_obj = Mock(return_value=mock_provider_instance)
        mock_class.return_value = mock_provider_class_obj

        provider = await provider_service.create_provider(**sample_provider_create_data)

        from uuid import UUID

        result = await provider_service.test_provider_connection(UUID(provider.id))

        assert result.success is False
        assert "API key invalid" in result.message


@pytest.mark.asyncio
async def test_test_connection_provider_not_found(provider_service):
    """Test connection test for non-existent provider."""
    from uuid import uuid4

    result = await provider_service.test_provider_connection(uuid4())
    assert result.success is False
    assert "Provider not found" in result.message


def test_get_provider_types_info(provider_service):
    """Test getting available provider types info."""
    with (
        patch("providers.registry.ProviderRegistry.get_supported_types") as mock_types,
        patch(
            "providers.registry.ProviderRegistry.get_provider_metadata"
        ) as mock_metadata,
    ):
        mock_types.return_value = ["openai", "aws", "azure", "gcp"]
        mock_metadata.return_value = {
            "display_name": "Test Provider",
            "description": "Test provider description",
            "supported_auth_methods": [Mock(value="bearer_token")],
            "required_config": [],
            "optional_config": [],
        }

        result = provider_service.get_provider_types_info()

        assert isinstance(result, dict)
        assert "providers" in result
        assert "total_providers" in result
        assert len(result["providers"]) == 4

        # Check that common providers are included
        provider_types = [p["provider_type"] for p in result["providers"]]
        assert "openai" in provider_types
        assert "aws" in provider_types
        assert "azure" in provider_types
        assert "gcp" in provider_types

        # Check structure
        for provider_info in result["providers"]:
            assert "provider_type" in provider_info
            assert "display_name" in provider_info
            assert "description" in provider_info


def test_get_auth_fields(provider_service):
    """Test getting auth fields for provider types."""
    with patch(
        "providers.registry.ProviderRegistry.get_provider_metadata"
    ) as mock_metadata:
        mock_metadata.return_value = {
            "supported_auth_methods": [Mock(value="bearer_token")],
            "default_auth_method": Mock(value="bearer_token"),
            "auth_fields": {
                Mock(value="bearer_token"): {
                    "api_key": {
                        "type": "password",
                        "required": True,
                        "label": "API Key",
                    }
                }
            },
        }

        # Test OpenAI auth fields
        result = provider_service.get_auth_fields("openai")

        assert isinstance(result, dict)
        assert "auth_fields" in result
        assert "supported_auth_methods" in result
        assert "bearer_token" in result["supported_auth_methods"]
        assert "bearer_token" in result["auth_fields"]


def test_get_auth_fields_invalid_type(provider_service):
    """Test getting auth fields for invalid provider type."""
    with patch(
        "providers.registry.ProviderRegistry.get_provider_metadata"
    ) as mock_metadata:
        mock_metadata.return_value = None

        with pytest.raises(ValueError, match="Provider type 'invalid-type' not found"):
            provider_service.get_auth_fields("invalid-type")


def test_get_provider_config(provider_service, sample_provider_create_data):
    """Test getting provider configuration."""
    with (
        patch("providers.registry.ProviderRegistry.get_supported_types") as mock_types,
        patch(
            "providers.registry.ProviderRegistry.get_provider_metadata"
        ) as mock_metadata,
        patch.object(provider_service, "test_provider_connection") as mock_test,
    ):
        mock_types.return_value = ["openai"]
        mock_metadata.return_value = {
            "display_name": "OpenAI",
            "supported_auth_methods": [Mock(value="bearer_token")],
            "required_config": [],
            "default_endpoint": "https://api.openai.com",
        }
        mock_test.return_value = Mock(success=True)

        # Create provider first
        import asyncio

        provider = asyncio.run(
            provider_service.create_provider(**sample_provider_create_data)
        )

        from uuid import UUID

        config = provider_service.get_provider_config(UUID(provider.id))

        assert config is not None
        assert config["provider_type"] == "openai"
        assert config["name"] == "test-openai-provider"
        assert "auth_config" in config


@pytest.mark.asyncio
async def test_get_provider_by_name(provider_service, sample_provider_create_data):
    """Test getting provider by name via repository."""
    with (
        patch("providers.registry.ProviderRegistry.get_supported_types") as mock_types,
        patch(
            "providers.registry.ProviderRegistry.get_provider_metadata"
        ) as mock_metadata,
        patch.object(provider_service, "test_provider_connection") as mock_test,
    ):
        mock_types.return_value = ["openai"]
        mock_metadata.return_value = {
            "display_name": "OpenAI",
            "supported_auth_methods": [Mock(value="bearer_token")],
            "required_config": [],
            "default_endpoint": "https://api.openai.com",
        }
        mock_test.return_value = Mock(success=True)

        created_provider = await provider_service.create_provider(
            **sample_provider_create_data
        )

        provider = provider_service.provider_repo.get_by_name("test-openai-provider")

        assert provider is not None
        assert provider.id == created_provider.id
        assert provider.name == "test-openai-provider"


@pytest.mark.asyncio
async def test_get_providers_by_type(provider_service, sample_provider_create_data):
    """Test getting providers by type."""
    with (
        patch("providers.registry.ProviderRegistry.get_supported_types") as mock_types,
        patch(
            "providers.registry.ProviderRegistry.get_provider_metadata"
        ) as mock_metadata,
        patch.object(provider_service, "test_provider_connection") as mock_test,
    ):
        mock_types.return_value = ["openai", "azure"]
        mock_metadata.return_value = {
            "display_name": "Test Provider",
            "supported_auth_methods": [Mock(value="bearer_token")],
            "required_config": [],
            "default_endpoint": "https://api.test.com",
        }
        mock_test.return_value = Mock(success=True)

        # Create multiple providers of different types
        await provider_service.create_provider(**sample_provider_create_data)

        azure_data = sample_provider_create_data.copy()
        azure_data["name"] = "test-azure"
        azure_data["provider_type"] = "azure"
        await provider_service.create_provider(**azure_data)

        # Get only OpenAI providers
        openai_providers = provider_service.get_all_providers(provider_type="openai")

        assert all(p.provider_type == "openai" for p in openai_providers)
        assert len(openai_providers) >= 1  # At least our created one


def test_encrypt_decrypt_auth_config(provider_service):
    """Test auth config encryption and decryption."""
    original_config = {"method": "bearer_token", "api_key": "sk-test-key-123456"}

    # Encrypt
    with patch("app.models.auth.get_sensitive_fields") as mock_sensitive:
        mock_sensitive.return_value = ["api_key"]
        encrypted = provider_service._encrypt_auth_config(original_config)
        assert encrypted["api_key"] != original_config["api_key"]

        # Decrypt
        decrypted = provider_service._decrypt_auth_config(encrypted)
        assert decrypted["api_key"] == original_config["api_key"]
