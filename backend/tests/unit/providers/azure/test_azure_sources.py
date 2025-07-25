"""
Unit tests for Azure Data Sources Configuration
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from pipeline.sources.base import BaseSource
from providers.azure.sources import AzureSource


class TestAzureSource:
    """Test suite for AzureSource class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.start_date = datetime(2024, 1, 1)
        self.end_date = datetime(2024, 1, 31)

        # Mock provider
        self.mock_provider = Mock()
        self.mock_provider.get_filesystem_config.return_value = {
            "bucket_url": "az://billing-exports/exports/daily",
            "azure_storage_account_key": "test-storage-key",
            "azure_storage_account_name": "teststorage",
        }

    def test_init_with_provider(self):
        """Test initialization with provider."""
        source = AzureSource(provider=self.mock_provider)
        assert source.provider == self.mock_provider

    def test_init_without_provider(self):
        """Test initialization without provider."""
        source = AzureSource()
        assert source.provider is None

    def test_get_sources_with_provider(self):
        """Test source configuration generation with provider."""
        source = AzureSource(provider=self.mock_provider)

        with patch.object(source, "validate_source_configs") as mock_validate:
            expected_sources = [
                {
                    "name": "azure_focus_export",
                    "source_type": "filesystem",
                    "config": {
                        "bucket_url": "az://billing-exports/exports/daily",
                        "azure_storage_account_key": "test-storage-key",
                        "azure_storage_account_name": "teststorage",
                        "file_pattern": "**/part*.parquet",
                        "parse_options": {
                            "format": "parquet",
                        },
                        "filters": {
                            "date_column": "ChargePeriodStart",
                            "start_date": "2024-01-01T00:00:00",
                            "end_date": "2024-01-31T00:00:00",
                        },
                    },
                }
            ]
            mock_validate.return_value = expected_sources

            sources = source.get_sources(self.start_date, self.end_date)

            assert len(sources) == 1
            assert sources[0]["name"] == "azure_focus_export"
            assert sources[0]["source_type"] == "filesystem"

            # Verify filesystem config from provider is included
            config = sources[0]["config"]
            assert "bucket_url" in config
            assert "azure_storage_account_key" in config
            assert "azure_storage_account_name" in config

            # Verify Azure-specific config
            assert config["file_pattern"] == "**/part*.parquet"
            assert config["parse_options"]["format"] == "parquet"
            assert config["filters"]["date_column"] == "ChargePeriodStart"
            assert config["filters"]["start_date"] == "2024-01-01T00:00:00"
            assert config["filters"]["end_date"] == "2024-01-31T00:00:00"

            mock_validate.assert_called_once()

    def test_get_sources_without_provider(self):
        """Test source configuration generation without provider."""
        source = AzureSource()

        with patch.object(source, "validate_source_configs") as mock_validate:
            expected_sources = [
                {
                    "name": "azure_focus_export",
                    "source_type": "filesystem",
                    "config": {
                        "file_pattern": "**/part*.parquet",
                        "parse_options": {
                            "format": "parquet",
                        },
                        "filters": {
                            "date_column": "ChargePeriodStart",
                            "start_date": "2024-01-01T00:00:00",
                            "end_date": "2024-01-31T00:00:00",
                        },
                    },
                }
            ]
            mock_validate.return_value = expected_sources

            sources = source.get_sources(self.start_date, self.end_date)

            assert len(sources) == 1
            config = sources[0]["config"]

            # Should not have filesystem config from provider
            assert "bucket_url" not in config
            assert "azure_storage_account_key" not in config

            # Should still have Azure-specific config
            assert config["file_pattern"] == "**/part*.parquet"
            assert config["parse_options"]["format"] == "parquet"

    def test_get_sources_provider_no_filesystem_config_method(self):
        """Test source generation when provider has no get_filesystem_config method."""
        mock_provider_no_method = Mock(spec=[])  # Empty spec, no methods
        source = AzureSource(provider=mock_provider_no_method)

        with patch.object(source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []

            source.get_sources(self.start_date, self.end_date)

            # Should not fail, just continue without filesystem config
            called_args = mock_validate.call_args[0][0]
            assert len(called_args) == 1
            config = called_args[0]["config"]
            assert "bucket_url" not in config

    def test_get_sources_date_formatting(self):
        """Test date formatting in source configuration."""
        source = AzureSource()

        # Use different dates to verify formatting
        start = datetime(2024, 6, 15, 10, 30, 45)
        end = datetime(2024, 6, 20, 14, 45, 30)

        with patch.object(source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []
            source.get_sources(start, end)

            called_args = mock_validate.call_args[0][0]
            filters = called_args[0]["config"]["filters"]

            assert filters["start_date"] == "2024-06-15T10:30:45"
            assert filters["end_date"] == "2024-06-20T14:45:30"

    def test_get_sources_file_pattern(self):
        """Test file pattern configuration for Azure parquet files."""
        source = AzureSource()

        with patch.object(source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []
            source.get_sources(self.start_date, self.end_date)

            called_args = mock_validate.call_args[0][0]
            config = called_args[0]["config"]

            assert config["file_pattern"] == "**/part*.parquet"

    def test_get_sources_parse_options(self):
        """Test parse options configuration."""
        source = AzureSource()

        with patch.object(source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []
            source.get_sources(self.start_date, self.end_date)

            called_args = mock_validate.call_args[0][0]
            parse_options = called_args[0]["config"]["parse_options"]

            assert parse_options["format"] == "parquet"

    def test_get_sources_focus_date_column(self):
        """Test FOCUS standard date column usage."""
        source = AzureSource()

        with patch.object(source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []
            source.get_sources(self.start_date, self.end_date)

            called_args = mock_validate.call_args[0][0]
            filters = called_args[0]["config"]["filters"]

            assert filters["date_column"] == "ChargePeriodStart"

    def test_get_sources_filesystem_config_merge(self):
        """Test that filesystem config is properly merged with source config."""
        # Provider with more complex filesystem config
        self.mock_provider.get_filesystem_config.return_value = {
            "bucket_url": "az://billing-exports/custom/path",
            "azure_storage_account_key": "complex-key",
            "azure_storage_account_name": "complexstorage",
            "custom_setting": "custom_value",
        }

        source = AzureSource(provider=self.mock_provider)

        with patch.object(source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []
            source.get_sources(self.start_date, self.end_date)

            called_args = mock_validate.call_args[0][0]
            config = called_args[0]["config"]

            # All filesystem config should be included
            assert config["bucket_url"] == "az://billing-exports/custom/path"
            assert config["azure_storage_account_key"] == "complex-key"
            assert config["azure_storage_account_name"] == "complexstorage"
            assert config["custom_setting"] == "custom_value"

            # Azure-specific config should still be present
            assert config["file_pattern"] == "**/part*.parquet"
            assert config["filters"]["date_column"] == "ChargePeriodStart"

    def test_get_sources_inherits_from_base_source(self):
        """Test that AzureSource inherits from BaseSource."""
        source = AzureSource()
        assert isinstance(source, BaseSource)

    def test_get_sources_calls_validate_source_configs(self):
        """Test that get_sources calls validate_source_configs."""
        source = AzureSource()

        with patch.object(source, "validate_source_configs") as mock_validate:
            expected_return = [{"validated": True}]
            mock_validate.return_value = expected_return

            result = source.get_sources(self.start_date, self.end_date)

            assert result == expected_return
            mock_validate.assert_called_once()

            # Verify the structure passed to validation
            called_args = mock_validate.call_args[0][0]
            assert len(called_args) == 1
            assert called_args[0]["name"] == "azure_focus_export"
            assert called_args[0]["source_type"] == "filesystem"

    def test_source_name_and_type(self):
        """Test source name and type configuration."""
        source = AzureSource()

        with patch.object(source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []
            source.get_sources(self.start_date, self.end_date)

            called_args = mock_validate.call_args[0][0]
            source_config = called_args[0]

            assert source_config["name"] == "azure_focus_export"
            assert source_config["source_type"] == "filesystem"

    @pytest.mark.parametrize(
        "start_date,end_date,expected_start,expected_end",
        [
            (
                datetime(2024, 1, 1, 0, 0, 0),
                datetime(2024, 1, 31, 23, 59, 59),
                "2024-01-01T00:00:00",
                "2024-01-31T23:59:59",
            ),
            (
                datetime(2023, 12, 25, 12, 30, 45),
                datetime(2024, 1, 5, 18, 15, 30),
                "2023-12-25T12:30:45",
                "2024-01-05T18:15:30",
            ),
            (
                datetime(2024, 6, 1),
                datetime(2024, 6, 30),
                "2024-06-01T00:00:00",
                "2024-06-30T00:00:00",
            ),
        ],
    )
    def test_date_range_formatting(
        self, start_date, end_date, expected_start, expected_end
    ):
        """Test various date range formatting scenarios."""
        source = AzureSource()

        with patch.object(source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []
            source.get_sources(start_date, end_date)

            called_args = mock_validate.call_args[0][0]
            filters = called_args[0]["config"]["filters"]

            assert filters["start_date"] == expected_start
            assert filters["end_date"] == expected_end
