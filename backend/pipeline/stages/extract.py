"""
Extract Stage
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import dlt

from pipeline.stages.base import BaseStage, StageResult
from pipeline.stages.extractors.factory import ExtractorFactory

logger = logging.getLogger(__name__)


class ExtractStage(BaseStage):
    """Extract stage that coordinates data extraction from various sources."""

    def __init__(self, config, db):
        super().__init__(config, db)

        # DLT configuration
        self.pipeline_name = config.dlt_pipeline_name
        self.dataset_name = config.dlt_dataset_name
        self.destination = config.dlt_destination

    async def validate_input(self, context: dict[str, Any]) -> None:
        """Validate extract stage input."""
        required = [
            "provider",
            "start_date",
            "end_date",
            "provider_config",
            "pipeline_run_id",
        ]
        missing = [field for field in required if field not in context]

        if missing:
            raise ValueError(f"Missing required context fields: {missing}")

        # Check if provider can provide sources
        if "sources" not in context:
            provider = context["provider"]
            if not hasattr(provider, "get_sources"):
                raise ValueError("Provider missing required method: get_sources")

    async def execute(self, context: dict[str, Any]) -> StageResult:
        """Execute extraction using appropriate extractors."""
        start_time = datetime.now(UTC)
        errors = []
        all_extracted_records = []
        all_raw_billing_ids = []

        try:
            # Extract required fields from context
            (
                provider_id,
                provider,
                start_date,
                end_date,
                provider_config,
                pipeline_run_id,
            ) = self._extract_context_fields(context)

            logger.info(f"Starting extraction for provider {provider_config['name']}")
            logger.info(f"Period: {start_date} to {end_date}")

            # Get sources
            sources = self._get_sources(context, provider, start_date, end_date)

            if not sources:
                # No sources available - this is not an error, just empty data
                logger.info("No sources available for extraction - empty data period")
                return self._prepare_stage_result(
                    all_extracted_records=[],
                    all_raw_billing_ids=[],
                    sources=[],
                    errors=[],
                    start_time=start_time,
                    context=context,
                )

            logger.info(f"Found {len(sources)} sources to process")

            # Create DLT pipeline
            pipeline = self._create_pipeline()

            # Process each source
            for source_config in sources:
                source_name = source_config.get("name", "unknown")

                try:
                    records, raw_id = await self._process_source(
                        source_config=source_config,
                        provider_id=provider_id,
                        provider=provider,
                        start_date=start_date,
                        end_date=end_date,
                        provider_config=provider_config,
                        pipeline_run_id=pipeline_run_id,
                        pipeline=pipeline,
                    )

                    if records:  # Only add if we have records
                        all_extracted_records.extend(records)
                        all_raw_billing_ids.append(raw_id)

                except Exception as e:
                    error_msg = f"Failed to process source {source_name}: {e}"
                    logger.error(error_msg, exc_info=True)
                    errors.append(
                        {
                            "source": source_name,
                            "error": str(e),
                            "type": type(e).__name__,
                        }
                    )

            # Prepare output and return result
            return self._prepare_stage_result(
                all_extracted_records=all_extracted_records,
                all_raw_billing_ids=all_raw_billing_ids,
                sources=sources,
                errors=errors,
                start_time=start_time,
                context=context,
            )

        except Exception as e:
            logger.error(f"Extract stage failed: {e}", exc_info=True)
            return StageResult(
                stage_name="extract",
                success=False,
                records_processed=0,
                records_failed=0,
                duration_seconds=(datetime.now(UTC) - start_time).total_seconds(),
                errors=[{"error": str(e), "type": type(e).__name__}],
                data={},
            )

    async def _process_source(
        self,
        source_config: dict[str, Any],
        provider_id: str,
        provider: Any,
        start_date: datetime,
        end_date: datetime,
        provider_config: dict[str, Any],
        pipeline_run_id: str,
        pipeline: dlt.Pipeline,
    ) -> tuple[list[dict[str, Any]], str]:
        """Process a single source using appropriate extractor."""
        source_name = source_config.get("name", "unknown")
        source_type = source_config.get("source_type", "rest_api")

        logger.info(f"Processing source '{source_name}' of type '{source_type}'")

        # Create appropriate extractor
        extractor = ExtractorFactory.create_extractor(
            source_type=source_type, provider=provider, pipeline=pipeline
        )

        # Extract data
        records = await extractor.extract(
            source_config=source_config, start_date=start_date, end_date=end_date
        )

        logger.info(f"Extracted {len(records)} records from source '{source_name}'")

        # Save raw data only if we have records
        if records:
            raw_id = await self._save_raw_response_dlt(
                provider_id=provider_id,
                provider_config=provider_config,
                source_config=source_config,
                extracted_data=records,
                start_date=start_date,
                end_date=end_date,
                pipeline_run_id=pipeline_run_id,
                pipeline=pipeline,
            )

            logger.info(f"Saved raw data for source '{source_name}' with ID {raw_id}")
            return records, raw_id
        else:
            logger.warning(f"No records extracted from source '{source_name}'")
            return [], None

    def _get_sources(
        self,
        context: dict[str, Any],
        provider: Any,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict[str, Any]]:
        """Get sources from context or provider."""
        # Check if sources are already in context (e.g., from orchestrator)
        if "sources" in context:
            logger.debug("Using sources from context")
            return context["sources"]

        # Get from provider
        if hasattr(provider, "get_sources"):
            logger.debug("Getting sources from provider")
            sources = provider.get_sources(start_date, end_date)

            # Validate sources if provider has validation
            if hasattr(provider, "source_class") and provider.source_class:
                source_instance = provider.source_class()
                if hasattr(source_instance, "validate_source_configs"):
                    sources = source_instance.validate_source_configs(sources)

            return sources

        raise ValueError("Provider has no sources defined")

    async def _save_raw_response_dlt(
        self,
        provider_id: str,
        provider_config: dict[str, Any],
        source_config: dict[str, Any],
        extracted_data: list[dict[str, Any]],
        start_date: datetime,
        end_date: datetime,
        pipeline_run_id: str,
        pipeline: dlt.Pipeline,
    ) -> str:
        """Save extracted data to database using DLT."""
        raw_id = str(uuid4())
        source_name = source_config.get("name", "unknown")
        source_type = source_config.get("source_type", "unknown")

        # Extract any parameters used for extraction
        extraction_params = {}

        # Get params from different possible locations in source_config
        if "config" in source_config:
            config = source_config["config"]
            if "endpoint" in config and "params" in config["endpoint"]:
                extraction_params = config["endpoint"]["params"]
            elif "query_params" in config:
                extraction_params = config["query_params"]
        elif "params" in source_config:
            extraction_params = source_config["params"]

        # Serialize data to JSON strings for database storage
        extracted_data_json = json.dumps(extracted_data, default=str)
        extraction_params_json = (
            json.dumps(extraction_params, default=str)
            if extraction_params
            else json.dumps({})
        )

        # Prepare raw billing data record
        raw_record = {
            "id": raw_id,
            "provider_id": provider_id,
            "provider_type": provider_config["provider_type"],
            "source_name": source_name,
            "source_type": source_type,
            "extraction_timestamp": datetime.now(UTC),
            "extraction_params": extraction_params_json,
            "period_start": start_date,
            "period_end": end_date,
            "extracted_data": extracted_data_json,
            "record_count": len(extracted_data),
            "processed": False,
            "pipeline_run_id": str(pipeline_run_id),
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

        # Load to raw_billing_data table using DLT
        pipeline.run(
            [raw_record],
            table_name="raw_billing_data",
            write_disposition="append",
            primary_key="id",
        )

        logger.debug(
            f"Saved extracted data to database with ID {raw_id} "
            f"({len(extracted_data)} records from source '{source_name}')"
        )

        return raw_id

    def _create_pipeline(self) -> dlt.Pipeline:
        """Create DLT pipeline instance."""
        return self.config.get_dlt_pipeline(
            pipeline_name=self.pipeline_name, dataset_name=self.dataset_name
        )

    def _extract_context_fields(self, context: dict[str, Any]) -> tuple:
        """Extract required fields from context."""
        return (
            context.get("provider_id"),
            context["provider"],
            context["start_date"],
            context["end_date"],
            context["provider_config"],
            context["pipeline_run_id"],
        )

    def _prepare_stage_result(
        self,
        all_extracted_records: list[dict[str, Any]],
        all_raw_billing_ids: list[str],
        sources: list[dict[str, Any]],
        errors: list[dict[str, Any]],
        start_time: datetime,
        context: dict[str, Any],
    ) -> StageResult:
        """Prepare output data and stage result."""
        # Filter out None values from raw_billing_ids
        valid_raw_billing_ids = [id for id in all_raw_billing_ids if id is not None]

        output_data = {
            "raw_records": all_extracted_records,
            "raw_billing_ids": valid_raw_billing_ids,
            "extraction_summary": {
                "total_sources": len(sources),
                "successful_sources": len(valid_raw_billing_ids),
                "failed_sources": len(errors),
                "total_records": len(all_extracted_records),
            },
        }

        # Update context for next stage
        context.update(output_data)

        # Determine success - empty results are OK, only real errors should fail
        if len(sources) == 0:
            # No sources to process - this is success
            success = True
            logger.info("Extract stage completed with no sources - empty data period")
        elif len(all_extracted_records) == 0 and len(errors) == 0:
            # No records found but no errors - this is also success (empty period)
            success = True
            logger.info(
                f"Extract stage completed with no records found for period "
                f"{context['start_date']} to {context['end_date']}. "
                f"This may be normal for this period."
            )
        else:
            # Allow some source failures
            success = len(errors) <= len(sources) * 0.3  # Allow 30% failure rate

        return StageResult(
            stage_name="extract",
            success=success,
            records_processed=len(all_extracted_records),
            records_failed=len(errors),
            duration_seconds=(datetime.now(UTC) - start_time).total_seconds(),
            errors=errors,
            data=output_data,
        )

    async def rollback(self, context: dict[str, Any]) -> None:
        """Rollback extract stage - DLT handles transactions."""
        logger.info("Extract stage rollback: DLT manages transaction rollback")

    def get_progress(self, context: dict[str, Any]) -> dict[str, Any]:
        """Get current progress of extraction."""
        return {
            "stage": "extract",
            "sources_total": len(context.get("sources", [])),
            "sources_processed": context.get("sources_processed", 0),
            "records_extracted": len(context.get("raw_records", [])),
            "records_saved": len(context.get("raw_billing_ids", [])),
        }
