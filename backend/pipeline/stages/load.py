"""
Load Stage - Uses DLT to load transformed billing data
"""

import json
import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import dlt

from pipeline.stages.base import BaseStage, StageResult

logger = logging.getLogger(__name__)


class LoadStage(BaseStage):
    """Load stage that saves transformed billing data to billing_data table using DLT."""

    def __init__(self, config, db):
        super().__init__(config, db)

        # DLT configuration
        self.pipeline_name = config.dlt_pipeline_name
        self.dataset_name = config.dlt_dataset_name
        self.destination = config.dlt_destination

        # Load configuration
        self.batch_size = config.load_config.get("batch_size", 500)
        self.write_disposition = config.load_config.get("write_disposition", "merge")
        self.primary_key = config.load_config.get("primary_key", ["id"])
        self.merge_key = config.load_config.get(
            "merge_key",
            ["x_provider_id", "charge_period_start", "charge_period_end", "sku_id"],
        )

    async def validate_input(self, context: dict[str, Any]) -> None:
        """Validate load stage input."""
        required = ["transformed_records", "failed_records"]
        missing = [field for field in required if field not in context]

        if missing:
            raise ValueError(f"Missing required context fields: {missing}")

        # Validate records format
        if context["transformed_records"]:
            sample = context["transformed_records"][0]
            required_fields = [
                "id",
                "x_provider_id",
                "charge_period_start",
                "charge_period_end",
                "billing_currency",
            ]
            missing_fields = [f for f in required_fields if f not in sample]

            if missing_fields:
                raise ValueError(
                    f"Missing required billing data fields: {missing_fields}"
                )

    async def execute(self, context: dict[str, Any]) -> StageResult:
        """Execute load using DLT."""
        start_time = datetime.now(UTC)
        loaded_count = 0
        failed_count = 0
        errors = []
        success = False

        try:
            transformed_records = context.get("transformed_records", [])
            failed_transform_records = context.get("failed_records", [])
            pipeline_run_id = context.get("pipeline_run_id")

            logger.info(f"Starting load of {len(transformed_records)} records")

            # Handle empty data - this is success, not failure
            if not transformed_records:
                logger.info(
                    "Load stage: No records to load - empty transformation result"
                )
                success = True
                output_data = {
                    "loaded_count": 0,
                    "failed_count": len(failed_transform_records),
                    "load_summary": {
                        "total_attempted": 0,
                        "successfully_loaded": 0,
                        "failed_loads": 0,
                        "transform_failures": len(failed_transform_records),
                    },
                }
                context.update(output_data)

                return StageResult(
                    stage_name="load",
                    success=success,
                    records_processed=0,
                    records_failed=len(failed_transform_records),
                    duration_seconds=(datetime.now(UTC) - start_time).total_seconds(),
                    errors=[],
                    data=output_data,
                )

            # Create DLT pipeline
            pipeline = self._create_pipeline()

            # Create DLT resource with merge configuration
            @dlt.resource(
                name="billing_data",
                write_disposition=self.write_disposition,
                primary_key=self.primary_key,
                merge_key=self.merge_key,
            )
            def billing_data_resource(records):
                yield from records

            # Process in batches
            for i in range(0, len(transformed_records), self.batch_size):
                batch = transformed_records[i : i + self.batch_size]
                batch_num = i // self.batch_size + 1
                total_batches = (
                    len(transformed_records) + self.batch_size - 1
                ) // self.batch_size

                logger.info(
                    f"Loading batch {batch_num}/{total_batches} ({len(batch)} records)"
                )

                try:
                    # Prepare records for DLT
                    prepared_batch = self._prepare_records_for_dlt(batch)

                    # Load using DLT with configured resource
                    load_info = pipeline.run(
                        billing_data_resource(prepared_batch),
                        table_name="billing_data",
                    )

                    # Check for failures
                    batch_failed = 0
                    if (
                        hasattr(load_info, "has_failed_jobs")
                        and load_info.has_failed_jobs
                    ):
                        for job in load_info.jobs:
                            if job.failed:
                                batch_failed += 1
                                logger.error(
                                    f"DLT job failed: {job.job_id} - {job.exception}"
                                )
                                errors.append(
                                    {
                                        "error": str(job.exception),
                                        "job_id": job.job_id,
                                        "batch": batch_num,
                                    }
                                )

                    # Count loaded records
                    batch_loaded = len(batch) - batch_failed
                    loaded_count += batch_loaded

                    logger.info(
                        f"Batch {batch_num} completed: {batch_loaded} loaded, {batch_failed} failed"
                    )

                except Exception as e:
                    logger.error(
                        f"Failed to load batch {batch_num}: {e}", exc_info=True
                    )
                    failed_count += len(batch)
                    errors.append(
                        {
                            "error": str(e),
                            "batch": batch_num,
                            "records_in_batch": len(batch),
                        }
                    )

            # Update raw billing data to mark as processed
            if loaded_count > 0:
                await self._mark_raw_records_as_processed(context, pipeline_run_id)

            # Prepare output
            output_data = {
                "loaded_count": loaded_count,
                "failed_count": failed_count + len(failed_transform_records),
                "load_summary": {
                    "total_attempted": len(transformed_records),
                    "successfully_loaded": loaded_count,
                    "failed_loads": failed_count,
                    "transform_failures": len(failed_transform_records),
                },
            }

            # Update context for next stage
            context.update(output_data)

            # Determine success - any loaded records or no records to load is success
            if len(transformed_records) == 0:
                success = True  # No records to load is success
            else:
                success = failed_count == 0 or (
                    failed_count / len(transformed_records) < 0.1  # Allow 10% failure
                )

            logger.info(
                f"Load stage completed: {loaded_count} loaded, {failed_count} failed"
            )

            return StageResult(
                stage_name="load",
                success=success,
                records_processed=loaded_count,
                records_failed=failed_count + len(failed_transform_records),
                duration_seconds=(datetime.now(UTC) - start_time).total_seconds(),
                errors=errors[:10] if errors else [],  # Limit errors in response
                data=output_data,
            )

        except Exception as e:
            logger.error(f"Load stage failed: {e}", exc_info=True)
            return StageResult(
                stage_name="load",
                success=False,
                records_processed=0,
                records_failed=0,
                duration_seconds=(datetime.now(UTC) - start_time).total_seconds(),
                errors=[{"error": str(e), "type": type(e).__name__}],
                data={},
            )

    def _prepare_records_for_dlt(
        self, records: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Prepare records for DLT by converting data types."""
        prepared = []

        for record in records:
            prepared_record = record.copy()

            # Convert datetime strings to datetime objects
            date_fields = [
                "charge_period_start",
                "charge_period_end",
                "x_created_at",
                "x_updated_at",
            ]

            for field in date_fields:
                if field in prepared_record and prepared_record[field]:
                    if isinstance(prepared_record[field], str):
                        try:
                            prepared_record[field] = datetime.fromisoformat(
                                prepared_record[field].replace("Z", "+00:00")
                            )
                        except ValueError:
                            logger.warning(
                                f"Failed to parse date field {field}: {prepared_record[field]}"
                            )

            # Convert Decimal to float for numeric fields
            numeric_fields = [
                "billed_cost",
                "billing_currency_exchange_rate",
                "contracted_unit_cost",
                "effective_cost",
                "list_unit_cost",
                "pricing_quantity",
                "usage_quantity",
            ]

            for field in numeric_fields:
                if field in prepared_record and prepared_record[field] is not None:
                    if isinstance(prepared_record[field], Decimal):
                        prepared_record[field] = float(prepared_record[field])

            # Ensure JSON fields are properly serialized
            json_fields = ["tags", "x_provider_data"]

            for field in json_fields:
                if field in prepared_record and prepared_record[field] is not None:
                    if not isinstance(prepared_record[field], str):
                        prepared_record[field] = json.dumps(prepared_record[field])

            prepared.append(prepared_record)

        return prepared

    async def _mark_raw_records_as_processed(
        self, context: dict[str, Any], pipeline_run_id: str
    ) -> None:
        """Mark raw billing records as processed using direct database update."""
        try:
            raw_billing_ids = context.get("raw_billing_ids", [])

            if raw_billing_ids:
                # Use SQLAlchemy directly to update records
                from datetime import datetime

                from app.models.raw_billing_data import RawBillingData

                # Update records directly in the database
                updated = (
                    self.db.query(RawBillingData)
                    .filter(RawBillingData.id.in_(raw_billing_ids))
                    .update(
                        {
                            RawBillingData.processed: True,
                            RawBillingData.processed_at: datetime.now(UTC),
                            RawBillingData.updated_at: datetime.now(UTC),
                        },
                        synchronize_session=False,
                    )
                )

                self.db.commit()
                logger.info(f"Marked {updated} raw records as processed")

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to mark raw records as processed: {e}")
            # Don't fail the whole load stage if this fails

    def _create_pipeline(self) -> dlt.Pipeline:
        """Create DLT pipeline instance."""
        return self.config.get_dlt_pipeline(
            pipeline_name=self.pipeline_name, dataset_name=self.dataset_name
        )

    async def rollback(self, context: dict[str, Any]) -> None:
        """Rollback load stage - DLT handles transactions."""
        logger.info("Load stage rollback: DLT manages transaction rollback")

    def get_progress(self, context: dict[str, Any]) -> dict[str, Any]:
        """Get current progress of loading."""
        return {
            "stage": "load",
            "records_total": len(context.get("transformed_records", [])),
            "records_loaded": context.get("loaded_count", 0),
            "records_failed": context.get("failed_count", 0),
        }
