"""
Transform Stage - Maps provider data to FOCUS format
"""

import logging
from datetime import UTC, datetime
from typing import Any

from focus.models import FocusRecord
from focus.validators import FocusValidator
from pipeline.stages.base import BaseStage, StageResult

logger = logging.getLogger(__name__)


class TransformStage(BaseStage):
    """Transform stage that maps provider data to FOCUS 1.2 format."""

    def __init__(self, config, db):
        super().__init__(config, db)
        self.validator = FocusValidator(
            strict_mode=self.stage_config.get("strict_validation", False)
        )

    def _utcnow(self) -> datetime:
        """Get current UTC time with timezone info."""
        return datetime.now(UTC)

    async def validate_input(self, context: dict[str, Any]) -> None:
        """Validate transform stage input."""
        required = ["mapper", "raw_records", "provider_type"]
        missing = [field for field in required if field not in context]

        if missing:
            raise ValueError(f"Missing required context fields: {missing}")

        # Validate mapper has required method
        mapper = context["mapper"]
        if not hasattr(mapper, "map_to_focus"):
            raise ValueError("Mapper missing required method: map_to_focus")

        # Validate we have records to transform
        if not context["raw_records"]:
            logger.warning("No raw records to transform")

    async def execute(self, context: dict[str, Any]) -> StageResult:
        """Execute transformation to FOCUS format."""
        start_time = self._utcnow()
        focus_records = []
        failed_records = []
        validation_errors = []
        skipped_records = 0
        all_records = []
        success = False

        try:
            raw_records = context["raw_records"]
            mapper = context["mapper"]
            provider_type = context["provider_type"]
            batch_size = self.stage_config.get("batch_size", 100)

            # Handle empty input - this is success, not failure
            if not raw_records:
                logger.info(
                    "Transform stage: No records to transform - empty source data"
                )
                success = True
                output_data = {
                    "focus_records": [],
                    "transformed_records": [],
                    "transform_summary": {
                        "provider_type": provider_type,
                        "total_raw_records": 0,
                        "total_records": 0,
                        "transformed": 0,
                        "failed": 0,
                        "skipped": 0,
                        "validation_errors": 0,
                    },
                }
                context.update(output_data)

                return StageResult(
                    stage_name="transform",
                    success=success,
                    records_processed=0,
                    records_failed=0,
                    duration_seconds=(self._utcnow() - start_time).total_seconds(),
                    errors=[],
                    data=output_data,
                )

            logger.info(f"Starting transformation of {len(raw_records)} raw records")

            # Process records from raw_billing_data
            for raw_billing_record in raw_records:
                # Extract the actual records from the raw_billing_data structure
                # Data might be in 'extracted_data' field as JSON string
                if "extracted_data" in raw_billing_record:
                    records = raw_billing_record.get("extracted_data", [])

                    if isinstance(records, str):
                        # Data is JSON string
                        import json

                        try:
                            records = json.loads(records)
                        except json.JSONDecodeError:
                            logger.error("Failed to parse JSON data from raw record")
                            records = []

                # Backward compatibility - check 'data' field
                elif "data" in raw_billing_record:
                    records = raw_billing_record.get("data", [])

                    if isinstance(records, str):
                        # Data is JSON string
                        import json

                        try:
                            records = json.loads(records)
                        except json.JSONDecodeError:
                            logger.error("Failed to parse JSON data from raw record")
                            records = []

                # Old format compatibility - check 'records' field
                elif "records" in raw_billing_record:
                    records = raw_billing_record.get("records", [])
                else:
                    # Maybe the record itself is the data
                    records = [raw_billing_record]

                # Flatten all records for processing
                if isinstance(records, list):
                    all_records.extend(records)
                else:
                    all_records.append(records)

            logger.info(f"Extracted {len(all_records)} records to transform")

            # Process in batches
            for i in range(0, len(all_records), batch_size):
                batch = all_records[i : i + batch_size]
                batch_results = self._transform_batch(batch, mapper)

                focus_records.extend(batch_results["transformed"])
                failed_records.extend(batch_results["failed"])
                validation_errors.extend(batch_results["validation_errors"])
                skipped_records += batch_results["skipped"]

            # Convert FocusRecord objects to dicts for Load stage
            transformed_dicts = []
            for record in focus_records:
                record_dict = record.model_dump(mode="json", exclude_none=True)
                # Ensure we have an ID
                if "id" not in record_dict or not record_dict["id"]:
                    import uuid

                    record_dict["id"] = str(uuid.uuid4())
                transformed_dicts.append(record_dict)

            # Prepare output
            output_data = {
                "focus_records": focus_records,  # Keep original FocusRecord objects
                "transformed_records": transformed_dicts,  # Add dict version for Load stage
                "transform_summary": {
                    "provider_type": provider_type,
                    "total_raw_records": len(raw_records),
                    "total_records": len(all_records),
                    "transformed": len(focus_records),
                    "failed": len(failed_records),
                    "skipped": skipped_records,
                    "validation_errors": len(validation_errors),
                },
            }

            # Update context for next stage
            context.update(output_data)

            # Determine success - no errors occurred is success
            if len(raw_records) == 0:
                # No records to transform - this is success
                success = True
                logger.info("Transform stage: No raw records to process")
            elif len(all_records) == 0:
                # No records extracted - this is also success (empty source)
                success = True
                logger.info(
                    "Transform stage: No records found in raw data - empty source"
                )
            elif len(focus_records) > 0 or (
                skipped_records > 0 and len(failed_records) == 0
            ):
                # We have some data or all were properly skipped
                success = True
            else:
                # Only fail if we had records but couldn't process any of them
                success = len(failed_records) < len(all_records)  # Some succeeded

            # Log results
            if len(failed_records) > 0:
                logger.warning(
                    f"Transform stage: {len(failed_records)} records failed out of {len(all_records)} records"
                )
                # Show first 3 errors for debugging
                for error in failed_records[:3]:
                    logger.warning(f"Failed record: {error}")

            if skipped_records > 0:
                logger.info(
                    f"Transform stage: {skipped_records} empty records properly skipped"
                )

            logger.info(
                f"Transform stage completed: {len(focus_records)} transformed, {len(failed_records)} failed, {skipped_records} skipped"
            )

            end_time = self._utcnow()
            duration = (end_time - start_time).total_seconds()

            return StageResult(
                stage_name="transform",
                success=success,
                records_processed=len(all_records),
                records_failed=len(failed_records),
                duration_seconds=duration,
                errors=validation_errors[:10] if validation_errors else [],
                data=output_data,
            )

        except Exception as e:
            logger.error(f"Transform stage failed: {e}", exc_info=True)
            end_time = self._utcnow()
            duration = (end_time - start_time).total_seconds()

            return StageResult(
                stage_name="transform",
                success=False,
                records_processed=0,
                records_failed=0,
                duration_seconds=duration,
                errors=[{"error": str(e), "type": type(e).__name__}],
                data={},
            )

    def _transform_batch(
        self, batch: list[dict[str, Any]], mapper: Any
    ) -> dict[str, list]:
        """Transform a batch of records with enhanced FOCUS validation."""
        transformed = []
        failed = []
        validation_errors = []
        skipped = 0

        for record in batch:
            try:
                # Map to FOCUS format using mapper
                focus_items = mapper.map_to_focus(record)

                if focus_items is None:
                    skipped += 1
                    logger.debug(f"Mapper skipped record: {record}")
                    continue

                if not focus_items:
                    skipped += 1
                    continue

                # Process each FOCUS record
                for focus_record in focus_items:
                    if not isinstance(focus_record, FocusRecord):
                        logger.error(
                            f"Mapper returned non-FocusRecord object: {type(focus_record)}"
                        )
                        failed.append(
                            {
                                "record": record,
                                "error": f"Invalid mapper output type: {type(focus_record)}",
                                "error_type": "InvalidMapperOutput",
                            }
                        )
                        continue

                    # Enhanced FOCUS validation
                    focus_errors = self._validate_focus_record(focus_record)
                    if focus_errors:
                        if self.stage_config.get("strict_validation", False):
                            failed.append(
                                {
                                    "record": record,
                                    "error": f"FOCUS validation failed: {focus_errors}",
                                    "error_type": "ValidationError",
                                    "validation_errors": focus_errors,
                                }
                            )
                            validation_errors.extend(
                                [
                                    {"field": "multiple", "message": err}
                                    for err in focus_errors
                                ]
                            )
                            continue
                        else:
                            # Log warnings but continue
                            for error in focus_errors:
                                logger.warning(f"FOCUS validation warning: {error}")
                            validation_errors.extend(
                                [
                                    {"field": "multiple", "message": err}
                                    for err in focus_errors
                                ]
                            )

                    # Standard FOCUS validator (if enabled)
                    if self.stage_config.get("validate_focus", True):
                        validation_result = self.validator.validate_record(focus_record)

                        if not validation_result.is_valid:
                            if self.stage_config.get("strict_validation", False):
                                failed.append(
                                    {
                                        "record": record,
                                        "error": f"FOCUS validation failed: {validation_result.errors}",
                                        "error_type": "ValidationError",
                                        "validation_errors": validation_result.errors,
                                    }
                                )
                                validation_errors.extend(validation_result.errors)
                                continue
                            else:
                                for error in validation_result.errors:
                                    logger.warning(
                                        f"FOCUS validation error: {error.field} - {error.message}"
                                    )
                                validation_errors.extend(validation_result.errors)

                    # Add successfully transformed record
                    transformed.append(focus_record)

            except Exception as e:
                logger.error(f"Error transforming record: {e}")
                logger.debug(f"Failed record: {record}")
                failed.append(
                    {"record": record, "error": str(e), "error_type": type(e).__name__}
                )

        return {
            "transformed": transformed,
            "failed": failed,
            "validation_errors": validation_errors,
            "skipped": skipped,
        }

    def _validate_focus_record(self, focus_record: FocusRecord) -> list[str]:
        """
        Validate FOCUS record compliance beyond standard validation.

        Returns:
            List of validation errors
        """
        errors = []

        # Check mandatory fields are not None/empty
        mandatory_checks = [
            ("billed_cost", focus_record.billed_cost),
            ("effective_cost", focus_record.effective_cost),
            ("list_cost", focus_record.list_cost),
            ("contracted_cost", focus_record.contracted_cost),
            ("billing_account_id", focus_record.billing_account_id),
            ("billing_account_name", focus_record.billing_account_name),
            ("billing_account_type", focus_record.billing_account_type),
            ("billing_period_start", focus_record.billing_period_start),
            ("billing_period_end", focus_record.billing_period_end),
            ("charge_period_start", focus_record.charge_period_start),
            ("charge_period_end", focus_record.charge_period_end),
            ("billing_currency", focus_record.billing_currency),
            ("service_name", focus_record.service_name),
            ("service_category", focus_record.service_category),
            ("provider_name", focus_record.provider_name),
            ("publisher_name", focus_record.publisher_name),
            ("invoice_issuer_name", focus_record.invoice_issuer_name),
            ("charge_category", focus_record.charge_category),
            ("charge_description", focus_record.charge_description),
        ]

        for field_name, value in mandatory_checks:
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append(f"Mandatory field '{field_name}' is missing or empty")

        # Validate enums using FocusSpec
        from focus.spec import FocusSpec

        if focus_record.service_category and not FocusSpec.is_valid_service_category(
            focus_record.service_category
        ):
            errors.append(f"Invalid service_category: {focus_record.service_category}")

        if focus_record.charge_category and not FocusSpec.is_valid_charge_category(
            focus_record.charge_category
        ):
            errors.append(f"Invalid charge_category: {focus_record.charge_category}")

        if focus_record.charge_class and not FocusSpec.is_valid_charge_class(
            focus_record.charge_class
        ):
            errors.append(f"Invalid charge_class: {focus_record.charge_class}")

        if (
            focus_record.commitment_discount_status
            and not FocusSpec.is_valid_commitment_discount_status(
                focus_record.commitment_discount_status
            )
        ):
            errors.append(
                f"Invalid commitment_discount_status: {focus_record.commitment_discount_status}"
            )

        if focus_record.charge_frequency and not FocusSpec.is_valid_charge_frequency(
            focus_record.charge_frequency
        ):
            errors.append(f"Invalid charge_frequency: {focus_record.charge_frequency}")

        # Validate date consistency
        if focus_record.billing_period_start and focus_record.billing_period_end:
            if focus_record.billing_period_end <= focus_record.billing_period_start:
                errors.append("billing_period_end must be after billing_period_start")

        if focus_record.charge_period_start and focus_record.charge_period_end:
            if focus_record.charge_period_end <= focus_record.charge_period_start:
                errors.append("charge_period_end must be after charge_period_start")

        # Validate cost values are non-negative
        cost_fields = [
            ("billed_cost", focus_record.billed_cost),
            ("effective_cost", focus_record.effective_cost),
            ("list_cost", focus_record.list_cost),
            ("contracted_cost", focus_record.contracted_cost),
        ]

        for field_name, value in cost_fields:
            if value is not None and value < 0:
                errors.append(f"Cost field '{field_name}' cannot be negative: {value}")

        # Validate quantity fields are non-negative
        quantity_fields = [
            ("pricing_quantity", focus_record.pricing_quantity),
            ("consumed_quantity", focus_record.consumed_quantity),
            ("commitment_discount_quantity", focus_record.commitment_discount_quantity),
        ]

        for field_name, value in quantity_fields:
            if value is not None and value < 0:
                errors.append(
                    f"Quantity field '{field_name}' cannot be negative: {value}"
                )

        return errors

    async def rollback(self, context: dict[str, Any]) -> None:
        """Rollback transform stage (no persistent changes to rollback)."""
        logger.info("Transform stage rollback: No persistent changes to rollback")

    def get_progress(self, context: dict[str, Any]) -> dict[str, Any]:
        """Get current progress of transformation."""
        focus_records = context.get("focus_records", [])
        raw_records = context.get("raw_records", [])

        return {
            "stage": "transform",
            "records_total": len(raw_records),
            "records_transformed": len(focus_records),
            "records_failed": context.get("transform_summary", {}).get("failed", 0),
            "validation_errors": context.get("transform_summary", {}).get(
                "validation_errors", 0
            ),
        }
