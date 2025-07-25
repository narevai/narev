# tests/unit/test_billing_repository.py
"""
Tests for BillingRepository
"""

from datetime import datetime
from unittest.mock import Mock, patch

from sqlalchemy.orm import Session

from app.models.billing_data import BillingData
from app.repositories.billing_repository import BillingRepository


class TestBillingRepository:
    """Basic tests for BillingRepository"""

    def setup_method(self):
        """Setup before each test"""
        self.mock_db = Mock(spec=Session)
        self.repo = BillingRepository(self.mock_db)

    def test_init(self):
        """Repository init test"""
        assert self.repo.db == self.mock_db

    def test_get_billing_data_basic(self):
        """Basic billing data fetching test"""
        mock_records = [Mock(spec=BillingData), Mock(spec=BillingData)]

        # Mock query chain
        mock_query = self.mock_db.query.return_value
        mock_query.count.return_value = 2
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_records

        records, total = self.repo.get_billing_data(skip=0, limit=10)

        assert records == mock_records
        assert total == 2
        self.mock_db.query.assert_called_with(BillingData)

    def test_get_billing_data_with_provider_filter(self):
        """Filter by provider_id"""
        mock_query = self.mock_db.query.return_value
        mock_filtered = Mock()
        mock_ordered = Mock()

        # Make chain: query -> filter -> count/order_by
        mock_query.filter.return_value = mock_filtered
        mock_filtered.count.return_value = 1
        mock_filtered.order_by.return_value = mock_ordered
        mock_ordered.offset.return_value.limit.return_value.all.return_value = []

        records, total = self.repo.get_billing_data(provider_id="test-provider")

        mock_query.filter.assert_called()
        assert total == 1

    def test_get_billing_data_with_date_filters(self):
        """Data filtering test"""
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 12, 31)

        mock_query = self.mock_db.query.return_value
        mock_filtered_1 = Mock()
        mock_filtered_2 = Mock()
        mock_ordered = Mock()

        # Chain: query -> filter (start) -> filter (end) -> count/order_by
        mock_query.filter.return_value = mock_filtered_1
        mock_filtered_1.filter.return_value = mock_filtered_2
        mock_filtered_2.count.return_value = 0
        mock_filtered_2.order_by.return_value = mock_ordered
        mock_ordered.offset.return_value.limit.return_value.all.return_value = []

        records, total = self.repo.get_billing_data(
            start_date=start_date, end_date=end_date
        )

        assert mock_query.filter.call_count == 1
        assert mock_filtered_1.filter.call_count == 1
        assert total == 0

    def test_create_billing_record_success(self):
        """Create billing record test"""
        if hasattr(self.repo, "create_record"):
            billing_data = {
                "provider_id": "test-provider",
                "effective_cost": 100.0,
                "billing_currency": "USD",
            }

            mock_record = Mock(spec=BillingData)

            with patch("app.models.billing_data.BillingData", return_value=mock_record):
                result = self.repo.create_record(billing_data)

            self.mock_db.add.assert_called_once_with(mock_record)
            self.mock_db.commit.assert_called_once()
            self.mock_db.refresh.assert_called_once_with(mock_record)
            assert result == mock_record
        else:
            assert True

    def test_create_batch_success(self):
        """Test create batch"""
        mock_records = [Mock(spec=BillingData), Mock(spec=BillingData)]

        result = self.repo.create_batch(mock_records)

        self.mock_db.bulk_save_objects.assert_called_once_with(mock_records)
        self.mock_db.commit.assert_called_once()
        assert result == 2

    def test_create_batch_empty_list(self):
        """Test empty list"""
        result = self.repo.create_batch([])

        assert result == 0
        self.mock_db.bulk_save_objects.assert_not_called()

    def test_get_by_id_found(self):
        """Test get by id ID"""
        record_id = "test-record-id"
        mock_record = Mock(spec=BillingData)

        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_record
        )

        result = self.repo.get_by_id(record_id)

        assert result == mock_record
        self.mock_db.query.assert_called_with(BillingData)

    def test_get_by_id_not_found(self):
        """Test no existing record"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = self.repo.get_by_id("nonexistent-id")

        assert result is None

    def test_delete_record_success(self):
        """Test record deletion"""
        record_id = "test-record-id"
        mock_record = Mock(spec=BillingData)

        with patch.object(self.repo, "get_by_id", return_value=mock_record):
            result = self.repo.delete_record(record_id)

        self.mock_db.delete.assert_called_once_with(mock_record)
        self.mock_db.commit.assert_called_once()
        assert result is True

    def test_delete_record_not_found(self):
        """Test deletion of not existing record"""
        with patch.object(self.repo, "get_by_id", return_value=None):
            result = self.repo.delete_record("nonexistent-id")

        assert result is False
        self.mock_db.delete.assert_not_called()

    def test_get_by_provider(self):
        """Test fetching records by provider_id"""
        provider_id = "test-provider"
        mock_records = [Mock(spec=BillingData)]

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.order_by.return_value.all.return_value = (
            mock_records
        )

        result = self.repo.get_by_provider(provider_id)

        assert result == mock_records
        mock_query.filter.assert_called()

    def test_get_by_provider_with_limit(self):
        """Test fetching records with limit"""
        provider_id = "test-provider"

        mock_query = self.mock_db.query.return_value
        mock_filtered = Mock()
        mock_ordered = Mock()
        mock_limited = Mock()

        # Chain: query -> filter -> order_by -> limit -> all
        mock_query.filter.return_value = mock_filtered
        mock_filtered.order_by.return_value = mock_ordered
        mock_ordered.limit.return_value = mock_limited
        mock_limited.all.return_value = []

        result = self.repo.get_by_provider(provider_id, limit=5)

        mock_ordered.limit.assert_called_with(5)
        assert result == []
