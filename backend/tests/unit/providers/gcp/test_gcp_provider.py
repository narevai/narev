"""
Unit tests for GCP Provider Implementation
"""

from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest

from app.models.auth import AuthMethod
from providers.gcp.provider import GCPProvider
from providers.gcp.sources import GCPSource


class TestGCPProvider:
    """Test cases for GCPProvider class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.valid_auth_config = {
            "method": AuthMethod.SERVICE_ACCOUNT,
            "credentials": {
                "type": "service_account",
                "project_id": "test-project-123",
                "private_key": "-----BEGIN PRIVATE KEY-----\ntest-key\n-----END PRIVATE KEY-----\n",
                "client_email": "test@test-project-123.iam.gserviceaccount.com",
            },
        }

        self.valid_config = {
            "auth_config": self.valid_auth_config,
            "additional_config": {
                "dataset_id": "billing_export",
                "table_name": "gcp_billing_export_v1_test",
                "location": "US",
            },
        }

        self.alternative_config = {
            "auth_config": self.valid_auth_config,
            "dataset_id": "billing_export",
            "table_name": "gcp_billing_export_v1_test",
            "location": "EU",
        }

    @patch("providers.gcp.provider.GCPAuth")
    def test_init_with_valid_config(self, mock_auth_class):
        """Test GCPProvider initialization with valid configuration."""
        mock_auth = Mock()
        mock_auth.get_project_id.return_value = "test-project-123"
        mock_auth.create_bigquery_client.return_value = Mock()
        mock_auth_class.return_value = mock_auth

        provider = GCPProvider(self.valid_config)

        assert provider.project_id == "test-project-123"
        assert provider.dataset_id == "billing_export"
        assert provider.table_name == "gcp_billing_export_v1_test"
        assert provider.location == "US"
        assert provider.source_class == GCPSource

        mock_auth_class.assert_called_once_with(self.valid_auth_config)
        mock_auth.create_bigquery_client.assert_called_once_with(
            project_id="test-project-123", location="US"
        )

    @patch("providers.gcp.provider.GCPAuth")
    def test_init_with_alternative_config_format(self, mock_auth_class):
        """Test GCPProvider initialization with alternative config format."""
        mock_auth = Mock()
        mock_auth.get_project_id.return_value = "test-project-123"
        mock_auth.create_bigquery_client.return_value = Mock()
        mock_auth_class.return_value = mock_auth

        provider = GCPProvider(self.alternative_config)

        assert provider.dataset_id == "billing_export"
        assert provider.table_name == "gcp_billing_export_v1_test"
        assert (
            provider.location == "US"
        )  # Default location is applied due to provider logic

    @patch("providers.gcp.provider.GCPAuth")
    def test_init_default_location(self, mock_auth_class):
        """Test GCPProvider initialization with default location."""
        config = {
            "auth_config": self.valid_auth_config,
            "additional_config": {
                "dataset_id": "billing_export",
                "table_name": "gcp_billing_export_v1_test",
            },
        }

        mock_auth = Mock()
        mock_auth.get_project_id.return_value = "test-project-123"
        mock_auth.create_bigquery_client.return_value = Mock()
        mock_auth_class.return_value = mock_auth

        provider = GCPProvider(config)

        assert provider.location == "US"

    @patch("providers.gcp.provider.GCPAuth")
    def test_init_missing_project_id(self, mock_auth_class):
        """Test GCPProvider initialization fails when project_id is missing."""
        mock_auth = Mock()
        mock_auth.get_project_id.return_value = None
        mock_auth_class.return_value = mock_auth

        with pytest.raises(
            ValueError, match="project_id not found in service account credentials"
        ):
            GCPProvider(self.valid_config)

    @patch("providers.gcp.provider.GCPAuth")
    def test_init_missing_required_config(self, mock_auth_class):
        """Test GCPProvider initialization fails when required config is missing."""
        config = {
            "auth_config": self.valid_auth_config,
            "additional_config": {"dataset_id": "billing_export"},
        }

        mock_auth = Mock()
        mock_auth.get_project_id.return_value = "test-project-123"
        mock_auth_class.return_value = mock_auth

        with pytest.raises(ValueError, match="Missing required GCP configuration"):
            GCPProvider(config)

    @patch("providers.gcp.provider.GCPAuth")
    def test_init_bigquery_client_failure(self, mock_auth_class):
        """Test GCPProvider initialization fails when BigQuery client creation fails."""
        mock_auth = Mock()
        mock_auth.get_project_id.return_value = "test-project-123"
        mock_auth.create_bigquery_client.side_effect = Exception("Auth failed")
        mock_auth_class.return_value = mock_auth

        with pytest.raises(Exception, match="Auth failed"):
            GCPProvider(self.valid_config)

    @patch("providers.gcp.provider.GCPAuth")
    @pytest.mark.asyncio
    async def test_fetch_billing_data_success(self, mock_auth_class):
        """Test successful billing data fetching."""
        mock_auth = Mock()
        mock_auth.get_project_id.return_value = "test-project-123"
        mock_client = Mock()
        mock_auth.create_bigquery_client.return_value = mock_client
        mock_auth_class.return_value = mock_auth

        mock_row1 = {"cost": "10.50", "service": "Compute Engine"}
        mock_row2 = {"cost": "5.25", "service": "Cloud Storage"}
        mock_results = [mock_row1, mock_row2]

        mock_query_job = Mock()
        mock_query_job.result.return_value = mock_results
        mock_client.query.return_value = mock_query_job

        provider = GCPProvider(self.valid_config)

        start_date = datetime(2024, 1, 1, tzinfo=UTC)
        end_date = datetime(2024, 1, 31, tzinfo=UTC)

        billing_data = await provider.fetch_billing_data(start_date, end_date)

        assert len(billing_data) == 2
        assert billing_data[0] == mock_row1
        assert billing_data[1] == mock_row2

        expected_query = """
        SELECT *
        FROM `test-project-123.billing_export.gcp_billing_export_v1_test`
        WHERE export_time >= TIMESTAMP('2024-01-01T00:00:00+00:00')
          AND export_time < TIMESTAMP('2024-01-31T00:00:00+00:00')
        ORDER BY export_time DESC
        """
        mock_client.query.assert_called_once()
        actual_query = mock_client.query.call_args[0][0]
        assert " ".join(actual_query.split()) == " ".join(expected_query.split())

    @patch("providers.gcp.provider.GCPAuth")
    @pytest.mark.asyncio
    async def test_fetch_billing_data_query_error(self, mock_auth_class):
        """Test billing data fetching handles query errors."""
        mock_auth = Mock()
        mock_auth.get_project_id.return_value = "test-project-123"
        mock_client = Mock()
        mock_auth.create_bigquery_client.return_value = mock_client
        mock_auth_class.return_value = mock_auth

        mock_client.query.side_effect = Exception("Query failed")

        provider = GCPProvider(self.valid_config)

        start_date = datetime(2024, 1, 1, tzinfo=UTC)
        end_date = datetime(2024, 1, 31, tzinfo=UTC)

        with pytest.raises(Exception, match="Query failed"):
            await provider.fetch_billing_data(start_date, end_date)

    @patch("providers.gcp.provider.GCPAuth")
    def test_get_source_config(self, mock_auth_class):
        """Test source configuration generation."""
        mock_auth = Mock()
        mock_auth.get_project_id.return_value = "test-project-123"
        mock_auth.create_bigquery_client.return_value = Mock()
        mock_auth_class.return_value = mock_auth

        provider = GCPProvider(self.valid_config)
        config = provider.get_source_config()

        expected_config = {
            "provider_type": "gcp",
            "project_id": "test-project-123",
            "dataset_id": "billing_export",
            "table_name": "gcp_billing_export_v1_test",
            "location": "US",
            "auth_config": self.valid_auth_config,
            "_auth_handler": mock_auth,
        }

        assert config == expected_config

    @patch("providers.gcp.provider.GCPAuth")
    @patch("providers.gcp.provider.GCPSource")
    def test_get_sources(self, mock_source_class, mock_auth_class):
        """Test sources retrieval."""
        mock_auth = Mock()
        mock_auth.get_project_id.return_value = "test-project-123"
        mock_auth.create_bigquery_client.return_value = Mock()
        mock_auth_class.return_value = mock_auth

        mock_source = Mock()
        expected_sources = [{"source": "test"}]
        mock_source.get_sources.return_value = expected_sources
        mock_source_class.return_value = mock_source

        provider = GCPProvider(self.valid_config)

        start_date = datetime(2024, 1, 1, tzinfo=UTC)
        end_date = datetime(2024, 1, 31, tzinfo=UTC)

        sources = provider.get_sources(start_date, end_date)

        assert sources == expected_sources
        mock_source.get_sources.assert_called_once_with(start_date, end_date)

    @patch("providers.gcp.provider.GCPAuth")
    def test_test_connection_success(self, mock_auth_class):
        """Test successful connection test."""
        mock_auth = Mock()
        mock_auth.get_project_id.return_value = "test-project-123"
        mock_client = Mock()
        mock_auth.create_bigquery_client.return_value = mock_client
        mock_auth_class.return_value = mock_auth

        mock_dataset = Mock()
        mock_client.get_dataset.return_value = mock_dataset

        mock_table = Mock()
        mock_table.num_bytes = 1024 * 1024 * 100
        mock_client.get_table.return_value = mock_table

        mock_query_job = Mock()
        mock_query_job.__iter__ = Mock(return_value=iter([{"count": 1000}]))
        mock_client.query.return_value = mock_query_job

        provider = GCPProvider(self.valid_config)
        result = provider.test_connection()

        assert result["success"] is True
        assert result["message"] == "Successfully connected to BigQuery"
        assert result["details"]["project_id"] == "test-project-123"
        assert result["details"]["dataset_id"] == "billing_export"
        assert result["details"]["table_name"] == "gcp_billing_export_v1_test"
        assert result["details"]["location"] == "US"
        assert result["details"]["row_count"] == 1000
        assert result["details"]["table_size_mb"] == 100.0
        assert result["details"]["auth_method"] == AuthMethod.SERVICE_ACCOUNT

    @patch("providers.gcp.provider.GCPAuth")
    def test_test_connection_dataset_not_found(self, mock_auth_class):
        """Test connection test with dataset not found error."""
        mock_auth = Mock()
        mock_auth.get_project_id.return_value = "test-project-123"
        mock_client = Mock()
        mock_auth.create_bigquery_client.return_value = mock_client
        mock_auth_class.return_value = mock_auth

        exception = Exception("404 Dataset not found")
        mock_client.get_dataset.side_effect = exception

        provider = GCPProvider(self.valid_config)
        result = provider.test_connection()

        assert result["success"] is False
        assert "Dataset 'billing_export' not found" in result["message"]
        assert result["details"]["error_type"] == "Exception"

    @patch("providers.gcp.provider.GCPAuth")
    def test_test_connection_table_not_found(self, mock_auth_class):
        """Test connection test with table not found error."""
        mock_auth = Mock()
        mock_auth.get_project_id.return_value = "test-project-123"
        mock_client = Mock()
        mock_auth.create_bigquery_client.return_value = mock_client
        mock_auth_class.return_value = mock_auth

        mock_dataset = Mock()
        mock_client.get_dataset.return_value = mock_dataset
        exception = Exception("404 Table not found")
        mock_client.get_table.side_effect = exception

        provider = GCPProvider(self.valid_config)
        result = provider.test_connection()

        assert result["success"] is False
        assert "Table 'gcp_billing_export_v1_test' not found" in result["message"]

    @patch("providers.gcp.provider.GCPAuth")
    def test_test_connection_permission_denied(self, mock_auth_class):
        """Test connection test with permission denied error."""
        mock_auth = Mock()
        mock_auth.get_project_id.return_value = "test-project-123"
        mock_client = Mock()
        mock_auth.create_bigquery_client.return_value = mock_client
        mock_auth_class.return_value = mock_auth

        exception = Exception("403 Permission denied")
        mock_client.get_dataset.side_effect = exception

        provider = GCPProvider(self.valid_config)
        result = provider.test_connection()

        assert result["success"] is False
        assert (
            "Permission denied - check service account permissions" in result["message"]
        )
        assert result["details"]["error_type"] == "Exception"

    @patch("providers.gcp.provider.GCPAuth")
    def test_test_connection_auth_failed(self, mock_auth_class):
        """Test connection test with authentication failure."""
        mock_auth = Mock()
        mock_auth.get_project_id.return_value = "test-project-123"
        mock_client = Mock()
        mock_auth.create_bigquery_client.return_value = mock_client
        mock_auth_class.return_value = mock_auth

        mock_client.get_dataset.side_effect = Exception("401 Unauthorized")

        provider = GCPProvider(self.valid_config)
        result = provider.test_connection()

        assert result["success"] is False
        assert "Authentication failed - check credentials" in result["message"]

    @patch("providers.gcp.provider.GCPAuth")
    def test_test_connection_generic_error(self, mock_auth_class):
        """Test connection test with generic error."""
        mock_auth = Mock()
        mock_auth.get_project_id.return_value = "test-project-123"
        mock_client = Mock()
        mock_auth.create_bigquery_client.return_value = mock_client
        mock_auth_class.return_value = mock_auth

        mock_client.get_dataset.side_effect = Exception("Something went wrong")

        provider = GCPProvider(self.valid_config)
        result = provider.test_connection()

        assert result["success"] is False
        assert "Connection test failed: Something went wrong" in result["message"]

    @patch("providers.gcp.provider.GCPAuth")
    def test_get_auth_method(self, mock_auth_class):
        """Test getting authentication method."""
        mock_auth = Mock()
        mock_auth.get_project_id.return_value = "test-project-123"
        mock_auth.create_bigquery_client.return_value = Mock()
        mock_auth_class.return_value = mock_auth

        provider = GCPProvider(self.valid_config)
        auth_method = provider.get_auth_method()

        assert auth_method == AuthMethod.SERVICE_ACCOUNT

    @patch("providers.gcp.provider.GCPAuth")
    def test_get_auth_method_no_config(self, mock_auth_class):
        """Test getting authentication method when no auth config."""
        config = self.valid_config.copy()
        config["auth_config"] = None

        mock_auth = Mock()
        mock_auth.get_project_id.return_value = "test-project-123"
        mock_auth.create_bigquery_client.return_value = Mock()
        mock_auth_class.return_value = mock_auth

        provider = GCPProvider(config)
        auth_method = provider.get_auth_method()

        assert auth_method == "default"

    @patch("providers.gcp.provider.GCPAuth")
    def test_get_bigquery_config(self, mock_auth_class):
        """Test BigQuery configuration retrieval."""
        mock_auth = Mock()
        mock_auth.get_project_id.return_value = "test-project-123"
        mock_auth.create_bigquery_client.return_value = Mock()
        mock_auth_class.return_value = mock_auth

        provider = GCPProvider(self.valid_config)
        config = provider.get_bigquery_config()

        expected_config = {
            "project_id": "test-project-123",
            "dataset_id": "billing_export",
            "table_name": "gcp_billing_export_v1_test",
            "location": "US",
        }

        assert config == expected_config

    @patch("providers.gcp.provider.GCPAuth")
    def test_get_credentials(self, mock_auth_class):
        """Test credentials retrieval."""
        mock_credentials = Mock()
        mock_auth = Mock()
        mock_auth.get_project_id.return_value = "test-project-123"
        mock_auth.create_bigquery_client.return_value = Mock()
        mock_auth.get_credentials.return_value = mock_credentials
        mock_auth_class.return_value = mock_auth

        provider = GCPProvider(self.valid_config)
        credentials = provider.get_credentials()

        assert credentials == mock_credentials
        mock_auth.get_credentials.assert_called_once()

    @patch("providers.gcp.provider.GCPAuth")
    def test_get_credentials_json(self, mock_auth_class):
        """Test credentials JSON retrieval."""
        mock_auth = Mock()
        mock_auth.get_project_id.return_value = "test-project-123"
        mock_auth.create_bigquery_client.return_value = Mock()
        mock_auth.auth_config = self.valid_auth_config
        mock_auth_class.return_value = mock_auth

        provider = GCPProvider(self.valid_config)
        credentials_json = provider.get_credentials_json()

        assert credentials_json == self.valid_auth_config["credentials"]

    @patch("providers.gcp.provider.GCPAuth")
    def test_credentials_json_property(self, mock_auth_class):
        """Test credentials JSON property compatibility."""
        mock_auth = Mock()
        mock_auth.get_project_id.return_value = "test-project-123"
        mock_auth.create_bigquery_client.return_value = Mock()
        mock_auth.auth_config = self.valid_auth_config
        mock_auth_class.return_value = mock_auth

        provider = GCPProvider(self.valid_config)
        credentials_json = provider.credentials_json

        assert credentials_json == self.valid_auth_config["credentials"]

    @patch("providers.gcp.provider.GCPAuth")
    def test_test_connection_empty_query_result(self, mock_auth_class):
        """Test connection test with empty query result."""
        mock_auth = Mock()
        mock_auth.get_project_id.return_value = "test-project-123"
        mock_client = Mock()
        mock_auth.create_bigquery_client.return_value = mock_client
        mock_auth_class.return_value = mock_auth

        mock_client.get_dataset.return_value = Mock()
        mock_table = Mock()
        mock_table.num_bytes = None
        mock_client.get_table.return_value = mock_table

        mock_query_job = Mock()
        mock_query_job.__iter__ = Mock(return_value=iter([]))
        mock_client.query.return_value = mock_query_job

        provider = GCPProvider(self.valid_config)
        result = provider.test_connection()

        assert result["success"] is True
        assert result["details"]["row_count"] == 0
        assert result["details"]["table_size_mb"] == 0
