"""
Pipeline Configuration
"""

from typing import Any

import dlt
from pydantic import BaseModel, Field

from app.config import settings


class PipelineConfig(BaseModel):
    """Pipeline configuration settings."""

    # Pipeline metadata
    name: str = "billing_pipeline"
    version: str = "1.0.0"

    # DLT configuration
    dlt_pipeline_name: str = "billing_etl"
    dlt_dataset_name: str = "main"  # IMPORTANT: 'main' = no separate file for SQLite!
    dlt_destination: str = Field("sqlite", env="DATABASE_TYPE")

    # Stage configurations
    extract_config: dict[str, Any] = {
        "batch_size": 1000,
        "max_retries": 3,
        "retry_delay": 1.0,
        "timeout": 30.0,
        "save_raw_responses": True,
    }

    transform_config: dict[str, Any] = {
        "batch_size": 100,
        "validate_focus": True,
        "strict_validation": False,
        "save_validation_errors": True,
    }

    load_config: dict[str, Any] = {
        "batch_size": 500,
        "write_disposition": "merge",
        "primary_key": ["id"],
        "merge_key": [
            "x_provider_id",
            "charge_period_start",
            "charge_period_end",
            "sku_id",
        ],
        "column_hints": {
            "tags": {"data_type": "json"},
            "x_provider_data": {"data_type": "json"},
        },
    }

    # Performance settings
    parallel_stages: bool = False
    max_workers: int = 4
    memory_limit_mb: int = 1024

    # Error handling
    fail_fast: bool = False
    max_errors_percentage: float = 5.0
    save_failed_records: bool = True

    class Config:
        env_file = ".env"
        env_prefix = "PIPELINE_"

    def get_dlt_pipeline(
        self, pipeline_name: str | None = None, dataset_name: str | None = None
    ) -> dlt.Pipeline:
        """
        Get configured DLT pipeline instance.

        Args:
            pipeline_name: Optional custom pipeline name
            dataset_name: Optional custom dataset name

        Returns:
            Configured DLT pipeline
        """
        return dlt.pipeline(
            pipeline_name=pipeline_name or self.dlt_pipeline_name,
            destination=self.get_dlt_destination(),
            dataset_name=dataset_name or self.dlt_dataset_name,
            dev_mode=False,
        )

    def get_dlt_destination(self) -> Any:
        """
        Get DLT destination based on configuration.

        Returns:
            DLT destination object (postgres or sqlite)
        """
        if self.dlt_destination == "postgres":
            return dlt.destinations.postgres(
                host=settings.postgres_host,
                port=settings.postgres_port,
                user=settings.postgres_user,
                password=settings.postgres_password,
                database=settings.postgres_db,
            )
        elif self.dlt_destination == "sqlite":
            return dlt.destinations.sqlalchemy(
                f"sqlite:///{settings.sqlite_path}",
            )
        else:
            raise ValueError(f"Unsupported DLT destination: {self.dlt_destination}")

    def get_stage_config(self, stage_name: str) -> dict[str, Any]:
        """
        Get configuration for a specific stage.

        Args:
            stage_name: Name of the stage (extract, transform, load)

        Returns:
            Stage configuration dictionary
        """
        config_map = {
            "extract": self.extract_config,
            "transform": self.transform_config,
            "load": self.load_config,
        }
        return config_map.get(stage_name, {})

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "dlt": {
                "pipeline_name": self.dlt_pipeline_name,
                "dataset_name": self.dlt_dataset_name,
                "destination": self.dlt_destination,
            },
            "stages": {
                "extract": self.extract_config,
                "transform": self.transform_config,
                "load": self.load_config,
            },
            "performance": {
                "parallel_stages": self.parallel_stages,
                "max_workers": self.max_workers,
                "memory_limit_mb": self.memory_limit_mb,
            },
            "error_handling": {
                "fail_fast": self.fail_fast,
                "max_errors_percentage": self.max_errors_percentage,
                "save_failed_records": self.save_failed_records,
            },
        }
