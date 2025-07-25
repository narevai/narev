"""
Hamilton Pipeline Orchestrator
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from hamilton import driver
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.pipeline_run import PipelineRun
from app.services.encryption_service import EncryptionService
from pipeline.config import PipelineConfig
from pipeline.stages.base import StageResult
from pipeline.stages.extract import ExtractStage
from pipeline.stages.load import LoadStage
from pipeline.stages.transform import TransformStage
from providers.registry import ProviderRegistry

logger = logging.getLogger(__name__)


# =============================================================================
# Hamilton DAG Functions - SYNCHRONOUS
# =============================================================================


def pipeline_context(
    provider_id: UUID,
    start_date: datetime,
    end_date: datetime,
    pipeline_run_id: UUID,
    provider_config: dict[str, Any],
    pipeline_config: PipelineConfig,
    db_session: Session,
) -> dict[str, Any]:
    """
    Initialize pipeline context - ROOT NODE of Hamilton DAG.

    """
    provider_type = provider_config["provider_type"]

    # Get provider instance from registry
    provider = ProviderRegistry.create_provider(provider_type, provider_config)
    if not provider:
        raise ValueError(
            f"Failed to create provider instance for type: {provider_type}"
        )

    # Get mapper from registry
    mapper = ProviderRegistry.get_mapper(provider_type, provider_config)
    if not mapper:
        raise ValueError(f"No mapper found for provider type: {provider_type}")

    # Get sources from provider
    if hasattr(provider, "get_sources"):
        sources = provider.get_sources(start_date, end_date)
        logger.info(
            f"Hamilton: Got {len(sources)} sources from provider {provider_type}"
        )
    else:
        raise ValueError(
            f"Provider {provider_type} missing required method: get_sources()"
        )

    if not sources:
        logger.warning(f"No sources found for provider type: {provider_type}")

    return {
        "pipeline_run_id": pipeline_run_id,
        "start_date": start_date,
        "end_date": end_date,
        "provider_id": provider_id,
        "provider_config": provider_config,
        "provider": provider,
        "mapper": mapper,
        "sources": sources,
        "provider_type": provider_type,
        "pipeline_config": pipeline_config,
        "db_session": db_session,
    }


def extract_stage_result(pipeline_context: dict[str, Any]) -> StageResult:
    """
    Extract stage using existing ExtractStage class.
    """
    logger.info("Hamilton: Starting extract stage")

    # Get configuration and database session
    pipeline_config = pipeline_context["pipeline_config"]
    db_session = pipeline_context["db_session"]

    # Create existing ExtractStage instance
    extract_stage = ExtractStage(pipeline_config, db_session)

    try:
        result = asyncio.run(extract_stage.execute(pipeline_context))
    except RuntimeError as e:
        if "asyncio.run() cannot be called from a running event loop" in str(e):
            # Fallback: use get_event_loop().run_until_complete() if needed
            # But this should not happen in thread executor
            logger.warning("Using fallback event loop handling")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    extract_stage.execute(pipeline_context)
                )
            finally:
                loop.close()
        else:
            raise

    logger.info(
        f"Hamilton: Extract stage completed - {result.records_processed} records"
    )
    return result


def transform_stage_result(
    extract_stage_result: StageResult, pipeline_context: dict[str, Any]
) -> StageResult:
    """
    Transform stage using existing TransformStage class.
    """
    logger.info("Hamilton: Starting transform stage")

    # Get configuration and database session
    pipeline_config = pipeline_context["pipeline_config"]
    db_session = pipeline_context["db_session"]

    # Update context with extract results
    updated_context = {**pipeline_context}
    if extract_stage_result.success and extract_stage_result.data:
        updated_context.update(extract_stage_result.data)

    # Create existing TransformStage instance
    transform_stage = TransformStage(pipeline_config, db_session)

    # Use asyncio.run() for isolated async execution
    try:
        result = asyncio.run(transform_stage.execute(updated_context))
    except RuntimeError as e:
        if "asyncio.run() cannot be called from a running event loop" in str(e):
            logger.warning("Using fallback event loop handling")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    transform_stage.execute(updated_context)
                )
            finally:
                loop.close()
        else:
            raise

    logger.info(
        f"Hamilton: Transform stage completed - {result.records_processed} records"
    )
    return result


def load_stage_result(
    transform_stage_result: StageResult, pipeline_context: dict[str, Any]
) -> StageResult:
    """
    Load stage using existing LoadStage class.

    """
    logger.info("Hamilton: Starting load stage")

    # Get configuration and database session
    pipeline_config = pipeline_context["pipeline_config"]
    db_session = pipeline_context["db_session"]

    # Update context with transform results
    updated_context = {**pipeline_context}
    if transform_stage_result.success and transform_stage_result.data:
        updated_context.update(transform_stage_result.data)

    # Create existing LoadStage instance
    load_stage = LoadStage(pipeline_config, db_session)

    # Use asyncio.run() for isolated async execution
    try:
        result = asyncio.run(load_stage.execute(updated_context))
    except RuntimeError as e:
        if "asyncio.run() cannot be called from a running event loop" in str(e):
            logger.warning("Using fallback event loop handling")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(load_stage.execute(updated_context))
            finally:
                loop.close()
        else:
            raise

    logger.info(f"Hamilton: Load stage completed - {result.records_processed} records")
    return result


def pipeline_result(
    extract_stage_result: StageResult,
    transform_stage_result: StageResult,
    load_stage_result: StageResult,
    pipeline_context: dict[str, Any],
) -> dict[str, Any]:
    """
    Final pipeline result aggregation.

    """
    pipeline_run_id = pipeline_context["pipeline_run_id"]
    provider_id = pipeline_context["provider_id"]

    # Determine final status based on all stages
    all_success = all(
        [
            extract_stage_result.success,
            transform_stage_result.success,
            load_stage_result.success,
        ]
    )

    final_status = "completed" if all_success else "failed"

    # Build comprehensive result using StageResult objects
    return {
        "pipeline_run_id": str(pipeline_run_id),
        "provider_id": str(provider_id),
        "status": final_status,
        "stages": {
            "extract": {
                "success": extract_stage_result.success,
                "records_processed": extract_stage_result.records_processed,
                "records_failed": extract_stage_result.records_failed,
                "duration": extract_stage_result.duration_seconds,
                "errors": extract_stage_result.errors[:3],
            },
            "transform": {
                "success": transform_stage_result.success,
                "records_processed": transform_stage_result.records_processed,
                "records_failed": transform_stage_result.records_failed,
                "duration": transform_stage_result.duration_seconds,
                "errors": transform_stage_result.errors[:3],
            },
            "load": {
                "success": load_stage_result.success,
                "records_processed": load_stage_result.records_processed,
                "records_failed": load_stage_result.records_failed,
                "duration": load_stage_result.duration_seconds,
                "errors": load_stage_result.errors[:3],
            },
        },
        "totals": {
            "total_records_processed": load_stage_result.records_processed,
            "total_records_failed": load_stage_result.records_failed,
            "total_duration": (
                extract_stage_result.duration_seconds
                + transform_stage_result.duration_seconds
                + load_stage_result.duration_seconds
            ),
            "stages_completed": sum(
                [
                    extract_stage_result.success,
                    transform_stage_result.success,
                    load_stage_result.success,
                ]
            ),
            "stages_failed": sum(
                [
                    not extract_stage_result.success,
                    not transform_stage_result.success,
                    not load_stage_result.success,
                ]
            ),
        },
    }


# =============================================================================
# Optional: Monitoring functions
# =============================================================================


def extract_summary(extract_stage_result: StageResult) -> dict[str, Any]:
    """Optional function to create extract summary for monitoring."""
    return {
        "stage": "extract",
        "success": extract_stage_result.success,
        "records": extract_stage_result.records_processed,
        "errors": len(extract_stage_result.errors),
        "duration": extract_stage_result.duration_seconds,
    }


def transform_summary(transform_stage_result: StageResult) -> dict[str, Any]:
    """Optional function to create transform summary for monitoring."""
    return {
        "stage": "transform",
        "success": transform_stage_result.success,
        "records": transform_stage_result.records_processed,
        "errors": len(transform_stage_result.errors),
        "duration": transform_stage_result.duration_seconds,
    }


def load_summary(load_stage_result: StageResult) -> dict[str, Any]:
    """Optional function to create load summary for monitoring."""
    return {
        "stage": "load",
        "success": load_stage_result.success,
        "records": load_stage_result.records_processed,
        "errors": len(load_stage_result.errors),
        "duration": load_stage_result.duration_seconds,
    }


def pipeline_summary(
    extract_summary: dict[str, Any],
    transform_summary: dict[str, Any],
    load_summary: dict[str, Any],
) -> dict[str, Any]:
    """Optional function to create complete pipeline summary."""
    return {
        "stages": [extract_summary, transform_summary, load_summary],
        "total_duration": (
            extract_summary["duration"]
            + transform_summary["duration"]
            + load_summary["duration"]
        ),
        "all_successful": all(
            [
                extract_summary["success"],
                transform_summary["success"],
                load_summary["success"],
            ]
        ),
    }


# =============================================================================
# Hamilton Orchestrator Class
# =============================================================================


class HamiltonOrchestrator:
    """
    Hamilton-based pipeline orchestrator with thread executor approach.

    This class provides async interface while running Hamilton synchronously
    in a thread pool to avoid event loop conflicts.
    """

    def __init__(self, config: PipelineConfig | None = None):
        """Initialize Hamilton orchestrator."""
        self.config = config or PipelineConfig()
        self.encryption_service = EncryptionService()

        # Create Hamilton driver - it auto-discovers functions in this module
        self.driver = self._create_hamilton_driver()

        logger.info("Hamilton orchestrator initialized")

    def _create_hamilton_driver(self) -> driver.Driver:
        """Create Hamilton driver with our DAG functions."""
        # Import current module to get the functions
        import sys

        current_module = sys.modules[__name__]

        # Hamilton automatically builds DAG from function signatures
        return driver.Builder().with_modules(current_module).build()

    def get_dag_structure(self) -> dict[str, Any]:
        """Get DAG structure information."""
        # Get all available functions (nodes)
        nodes = self.driver.list_available_variables()

        # Get dependencies for key nodes
        dependencies = {}
        for node in [
            "extract_stage_result",
            "transform_stage_result",
            "load_stage_result",
            "pipeline_result",
        ]:
            if node in nodes:
                deps = self.driver.what_is_upstream_of(node)
                dependencies[node] = list(deps)

        return {
            "nodes": sorted(nodes),
            "dependencies": dependencies,
            "execution_order": [
                "pipeline_context",
                "extract_stage_result",
                "transform_stage_result",
                "load_stage_result",
                "pipeline_result",
            ],
        }

    def visualize_dag(self, output_path: str = "hamilton_pipeline_dag.png") -> str:
        """Generate DAG visualization."""
        try:
            # Determine format from extension
            format_ext = output_path.split(".")[-1] if "." in output_path else "png"

            # Create example inputs for visualization
            example_inputs = {
                "provider_id": UUID("12345678-1234-5678-9012-123456789012"),
                "start_date": datetime.now(UTC),
                "end_date": datetime.now(UTC),
                "pipeline_run_id": UUID("87654321-4321-8765-2109-876543210987"),
                "provider_config": {"provider_type": "example"},
                "pipeline_config": self.config,
                "db_session": None,
            }

            # Generate visualization
            self.driver.visualize_execution(
                ["pipeline_result"],  # Final node we want
                output_file_path=output_path,
                render_kwargs={"format": format_ext},
                inputs=example_inputs,
            )

            # Verify file was created
            import os

            if not os.path.exists(output_path):
                raise FileNotFoundError(
                    f"Hamilton failed to create file: {output_path}"
                )

            logger.info(f"DAG visualization saved to: {output_path}")
            return output_path

        except ImportError:
            logger.warning(
                'DAG visualization requires: pip install "sf-hamilton[visualization]"'
            )
            raise
        except Exception as e:
            logger.error(f"Failed to generate DAG visualization: {e}")
            raise

    async def run_pipeline(
        self,
        provider_id: UUID,
        start_date: datetime,
        end_date: datetime,
        run_type: str = "incremental",
    ) -> dict[str, Any]:
        """
        Run pipeline using Hamilton DAG in thread executor.

        """
        pipeline_run_id = uuid4()
        db = SessionLocal()

        try:
            # Initialize pipeline run
            provider_config, pipeline_run = await self._initialize_pipeline(
                db, provider_id, pipeline_run_id, run_type, start_date, end_date
            )

            # Prepare Hamilton inputs - these become the DAG inputs
            inputs = {
                "provider_id": provider_id,
                "start_date": start_date,
                "end_date": end_date,
                "pipeline_run_id": pipeline_run_id,
                "provider_config": provider_config,
                "pipeline_config": self.config,
                "db_session": db,
            }

            # Execute Hamilton DAG in thread pool to avoid event loop conflicts
            logger.info(
                f"Hamilton: Executing DAG for provider {provider_config['name']} in thread pool"
            )

            # Get current event loop
            loop = asyncio.get_event_loop()

            # Run Hamilton SYNCHRONOUSLY in thread executor
            # This is the key - Hamilton runs in its own thread with no event loop conflicts
            result = await loop.run_in_executor(
                None,  # Use default thread pool executor
                self._execute_hamilton_sync,  # Synchronous function
                inputs,  # Arguments
            )

            # Extract the final result
            pipeline_result = result["pipeline_result"]

            # Update pipeline run with final results
            final_status = pipeline_result["status"]
            await self._finalize_pipeline(
                db, pipeline_run, final_status, pipeline_result
            )

            logger.info(
                f"Hamilton: Pipeline {pipeline_run_id} completed with status: {final_status}"
            )

            return pipeline_result

        except Exception as e:
            logger.error(f"Hamilton: Pipeline failed for provider {provider_id}: {e}")
            await self._handle_pipeline_error(db, locals().get("pipeline_run"), str(e))
            raise
        finally:
            db.close()

    def _execute_hamilton_sync(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        Execute Hamilton DAG synchronously.

        This function runs in a thread pool, so it has no event loop conflicts.
        Hamilton can run its synchronous DAG functions safely here.
        """
        try:
            # Execute Hamilton DAG synchronously
            # Each DAG function will use asyncio.run() for isolated async execution
            result = self.driver.execute(
                ["pipeline_result"],  # We want the final result
                inputs=inputs,  # These are injected into the DAG
                overrides={},  # Can override any intermediate values
            )

            return result

        except Exception as e:
            logger.error(f"Hamilton synchronous execution failed: {e}")
            raise

    async def run_pipeline_with_intermediate_results(
        self,
        provider_id: UUID,
        start_date: datetime,
        end_date: datetime,
        run_type: str = "incremental",
    ) -> dict[str, Any]:
        """Run pipeline and return all intermediate results for debugging."""
        pipeline_run_id = uuid4()
        db = SessionLocal()

        try:
            provider_config, pipeline_run = await self._initialize_pipeline(
                db, provider_id, pipeline_run_id, run_type, start_date, end_date
            )

            inputs = {
                "provider_id": provider_id,
                "start_date": start_date,
                "end_date": end_date,
                "pipeline_run_id": pipeline_run_id,
                "provider_config": provider_config,
                "pipeline_config": self.config,
                "db_session": db,
            }

            # Execute and get ALL intermediate results using thread executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._execute_hamilton_with_intermediates, inputs
            )

            # Return all results for debugging
            return {
                "pipeline_result": result["pipeline_result"],
                "stage_results": {
                    "extract": result["extract_stage_result"].to_dict(),
                    "transform": result["transform_stage_result"].to_dict(),
                    "load": result["load_stage_result"].to_dict(),
                },
                "summaries": {
                    "extract": result["extract_summary"],
                    "transform": result["transform_summary"],
                    "load": result["load_summary"],
                    "pipeline": result["pipeline_summary"],
                },
            }

        finally:
            db.close()

    def _execute_hamilton_with_intermediates(
        self, inputs: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute Hamilton and return all intermediate results."""
        return self.driver.execute(
            [
                "extract_stage_result",
                "transform_stage_result",
                "load_stage_result",
                "pipeline_result",
                "extract_summary",
                "transform_summary",
                "load_summary",
                "pipeline_summary",
            ],
            inputs=inputs,
        )

    # Rest of the methods remain the same as in previous implementation
    async def _initialize_pipeline(
        self, db, provider_id, pipeline_run_id, run_type, start_date, end_date
    ):
        """Initialize pipeline run and get provider configuration."""
        # Get provider configuration
        provider_config = await self._get_provider_config(db, provider_id)
        if not provider_config:
            raise ValueError(f"Provider {provider_id} not found or not configured")

        # Create pipeline run
        pipeline_run = await self._create_pipeline_run(
            db, provider_id, pipeline_run_id, run_type, start_date, end_date
        )

        logger.info(
            f"Hamilton: Initialized pipeline {pipeline_run_id} for provider {provider_config['name']}"
        )

        return provider_config, pipeline_run

    async def _create_pipeline_run(
        self, db, provider_id, pipeline_run_id, run_type, start_date, end_date
    ):
        """Create pipeline run with retry logic."""
        max_retries = 3

        for attempt in range(max_retries):
            try:
                pipeline_run = PipelineRun(
                    id=str(pipeline_run_id),
                    provider_id=str(provider_id),
                    pipeline_name=self.config.name,
                    pipeline_version=self.config.version,
                    run_type=run_type,
                    status="running",
                    started_at=self._utcnow(),
                    pipeline_config=self.config.to_dict(),
                    date_range_start=start_date,
                    date_range_end=end_date,
                    current_stage="initializing",
                )

                db.add(pipeline_run)
                db.commit()
                db.refresh(pipeline_run)

                return pipeline_run

            except IntegrityError:
                db.rollback()
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Database conflict on attempt {attempt + 1}, retrying..."
                    )
                    pipeline_run_id = uuid4()
                    await asyncio.sleep(0.1 * (attempt + 1))
                    continue
                else:
                    raise
            except Exception:
                db.rollback()
                raise

        raise Exception(f"Failed to create pipeline run after {max_retries} attempts")

    async def _finalize_pipeline(self, db, pipeline_run, final_status, pipeline_result):
        """Finalize pipeline run with results."""
        try:
            db.refresh(pipeline_run)

            pipeline_run.status = final_status
            pipeline_run.current_stage = "completed"
            pipeline_run.completed_at = self._utcnow()

            # Add metrics from pipeline result
            if "totals" in pipeline_result:
                totals = pipeline_result["totals"]
                pipeline_run.records_extracted = totals.get(
                    "total_records_processed", 0
                )
                pipeline_run.records_transformed = totals.get(
                    "total_records_processed", 0
                )
                pipeline_run.records_loaded = totals.get("total_records_processed", 0)
                pipeline_run.records_failed = totals.get("total_records_failed", 0)

            # Calculate duration
            if pipeline_run.completed_at and pipeline_run.started_at:
                completed_at = self._ensure_timezone_aware(pipeline_run.completed_at)
                started_at = self._ensure_timezone_aware(pipeline_run.started_at)
                duration = (completed_at - started_at).total_seconds()
                pipeline_run.duration_seconds = int(duration)

            db.commit()

        except Exception as e:
            db.rollback()
            logger.error(f"Hamilton: Failed to finalize pipeline run: {e}")

    async def _handle_pipeline_error(self, db, pipeline_run, error_message):
        """Handle pipeline-level errors."""
        if pipeline_run:
            try:
                db.refresh(pipeline_run)
                pipeline_run.status = "failed"
                pipeline_run.error_message = error_message
                db.commit()
            except Exception as update_error:
                logger.error(
                    f"Hamilton: Failed to update pipeline run on error: {update_error}"
                )

    async def _get_provider_config(self, db, provider_id):
        """Get provider configuration from database."""
        from app.services.provider_service import ProviderService

        provider_service = ProviderService(db)
        return provider_service.get_provider_config(provider_id)

    def _utcnow(self) -> datetime:
        """Get current UTC time with timezone info."""
        return datetime.now(UTC)

    def _ensure_timezone_aware(self, dt: datetime | None) -> datetime | None:
        """Ensure datetime is timezone-aware."""
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt
