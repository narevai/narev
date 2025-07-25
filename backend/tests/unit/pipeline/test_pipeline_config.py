from unittest.mock import patch

import pytest

from pipeline.config import PipelineConfig


class TestPipelineConfig:
    """Test PipelineConfig class."""

    def test_default_configuration(self):
        """Test default configuration values."""
        config = PipelineConfig()

        assert config.name == "billing_pipeline"
        assert config.version == "1.0.0"
        assert config.dlt_pipeline_name == "billing_etl"
        assert config.dlt_dataset_name == "main"
        assert config.dlt_destination == "sqlite"

        assert config.extract_config["batch_size"] == 1000
        assert config.extract_config["max_retries"] == 3
        assert config.extract_config["save_raw_responses"] is True

        assert config.transform_config["batch_size"] == 100
        assert config.transform_config["validate_focus"] is True

        assert config.load_config["batch_size"] == 500
        assert config.load_config["write_disposition"] == "merge"

        assert config.parallel_stages is False
        assert config.max_workers == 4
        assert config.fail_fast is False
        assert config.max_errors_percentage == 5.0

    def test_custom_configuration(self):
        """Test custom configuration values."""
        custom_extract_config = {"batch_size": 500, "max_retries": 5}
        custom_transform_config = {"batch_size": 200}

        config = PipelineConfig(
            name="custom_pipeline",
            version="2.0.0",
            extract_config=custom_extract_config,
            transform_config=custom_transform_config,
            parallel_stages=True,
            max_workers=8,
            fail_fast=True,
        )

        assert config.name == "custom_pipeline"
        assert config.version == "2.0.0"
        assert config.extract_config["batch_size"] == 500
        assert config.extract_config["max_retries"] == 5
        assert config.transform_config["batch_size"] == 200
        assert config.parallel_stages is True
        assert config.max_workers == 8
        assert config.fail_fast is True

    def test_get_stage_config(self):
        """Test getting stage-specific configuration."""
        config = PipelineConfig()

        extract_config = config.get_stage_config("extract")
        transform_config = config.get_stage_config("transform")
        load_config = config.get_stage_config("load")
        unknown_config = config.get_stage_config("unknown")

        assert extract_config == config.extract_config
        assert transform_config == config.transform_config
        assert load_config == config.load_config
        assert unknown_config == {}

    def test_get_dlt_destination_sqlite(self):
        """Test getting SQLite DLT destination."""
        config = PipelineConfig(dlt_destination="sqlite")

        with (
            patch("dlt.destinations.sqlalchemy") as mock_sqlalchemy,
            patch("app.config.settings") as mock_settings,
        ):
            mock_settings.sqlite_path = "/test/path/db.sqlite"
            mock_destination = "mocked_sqlite_destination"
            mock_sqlalchemy.return_value = mock_destination

            result = config.get_dlt_destination()

            assert result == mock_destination

    def test_get_dlt_destination_postgres(self):
        """Test getting PostgreSQL DLT destination."""
        config = PipelineConfig(dlt_destination="postgres")

        with (
            patch("dlt.destinations.postgres") as mock_postgres,
            patch("app.config.settings") as mock_settings,
        ):
            mock_settings.postgres_host = "localhost"
            mock_settings.postgres_port = 5432
            mock_settings.postgres_user = "testuser"
            mock_settings.postgres_password = "testpass"
            mock_settings.postgres_db = "testdb"

            mock_destination = "mocked_postgres_destination"
            mock_postgres.return_value = mock_destination

            result = config.get_dlt_destination()

            assert result == mock_destination

    def test_get_dlt_destination_unsupported(self):
        """Test getting unsupported DLT destination."""
        config = PipelineConfig(dlt_destination="unsupported")

        with pytest.raises(ValueError, match="Unsupported DLT destination"):
            config.get_dlt_destination()

    def test_get_dlt_pipeline_default(self):
        """Test getting DLT pipeline with default parameters."""
        config = PipelineConfig()

        with (
            patch("dlt.pipeline") as mock_pipeline_func,
            patch(
                "pipeline.config.PipelineConfig.get_dlt_destination"
            ) as mock_destination,
        ):
            mock_pipeline = "mocked_pipeline"
            mock_pipeline_func.return_value = mock_pipeline
            mock_dest = "mocked_destination"
            mock_destination.return_value = mock_dest

            result = config.get_dlt_pipeline()

            assert result == mock_pipeline
            mock_pipeline_func.assert_called_once_with(
                pipeline_name="billing_etl",
                destination=mock_dest,
                dataset_name="main",
                dev_mode=False,
            )

    def test_get_dlt_pipeline_custom(self):
        """Test getting DLT pipeline with custom parameters."""
        config = PipelineConfig()

        with (
            patch("dlt.pipeline") as mock_pipeline_func,
            patch(
                "pipeline.config.PipelineConfig.get_dlt_destination"
            ) as mock_destination,
        ):
            mock_pipeline = "mocked_custom_pipeline"
            mock_pipeline_func.return_value = mock_pipeline
            mock_dest = "mocked_destination"
            mock_destination.return_value = mock_dest

            result = config.get_dlt_pipeline(
                pipeline_name="custom_pipeline", dataset_name="custom_dataset"
            )

            assert result == mock_pipeline
            mock_pipeline_func.assert_called_once_with(
                pipeline_name="custom_pipeline",
                destination=mock_dest,
                dataset_name="custom_dataset",
                dev_mode=False,
            )

    def test_to_dict(self):
        """Test converting configuration to dictionary."""
        config = PipelineConfig(
            name="test_pipeline", version="1.5.0", parallel_stages=True, max_workers=6
        )

        result = config.to_dict()

        assert result["name"] == "test_pipeline"
        assert result["version"] == "1.5.0"

        assert result["dlt"]["pipeline_name"] == "billing_etl"
        assert result["dlt"]["dataset_name"] == "main"
        assert result["dlt"]["destination"] == "sqlite"

        assert result["stages"]["extract"]["batch_size"] == 1000
        assert result["stages"]["transform"]["batch_size"] == 100
        assert result["stages"]["load"]["batch_size"] == 500

        assert result["performance"]["parallel_stages"] is True
        assert result["performance"]["max_workers"] == 6
        assert result["performance"]["memory_limit_mb"] == 1024

        assert result["error_handling"]["fail_fast"] is False
        assert result["error_handling"]["max_errors_percentage"] == 5.0
        assert result["error_handling"]["save_failed_records"] is True

    def test_load_config_defaults(self):
        """Test load configuration defaults."""
        config = PipelineConfig()

        assert config.load_config["write_disposition"] == "merge"
        assert config.load_config["primary_key"] == ["id"]
        assert set(config.load_config["merge_key"]) == {
            "x_provider_id",
            "charge_period_start",
            "charge_period_end",
            "sku_id",
        }
        assert config.load_config["column_hints"]["tags"]["data_type"] == "json"
        assert (
            config.load_config["column_hints"]["x_provider_data"]["data_type"] == "json"
        )

    def test_extract_config_defaults(self):
        """Test extract configuration defaults."""
        config = PipelineConfig()

        assert config.extract_config["timeout"] == 30.0
        assert config.extract_config["retry_delay"] == 1.0
        assert config.extract_config["save_raw_responses"] is True

    def test_transform_config_defaults(self):
        """Test transform configuration defaults."""
        config = PipelineConfig()

        assert config.transform_config["validate_focus"] is True
        assert config.transform_config["strict_validation"] is False
        assert config.transform_config["save_validation_errors"] is True

    def test_performance_settings(self):
        """Test performance-related settings."""
        config = PipelineConfig(
            memory_limit_mb=2048, max_workers=12, parallel_stages=True
        )

        assert config.memory_limit_mb == 2048
        assert config.max_workers == 12
        assert config.parallel_stages is True

    def test_error_handling_settings(self):
        """Test error handling settings."""
        config = PipelineConfig(
            fail_fast=True, max_errors_percentage=2.5, save_failed_records=False
        )

        assert config.fail_fast is True
        assert config.max_errors_percentage == 2.5
        assert config.save_failed_records is False
