"""
Unit tests for AWS Data Sources Configuration
"""

from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest

from pipeline.sources.base import BaseSource
from providers.aws.sources import AWSSource


class TestAWSSource:
    """Test cases for AWSSource class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.source = AWSSource()
        self.start_date = datetime(2024, 1, 1, tzinfo=UTC)
        self.end_date = datetime(2024, 1, 31, tzinfo=UTC)

    def test_inheritance(self):
        """Test that AWSSource inherits from BaseSource."""
        assert isinstance(self.source, BaseSource)
        assert hasattr(self.source, "get_sources")
        assert hasattr(self.source, "validate_source_configs")

    def test_init_without_provider(self):
        """Test AWSSource initialization without provider."""
        source = AWSSource()
        assert source.provider is None

    def test_init_with_provider(self):
        """Test AWSSource initialization with provider."""
        mock_provider = Mock()
        source = AWSSource(provider=mock_provider)
        assert source.provider == mock_provider

    def test_get_sources_returns_list(self):
        """Test that get_sources returns a list."""
        sources = self.source.get_sources(self.start_date, self.end_date)

        assert isinstance(sources, list)
        assert len(sources) > 0

    def test_get_sources_structure(self):
        """Test that get_sources returns correctly structured sources."""
        sources = self.source.get_sources(self.start_date, self.end_date)

        # Should have exactly one cost and usage report source
        assert len(sources) == 1

        cur_source = sources[0]

        # Check required fields
        assert "name" in cur_source
        assert "source_type" in cur_source
        assert "config" in cur_source

        # Check field values (defaults to FOCUS since no provider)
        assert cur_source["name"] == "aws_focus_export"
        assert cur_source["source_type"] == "filesystem"
        assert isinstance(cur_source["config"], dict)

    def test_get_sources_config_structure(self):
        """Test the structure of the source configuration."""
        sources = self.source.get_sources(self.start_date, self.end_date)
        config = sources[0]["config"]

        # Check required config fields
        assert "file_pattern" in config
        assert "parse_options" in config
        assert "filters" in config

        # Check parse options structure
        parse_options = config["parse_options"]
        assert "compression" in parse_options
        assert "format" in parse_options
        assert parse_options["compression"] == "snappy"  # FOCUS uses snappy
        assert parse_options["format"] == "parquet"  # FOCUS uses parquet

        # Metadata structure
        metadata = config["metadata"]
        assert "export_format" in metadata
        assert "schema_version" in metadata
        assert "provider" in metadata
        assert metadata["export_format"] == "focus_1_0"
        assert metadata["schema_version"] == "1.0"
        assert metadata["provider"] == "aws"

        # Check filters structure
        filters = config["filters"]
        assert "date_column" in filters
        assert "start_date" in filters
        assert "end_date" in filters
        assert filters["date_column"] == "ChargePeriodStart"  # FOCUS field name

    def test_get_sources_without_provider(self):
        """Test get_sources without provider (no filesystem config)."""
        sources = self.source.get_sources(self.start_date, self.end_date)
        config = sources[0]["config"]

        # Should have FOCUS format config structure (no filesystem config)
        expected_keys = {"file_pattern", "parse_options", "filters", "metadata"}
        assert set(config.keys()) == expected_keys

    def test_get_sources_with_provider_filesystem_config(self):
        """Test get_sources with provider that has filesystem config."""
        mock_provider = Mock()
        mock_provider.get_filesystem_config.return_value = {
            "bucket_name": "test-bucket",
            "aws_region": "us-east-1",
            "credentials": {"access_key": "test"},
        }

        source = AWSSource(provider=mock_provider)
        sources = source.get_sources(self.start_date, self.end_date)
        config = sources[0]["config"]

        # Should include filesystem config from provider
        assert config["bucket_name"] == "test-bucket"
        assert config["aws_region"] == "us-east-1"
        assert config["credentials"] == {"access_key": "test"}

        # Should still have other required fields
        assert "file_pattern" in config
        assert "parse_options" in config
        assert "filters" in config

    def test_get_sources_with_provider_no_filesystem_config(self):
        """Test get_sources with provider that doesn't have get_filesystem_config."""
        mock_provider = Mock(spec=[])  # Provider without get_filesystem_config method

        source = AWSSource(provider=mock_provider)
        sources = source.get_sources(self.start_date, self.end_date)
        config = sources[0]["config"]

        # Should have FOCUS format config structure (no filesystem config)
        expected_keys = {"file_pattern", "parse_options", "filters", "metadata"}
        assert set(config.keys()) == expected_keys

    def test_get_sources_filters_date_format(self):
        """Test that filters contain properly formatted dates."""
        start_date = datetime(2024, 2, 15, 10, 30, 0, tzinfo=UTC)
        end_date = datetime(2024, 2, 29, 23, 59, 59, tzinfo=UTC)

        sources = self.source.get_sources(start_date, end_date)
        filters = sources[0]["config"]["filters"]

        assert filters["start_date"] == "2024-02-15T10:30:00+00:00"
        assert filters["end_date"] == "2024-02-29T23:59:59+00:00"

    def test_get_sources_calls_validation(self):
        """Test that get_sources calls validate_source_configs."""
        with patch.object(self.source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []

            self.source.get_sources(self.start_date, self.end_date)

            mock_validate.assert_called_once()
            # Check that validation was called with correct structure
            call_args = mock_validate.call_args[0][0]
            assert len(call_args) == 1
            # Should default to FOCUS format
            assert call_args[0]["name"] == "aws_focus_export"

    def test_build_focus_file_pattern(self):
        """Test FOCUS file pattern building."""
        start_date = datetime(2024, 3, 1, tzinfo=UTC)
        end_date = datetime(2024, 3, 31, tzinfo=UTC)

        pattern = self.source._build_focus_file_pattern(start_date, end_date)

        # FOCUS uses general pattern, filtering is done by date column
        assert pattern == "**/*.parquet"

    def test_build_legacy_file_pattern_same_month(self):
        """Test legacy CUR file pattern building for same month."""
        start_date = datetime(2024, 1, 15, tzinfo=UTC)
        end_date = datetime(2024, 1, 31, tzinfo=UTC)

        pattern = self.source._build_legacy_file_pattern(start_date, end_date)

        assert pattern == "**/202401*/**/*.parquet"

    def test_build_legacy_file_pattern_different_months(self):
        """Test legacy file pattern building for dates across different months."""
        start_date = datetime(2023, 12, 1, tzinfo=UTC)
        end_date = datetime(2024, 1, 31, tzinfo=UTC)

        pattern = self.source._build_legacy_file_pattern(start_date, end_date)

        assert pattern == "**/*.parquet"

    def test_validate_source_configs_success(self):
        """Test successful source configuration validation."""
        sources = [
            {
                "name": "test_source",
                "source_type": "filesystem",
                "config": {"file_pattern": "**/*.csv"},
            }
        ]

        validated = self.source.validate_source_configs(sources)

        assert validated == sources

    def test_validate_source_configs_missing_name(self):
        """Test validation fails when name is missing."""
        sources = [
            {"source_type": "filesystem", "config": {"file_pattern": "**/*.csv"}}
        ]

        with pytest.raises(ValueError, match="Source 0 missing required field: name"):
            self.source.validate_source_configs(sources)

    def test_validate_source_configs_missing_source_type(self):
        """Test validation fails when source_type is missing."""
        sources = [{"name": "test_source", "config": {"file_pattern": "**/*.csv"}}]

        with pytest.raises(
            ValueError, match="Source 'test_source' missing required field: source_type"
        ):
            self.source.validate_source_configs(sources)

    def test_validate_source_configs_missing_config(self):
        """Test validation fails when config is missing."""
        sources = [{"name": "test_source", "source_type": "filesystem"}]

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
                "config": {"file_pattern": "**/*.csv"},
            }
        ]

        with pytest.raises(
            ValueError,
            match="Source 'test_source' has invalid source_type: invalid_type",
        ):
            self.source.validate_source_configs(sources)

    def test_validate_source_configs_filesystem_type_valid(self):
        """Test validation passes with filesystem source type."""
        sources = [
            {
                "name": "test_source",
                "source_type": "filesystem",
                "config": {"file_pattern": "**/*.csv"},
            }
        ]

        validated = self.source.validate_source_configs(sources)
        assert validated == sources

    def test_integration_get_sources_validates_correctly(self):
        """Integration test: ensure get_sources returns valid configurations."""
        sources = self.source.get_sources(self.start_date, self.end_date)

        # This should not raise any exceptions
        validated = self.source.validate_source_configs(sources)

        assert validated == sources
        assert len(validated) == 1
        assert validated[0]["source_type"] == "filesystem"

    def test_different_date_ranges(self):
        """Test get_sources with different date ranges."""
        # Test various date ranges
        test_cases = [
            (datetime(2024, 1, 1, tzinfo=UTC), datetime(2024, 1, 31, tzinfo=UTC)),
            (datetime(2024, 6, 15, tzinfo=UTC), datetime(2024, 7, 15, tzinfo=UTC)),
            (datetime(2023, 12, 1, tzinfo=UTC), datetime(2024, 2, 28, tzinfo=UTC)),
        ]

        for start_date, end_date in test_cases:
            sources = self.source.get_sources(start_date, end_date)

            assert len(sources) == 1
            config = sources[0]["config"]

            # Verify dates are properly set in filters
            assert config["filters"]["start_date"] == start_date.isoformat()
            assert config["filters"]["end_date"] == end_date.isoformat()

            # Verify file pattern is generated
            assert "file_pattern" in config
            assert config["file_pattern"].endswith("*.parquet")

    def test_parse_options_configuration(self):
        """Test that parse options are correctly configured."""
        sources = self.source.get_sources(self.start_date, self.end_date)
        parse_options = sources[0]["config"]["parse_options"]

        # FOCUS format uses parquet with snappy compression
        assert parse_options["compression"] == "snappy"
        assert parse_options["format"] == "parquet"

        # Ensure options are strings
        assert isinstance(parse_options["compression"], str)
        assert isinstance(parse_options["format"], str)

    def test_date_column_configuration(self):
        """Test that date column is correctly configured for AWS FOCUS."""
        sources = self.source.get_sources(self.start_date, self.end_date)
        filters = sources[0]["config"]["filters"]

        # AWS FOCUS uses ChargePeriodStart as the primary date column
        assert filters["date_column"] == "ChargePeriodStart"

    def test_provider_interaction(self):
        """Test proper interaction with provider object."""
        mock_provider = Mock()
        mock_provider.get_filesystem_config.return_value = {
            "s3_bucket": "test-cur-bucket",
            "region": "us-west-2",
        }

        source = AWSSource(provider=mock_provider)
        sources = source.get_sources(self.start_date, self.end_date)

        # Verify provider method was called
        mock_provider.get_filesystem_config.assert_called_once()

        # Verify provider config is merged
        config = sources[0]["config"]
        assert config["s3_bucket"] == "test-cur-bucket"
        assert config["region"] == "us-west-2"

    def test_detect_export_type_default(self):
        """Test export type detection defaults to FOCUS."""
        export_type = self.source._detect_export_type({})
        assert export_type == "focus"

    def test_detect_export_type_with_provider(self):
        """Test export type detection with provider."""
        mock_provider = Mock()
        mock_provider.export_type = "legacy"

        source = AWSSource(provider=mock_provider)
        export_type = source._detect_export_type({})
        assert export_type == "legacy"

    def test_get_legacy_sources(self):
        """Test getting legacy CUR sources."""
        sources = self.source._get_legacy_cur_sources(
            self.start_date, self.end_date, {}
        )

        assert len(sources) == 1
        source = sources[0]
        assert source["name"] == "cost_and_usage_report"
        assert source["config"]["metadata"]["export_format"] == "cur_legacy"
        assert source["config"]["filters"]["date_column"] == "lineItem/UsageStartDate"

    def test_get_focus_sources(self):
        """Test getting FOCUS export sources."""
        sources = self.source._get_focus_sources(self.start_date, self.end_date, {})

        assert len(sources) == 1
        source = sources[0]
        assert source["name"] == "aws_focus_export"
        assert source["config"]["metadata"]["export_format"] == "focus_1_0"
        assert source["config"]["filters"]["date_column"] == "ChargePeriodStart"
        assert source["config"]["parse_options"]["format"] == "parquet"
