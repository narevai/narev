"""
Base Stage Class
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from pipeline.config import PipelineConfig

logger = logging.getLogger(__name__)


@dataclass
class StageResult:
    """Result of a stage execution."""

    stage_name: str
    success: bool
    records_processed: int
    records_failed: int
    duration_seconds: float
    errors: list[dict[str, Any]]
    data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stage_name": self.stage_name,
            "success": self.success,
            "records_processed": self.records_processed,
            "records_failed": self.records_failed,
            "duration_seconds": self.duration_seconds,
            "errors": self.errors[:10]
            if self.errors
            else [],  # Limit errors in response
            "data_summary": {
                key: len(value) if isinstance(value, list) else str(value)
                for key, value in self.data.items()
                if key != "records"  # Don't include actual records in summary
            },
        }


class BaseStage(ABC):
    """Abstract base class for pipeline stages."""

    def __init__(self, config: PipelineConfig, db: Session):
        """
        Initialize stage.

        Args:
            config: Pipeline configuration
            db: Database session
        """
        self.config = config
        self.db = db
        self.stage_name = self.__class__.__name__.replace("Stage", "").lower()
        self.stage_config = config.get_stage_config(self.stage_name)
        self.errors: list[dict[str, Any]] = []

    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> StageResult:
        """
        Execute the stage.

        Args:
            context: Execution context containing provider, mapper, etc.

        Returns:
            StageResult with execution details
        """
        pass

    @abstractmethod
    async def validate_input(self, context: dict[str, Any]) -> None:
        """
        Validate input for the stage.

        Args:
            context: Execution context

        Raises:
            ValueError: If input is invalid
        """
        pass

    async def run(self, context: dict[str, Any]) -> StageResult:
        """
        Run the stage with error handling.

        Args:
            context: Execution context

        Returns:
            StageResult
        """
        start_time = datetime.now()
        records_processed = 0
        records_failed = 0
        data = {}

        try:
            # Validate input
            await self.validate_input(context)

            # Execute stage
            logger.info(f"Executing {self.stage_name} stage")
            result = await self.execute(context)

            # Log completion
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"{self.stage_name} stage completed: "
                f"{result.records_processed} processed, "
                f"{result.records_failed} failed, "
                f"{duration:.2f}s"
            )

            return result

        except Exception as e:
            # Log error
            logger.error(f"{self.stage_name} stage failed: {str(e)}", exc_info=True)

            # Create error result
            duration = (datetime.now() - start_time).total_seconds()
            return StageResult(
                stage_name=self.stage_name,
                success=False,
                records_processed=records_processed,
                records_failed=records_failed,
                duration_seconds=duration,
                errors=[
                    {
                        "error": str(e),
                        "type": type(e).__name__,
                        "stage": self.stage_name,
                    }
                ],
                data=data,
            )

    def add_error(self, error: dict[str, Any]) -> None:
        """Add an error to the error list."""
        self.errors.append(
            {**error, "stage": self.stage_name, "timestamp": datetime.now().isoformat()}
        )

    def should_fail_fast(self) -> bool:
        """Check if stage should fail fast based on error count."""
        if not self.config.fail_fast:
            return False

        if not self.errors:
            return False

        # Check error percentage
        total_records = getattr(self, "_total_records", 0)
        if total_records > 0:
            error_percentage = (len(self.errors) / total_records) * 100
            return error_percentage > self.config.max_errors_percentage

        return False

    def get_batch_size(self) -> int:
        """Get batch size for this stage."""
        return self.stage_config.get("batch_size", 100)

    def get_max_retries(self) -> int:
        """Get max retries for this stage."""
        return self.stage_config.get("max_retries", 3)

    def get_retry_delay(self) -> float:
        """Get retry delay in seconds."""
        return self.stage_config.get("retry_delay", 1.0)

    async def process_batch(
        self, batch: list[Any], process_func: Any, context: dict[str, Any]
    ) -> tuple[list[Any], list[dict[str, Any]]]:
        """
        Process a batch of records.

        Args:
            batch: Batch of records to process
            process_func: Function to process each record
            context: Processing context

        Returns:
            Tuple of (successful_records, errors)
        """
        successful = []
        errors = []

        for record in batch:
            try:
                result = await process_func(record, context)
                if result:
                    successful.append(result)
            except Exception as e:
                errors.append(
                    {
                        "record": str(record)[:500],  # Truncate for storage
                        "error": str(e),
                        "type": type(e).__name__,
                    }
                )

                # Check if should fail fast
                if self.should_fail_fast():
                    raise RuntimeError(
                        f"Too many errors in {self.stage_name} stage"
                    ) from e

        return successful, errors

    def create_batches(self, items: list[Any]) -> list[list[Any]]:
        """Create batches from a list of items."""
        batch_size = self.get_batch_size()
        return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]
