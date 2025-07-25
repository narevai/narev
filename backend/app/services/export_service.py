"""
Export Service - Handling data export in various formats
"""

import io
import logging
from datetime import UTC, datetime
from typing import Any

import pandas as pd
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting data in various formats."""

    @staticmethod
    def export_data(
        data: list[dict[str, Any]],
        format: str,
        filename_prefix: str = "export",
        metadata: dict[str, Any] | None = None,
    ) -> StreamingResponse | dict[str, Any]:
        """
        Export data in specified format.

        Args:
            data: List of records to export
            format: Export format (csv, json, xlsx)
            filename_prefix: Prefix for generated filename
            metadata: Optional metadata for Excel export

        Returns:
            StreamingResponse for file downloads or dict for JSON
        """
        if not data:
            raise HTTPException(status_code=404, detail="No data found for export")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "csv":
            return ExportService._export_csv(data, filename_prefix, timestamp)
        elif format == "xlsx":
            return ExportService._export_xlsx(
                data, filename_prefix, timestamp, metadata
            )
        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported export format: {format}"
            )

    @staticmethod
    def _export_csv(
        data: list[dict[str, Any]], filename_prefix: str, timestamp: str
    ) -> StreamingResponse:
        """Export data as CSV file."""
        logger.info("Exporting data as CSV")

        try:
            # Convert to DataFrame
            df = pd.DataFrame(data)
            logger.info(f"DataFrame created with shape: {df.shape}")

            # Create CSV in memory
            output = io.StringIO()
            df.to_csv(output, index=False, encoding="utf-8")
            output.seek(0)

            filename = f"{filename_prefix}_{timestamp}.csv"
            logger.info(f"CSV created successfully, filename: {filename}")

            return StreamingResponse(
                io.BytesIO(output.getvalue().encode("utf-8")),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

        except Exception as e:
            logger.error(f"Error creating CSV: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Error generating CSV: {str(e)}"
            ) from e

    @staticmethod
    def _export_xlsx(
        data: list[dict[str, Any]],
        filename_prefix: str,
        timestamp: str,
        metadata: dict[str, Any] | None = None,
    ) -> StreamingResponse:
        """Export data as Excel file."""
        logger.info("Exporting data as XLSX")

        try:
            # Convert to DataFrame
            df = pd.DataFrame(data)
            logger.info(f"DataFrame created with shape: {df.shape}")

            # Create Excel file in memory
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                # Main data sheet
                df.to_excel(writer, sheet_name="Data", index=False)

                # Metadata sheet if provided
                if metadata:
                    ExportService._add_metadata_sheet(writer, metadata)

            output.seek(0)
            filename = f"{filename_prefix}_{timestamp}.xlsx"
            logger.info(f"XLSX created successfully, filename: {filename}")

            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

        except Exception as e:
            logger.error(f"Error creating XLSX: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Error generating Excel file: {str(e)}"
            ) from e

    @staticmethod
    def _add_metadata_sheet(writer: pd.ExcelWriter, metadata: dict[str, Any]) -> None:
        """Add metadata sheet to Excel file."""
        try:
            # Convert metadata to DataFrame
            metadata_items = []
            for key, value in metadata.items():
                # Convert datetime objects to ISO string
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif value is None:
                    value = "Not specified"

                metadata_items.append(
                    {"Property": key.replace("_", " ").title(), "Value": str(value)}
                )

            metadata_df = pd.DataFrame(metadata_items)
            metadata_df.to_excel(writer, sheet_name="Export Info", index=False)

        except Exception as e:
            logger.warning(f"Failed to add metadata sheet: {str(e)}")
            # Don't fail the entire export if metadata fails


class BillingExportService:
    """Specialized service for billing data exports."""

    @staticmethod
    def export_billing_data(
        data: list[dict[str, Any]],
        format: str,
        total_records: int,
        export_params: dict[str, Any],
    ) -> StreamingResponse | dict[str, Any]:
        """
        Export billing data with billing-specific metadata.

        Args:
            data: Billing records to export
            format: Export format
            total_records: Total number of records available
            export_params: Parameters used for the export

        Returns:
            StreamingResponse or dict based on format
        """
        # Prepare billing-specific metadata
        metadata = {
            "total_records": total_records,
            "exported_records": len(data),
            "export_date": datetime.now(UTC),
            "start_date": export_params.get("start_date"),
            "end_date": export_params.get("end_date"),
            "provider_id": export_params.get("provider_id"),
            "service_category": export_params.get("service_category"),
            "service_name": export_params.get("service_name"),
            "charge_category": export_params.get("charge_category"),
            "min_cost": export_params.get("min_cost"),
            "max_cost": export_params.get("max_cost"),
            "skip": export_params.get("skip", 0),
            "limit": export_params.get("limit"),
        }

        return ExportService.export_data(
            data=data, format=format, filename_prefix="billing_data", metadata=metadata
        )
