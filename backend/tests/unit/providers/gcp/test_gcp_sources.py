"""
Unit tests for GCP Data Sources Configuration
"""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from pipeline.sources.base import BaseSource
from providers.gcp.sources import GCPSource


class TestGCPSource:
    """Test cases for GCPSource class."""

    def setup_method(self):
        self.source = GCPSource()
        self.start_date = datetime(2024, 1, 1, tzinfo=UTC)
        self.end_date = datetime(2024, 1, 31, tzinfo=UTC)

    def test_inheritance(self):
        """Test that GCPSource inherits from BaseSource."""
        assert isinstance(self.source, BaseSource)
        assert hasattr(self.source, "get_sources")
        assert hasattr(self.source, "validate_source_configs")

    def test_get_sources_returns_list(self):
        """Test that get_sources returns a list."""
        sources = self.source.get_sources(self.start_date, self.end_date)

        assert isinstance(sources, list)
        assert len(sources) > 0

    def test_get_sources_structure(self):
        """Test that get_sources returns correctly structured sources."""
        sources = self.source.get_sources(self.start_date, self.end_date)

        assert len(sources) == 1

        billing_source = sources[0]

        assert "name" in billing_source
        assert "source_type" in billing_source
        assert "config" in billing_source

        assert billing_source["name"] == "billing_export"
        assert billing_source["source_type"] == "bigquery"
        assert isinstance(billing_source["config"], dict)

    def test_get_sources_config_structure(self):
        """Test the structure of the source configuration."""
        sources = self.source.get_sources(self.start_date, self.end_date)
        config = sources[0]["config"]

        assert "query_template" in config
        assert "query_params" in config
        assert "chunk_size" in config
        assert "use_legacy_sql" in config
        assert "partition_filter" in config

        assert isinstance(config["query_template"], str)
        assert isinstance(config["query_params"], dict)
        assert config["chunk_size"] == 10000
        assert config["use_legacy_sql"] is False
        assert config["partition_filter"] is True

    def test_get_sources_query_template_content(self):
        """Test the content of the query template."""
        sources = self.source.get_sources(self.start_date, self.end_date)
        query_template = sources[0]["config"]["query_template"]

        assert "SELECT *" in query_template
        assert "FROM {full_table_name}" in query_template
        assert "WHERE DATE(usage_start_time) >= DATE('{start_date}')" in query_template
        assert "AND DATE(usage_start_time) <= DATE('{end_date}')" in query_template
        assert "ORDER BY usage_start_time" in query_template

    def test_get_sources_query_params(self):
        """Test that query parameters are correctly formatted."""
        sources = self.source.get_sources(self.start_date, self.end_date)
        query_params = sources[0]["config"]["query_params"]

        assert "start_date" in query_params
        assert "end_date" in query_params

        assert query_params["start_date"] == "2024-01-01"
        assert query_params["end_date"] == "2024-01-31"

    def test_get_sources_different_date_range(self):
        """Test get_sources with different date ranges."""
        start_date = datetime(2023, 6, 15, tzinfo=UTC)
        end_date = datetime(2023, 6, 30, tzinfo=UTC)

        sources = self.source.get_sources(start_date, end_date)
        query_params = sources[0]["config"]["query_params"]

        assert query_params["start_date"] == "2023-06-15"
        assert query_params["end_date"] == "2023-06-30"

    def test_get_sources_same_start_end_date(self):
        """Test get_sources when start and end dates are the same."""
        same_date = datetime(2024, 3, 15, tzinfo=UTC)

        sources = self.source.get_sources(same_date, same_date)
        query_params = sources[0]["config"]["query_params"]

        assert query_params["start_date"] == "2024-03-15"
        assert query_params["end_date"] == "2024-03-15"

    def test_get_sources_timezone_handling(self):
        """Test get_sources with different timezones."""
        start_date = datetime(2024, 2, 1, 10, 30, tzinfo=UTC)
        end_date = datetime(2024, 2, 28, 15, 45, tzinfo=UTC)

        sources = self.source.get_sources(start_date, end_date)
        query_params = sources[0]["config"]["query_params"]

        # Should only use date part, ignoring time and timezone
        assert query_params["start_date"] == "2024-02-01"
        assert query_params["end_date"] == "2024-02-28"

    def test_get_sources_naive_datetime(self):
        """Test get_sources with naive datetime objects."""
        start_date = datetime(2024, 4, 1)
        end_date = datetime(2024, 4, 30)

        sources = self.source.get_sources(start_date, end_date)
        query_params = sources[0]["config"]["query_params"]

        assert query_params["start_date"] == "2024-04-01"
        assert query_params["end_date"] == "2024-04-30"

    @patch.object(GCPSource, "validate_source_configs")
    def test_get_sources_calls_validation(self, mock_validate):
        """Test that get_sources calls validate_source_configs."""
        mock_validate.return_value = []

        self.source.get_sources(self.start_date, self.end_date)

        mock_validate.assert_called_once()
        call_args = mock_validate.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0]["name"] == "billing_export"

    def test_validate_source_configs_success(self):
        """Test successful source configuration validation."""
        sources = [
            {
                "name": "test_source",
                "source_type": "bigquery",
                "config": {"query": "SELECT * FROM table"},
            }
        ]

        validated = self.source.validate_source_configs(sources)

        assert validated == sources

    def test_validate_source_configs_missing_name(self):
        """Test validation fails when name is missing."""
        sources = [
            {"source_type": "bigquery", "config": {"query": "SELECT * FROM table"}}
        ]

        with pytest.raises(ValueError, match="Source 0 missing required field: name"):
            self.source.validate_source_configs(sources)

    def test_validate_source_configs_missing_source_type(self):
        """Test validation fails when source_type is missing."""
        sources = [{"name": "test_source", "config": {"query": "SELECT * FROM table"}}]

        with pytest.raises(
            ValueError, match="Source 'test_source' missing required field: source_type"
        ):
            self.source.validate_source_configs(sources)

    def test_validate_source_configs_missing_config(self):
        """Test validation fails when config is missing."""
        sources = [{"name": "test_source", "source_type": "bigquery"}]

        with pytest.raises(
            ValueError, match="Source 'test_source' missing required field: config"
        ):
            self.source.validate_source_configs(sources)

    def test_validate_source_configs_invalid_source_type(self):
        """Test validation fails with invalid source_type."""
        sources = [
            {
                "name": "test_source",
                "source_type": "invalid_type",
                "config": {"query": "SELECT * FROM table"},
            }
        ]

        with pytest.raises(
            ValueError,
            match="Source 'test_source' has invalid source_type: invalid_type",
        ):
            self.source.validate_source_configs(sources)

    def test_validate_source_configs_not_dict(self):
        """Test validation fails when source is not a dictionary."""
        sources = ["not_a_dict"]

        with pytest.raises(ValueError, match="Source 0 must be a dictionary"):
            self.source.validate_source_configs(sources)

    def test_validate_source_configs_multiple_sources(self):
        """Test validation with multiple sources."""
        sources = [
            {
                "name": "source1",
                "source_type": "bigquery",
                "config": {"query": "SELECT * FROM table1"},
            },
            {
                "name": "source2",
                "source_type": "rest_api",
                "config": {"endpoint": "/api/data"},
            },
        ]

        validated = self.source.validate_source_configs(sources)

        assert validated == sources
        assert len(validated) == 2

    def test_validate_source_configs_empty_list(self):
        """Test validation with empty source list."""
        sources = []

        validated = self.source.validate_source_configs(sources)

        assert validated == []

    @pytest.mark.parametrize(
        "valid_source_type",
        ["rest_api", "filesystem", "sql_database", "bigquery", "custom"],
    )
    def test_validate_source_configs_valid_types(self, valid_source_type):
        """Test validation accepts all valid source types."""
        sources = [
            {
                "name": "test_source",
                "source_type": valid_source_type,
                "config": {"test": "config"},
            }
        ]

        validated = self.source.validate_source_configs(sources)

        assert validated == sources

    def test_integration_get_sources_validates_correctly(self):
        """Integration test: ensure get_sources returns valid configurations."""
        sources = self.source.get_sources(self.start_date, self.end_date)

        validated = self.source.validate_source_configs(sources)

        assert validated == sources
        assert len(validated) == 1
        assert validated[0]["source_type"] == "bigquery"

    def test_query_template_formatting_readiness(self):
        """Test that query template is ready for string formatting."""
        sources = self.source.get_sources(self.start_date, self.end_date)
        query_template = sources[0]["config"]["query_template"]
        query_params = sources[0]["config"]["query_params"]

        try:
            formatted_query = query_template.format(
                full_table_name="project.dataset.table", **query_params
            )

            assert "project.dataset.table" in formatted_query
            assert "2024-01-01" in formatted_query
            assert "2024-01-31" in formatted_query
            assert "{" not in formatted_query
        except KeyError as e:
            pytest.fail(f"Query template missing parameter: {e}")

    def test_chunk_size_configuration(self):
        """Test that chunk size is appropriately configured."""
        sources = self.source.get_sources(self.start_date, self.end_date)
        chunk_size = sources[0]["config"]["chunk_size"]

        assert isinstance(chunk_size, int)
        assert chunk_size > 0
        assert chunk_size == 10000

    def test_bigquery_options_configuration(self):
        """Test BigQuery-specific options are correctly configured."""
        sources = self.source.get_sources(self.start_date, self.end_date)
        config = sources[0]["config"]

        # Legacy SQL is disabled (modern SQL is preferred)
        assert config["use_legacy_sql"] is False

        # Partition filtering is enabled for cost optimization
        assert config["partition_filter"] is True
