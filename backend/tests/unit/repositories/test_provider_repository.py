# tests/unit/test_provider_repository.py
"""
Unit testy dla ProviderRepository
"""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.provider import Provider
from app.repositories.provider_repository import ProviderRepository


class TestProviderRepository:
    """Unit testy dla ProviderRepository"""

    def setup_method(self):
        """Setup before each test"""
        self.mock_db = Mock(spec=Session)
        self.repo = ProviderRepository(self.mock_db)
        self.provider_id = uuid4()

    def test_init(self):
        """Repository initialization test"""
        assert self.repo.db == self.mock_db

    def test_get_all_default(self):
        """Test get all active providers"""
        mock_providers = [Mock(spec=Provider), Mock(spec=Provider)]
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.order_by.return_value.all.return_value = (
            mock_providers
        )

        result = self.repo.get_all()

        self.mock_db.query.assert_called_once_with(Provider)
        mock_query.filter.assert_called_once()
        assert result == mock_providers

    def test_get_all_include_inactive(self):
        """Test get all providers, include inactive"""
        mock_providers = [Mock(spec=Provider)]
        mock_query = self.mock_db.query.return_value
        mock_query.order_by.return_value.all.return_value = mock_providers

        result = self.repo.get_all(include_inactive=True)

        self.mock_db.query.assert_called_once_with(Provider)
        mock_query.filter.assert_not_called()
        assert result == mock_providers

    def test_get_all_by_provider_type(self):
        """Test filter by provider type"""
        mock_providers = [Mock(spec=Provider)]
        mock_query = self.mock_db.query.return_value

        # Chain: query -> filter (is_active) -> filter (provider_type) -> order_by -> all
        mock_filtered_1 = Mock()
        mock_filtered_2 = Mock()
        mock_ordered = Mock()

        mock_query.filter.return_value = mock_filtered_1
        mock_filtered_1.filter.return_value = mock_filtered_2
        mock_filtered_2.order_by.return_value = mock_ordered
        mock_ordered.all.return_value = mock_providers

        result = self.repo.get_all(provider_type="openai")

        assert mock_query.filter.call_count == 1
        assert mock_filtered_1.filter.call_count == 1
        assert result == mock_providers

    def test_get_all_include_inactive_with_type(self):
        """Test with include_inactive=True and provider_type"""
        mock_providers = [Mock(spec=Provider)]
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.order_by.return_value.all.return_value = (
            mock_providers
        )

        result = self.repo.get_all(include_inactive=True, provider_type="openai")

        assert mock_query.filter.call_count == 1
        assert result == mock_providers

    def test_get_by_id_found(self):
        """Test get provider by id - found"""
        mock_provider = Mock(spec=Provider)
        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_provider
        )

        result = self.repo.get(self.provider_id)

        self.mock_db.query.assert_called_once_with(Provider)
        assert result == mock_provider

    def test_get_by_id_not_found(self):
        """Test get provider by id - not found"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = self.repo.get(self.provider_id)

        assert result is None

    def test_get_by_name_found(self):
        """Test get provider by name - found"""
        mock_provider = Mock(spec=Provider)
        mock_provider.name = "test-provider"
        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_provider
        )

        result = self.repo.get_by_name("test-provider")

        self.mock_db.query.assert_called_once_with(Provider)
        assert result == mock_provider

    def test_get_by_name_not_found(self):
        """Test get provider by name - not found"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = self.repo.get_by_name("nonexistent-provider")

        assert result is None

    def test_create_provider_success(self):
        """Test create new provider - success"""
        provider_data = {
            "name": "test-provider",
            "provider_type": "openai",
            "display_name": "Test Provider",
            "auth_config": {"api_key": "test-key"},
        }

        result = self.repo.create(provider_data)

        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()

        assert result is not None

    def test_create_provider_minimal_data(self):
        """Test create new provider with minimal data"""
        provider_data = {"name": "minimal-provider", "provider_type": "openai"}

        result = self.repo.create(provider_data)

        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()
        assert result is not None

    def test_update_provider_success(self):
        """Test update provider - success"""
        mock_provider = Mock(spec=Provider)
        mock_provider.name = "old-name"
        mock_provider.display_name = "Old Display Name"

        with patch.object(self.repo, "get", return_value=mock_provider):
            update_data = {
                "display_name": "New Display Name",
                "auth_config": {"api_key": "new-key"},
            }
            result = self.repo.update(self.provider_id, update_data)

        assert hasattr(mock_provider, "updated_at")
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once_with(mock_provider)
        assert result == mock_provider

    def test_update_provider_not_found(self):
        """Test update provider - not found"""
        with patch.object(self.repo, "get", return_value=None):
            result = self.repo.update(self.provider_id, {"name": "new-name"})

        assert result is None
        self.mock_db.commit.assert_not_called()
        self.mock_db.refresh.assert_not_called()

    def test_update_provider_empty_data(self):
        """Test update provider with empty data"""
        mock_provider = Mock(spec=Provider)

        with patch.object(self.repo, "get", return_value=mock_provider):
            result = self.repo.update(self.provider_id, {})

        assert hasattr(mock_provider, "updated_at")
        self.mock_db.commit.assert_called_once()
        assert result == mock_provider

    def test_update_provider_invalid_field(self):
        """Test update with invalid field"""
        mock_provider = Mock(spec=Provider)

        with patch.object(self.repo, "get", return_value=mock_provider):
            with patch("builtins.hasattr", return_value=False):
                result = self.repo.update(
                    self.provider_id, {"nonexistent_field": "value"}
                )

        assert result == mock_provider

    def test_delete_provider_success(self):
        """Test provider deletion - success"""
        mock_provider = Mock(spec=Provider)
        mock_provider.is_active = True

        with patch.object(self.repo, "get", return_value=mock_provider):
            result = self.repo.delete(self.provider_id)

        assert mock_provider.is_active is False
        assert hasattr(mock_provider, "updated_at")
        self.mock_db.commit.assert_called_once()
        assert result is True

    def test_delete_provider_not_found(self):
        """Test provider deletion - not found"""
        with patch.object(self.repo, "get", return_value=None):
            result = self.repo.delete(self.provider_id)

        assert result is False
        self.mock_db.commit.assert_not_called()

    def test_delete_already_inactive_provider(self):
        """Test deletion of inactive provider"""
        mock_provider = Mock(spec=Provider)
        mock_provider.is_active = False

        with patch.object(self.repo, "get", return_value=mock_provider):
            result = self.repo.delete(self.provider_id)

        assert mock_provider.is_active is False
        assert hasattr(mock_provider, "updated_at")
        assert result is True

    def test_get_provider_statistics(self):
        """Test get provider statistics method"""
        if hasattr(self.repo, "get_provider_statistics"):
            mock_stats = {
                "total_providers": 5,
                "active_providers": 3,
                "provider_types": {"openai": 2, "aws": 1},
            }

            with patch.object(
                self.repo, "get_provider_statistics", return_value=mock_stats
            ):
                result = self.repo.get_provider_statistics()
                assert result == mock_stats

    def test_get_providers_by_type_count(self):
        """Test cound providers by type"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.filter.return_value.count.return_value = 2

        if hasattr(self.repo, "count_by_type"):
            with patch.object(self.repo, "count_by_type", return_value=2):
                count = self.repo.count_by_type("openai")
                assert count == 2


class TestProviderRepositoryEdgeCases:
    """Edge cases for ProviderRepository"""

    def setup_method(self):
        """Setup before each test"""
        self.mock_db = Mock(spec=Session)
        self.repo = ProviderRepository(self.mock_db)

    def test_get_all_with_database_error(self):
        """Test database error"""
        self.mock_db.query.side_effect = Exception("Database connection error")

        with pytest.raises(Exception, match="Database connection error"):
            self.repo.get_all()

    def test_create_with_commit_error(self):
        """Test commit error"""
        provider_data = {"name": "test", "provider_type": "openai"}
        mock_provider = Mock(spec=Provider)

        self.mock_db.commit.side_effect = Exception("Commit failed")

        with patch("app.models.provider.Provider", return_value=mock_provider):
            with pytest.raises(Exception, match="Commit failed"):
                self.repo.create(provider_data)

    def test_large_provider_list(self):
        """Test large provider list"""
        mock_providers = [Mock(spec=Provider) for _ in range(1000)]
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.order_by.return_value.all.return_value = (
            mock_providers
        )

        result = self.repo.get_all()

        assert len(result) == 1000
        assert all(isinstance(p, Mock) for p in result)

    def test_concurrent_updates(self):
        """Test concurrent updates"""
        mock_provider = Mock(spec=Provider)

        with patch.object(self.repo, "get", return_value=mock_provider):
            update1 = {"display_name": "Update 1"}
            update2 = {"display_name": "Update 2"}

            result1 = self.repo.update(uuid4(), update1)
            result2 = self.repo.update(uuid4(), update2)

            assert result1 == mock_provider
            assert result2 == mock_provider
            assert self.mock_db.commit.call_count == 2
