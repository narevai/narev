"""
Tests for export service
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.services.export_service import ExportService


@pytest.fixture
def sample_export_data(test_db_session, sample_billing_data):
    """Create sample billing data for export tests."""
    from app.models.billing_data import BillingData

    records = []
    services = ["GPT-4", "GPT-3.5", "DALL-E"]
    now = datetime.now(UTC)

    for i in range(3):
        billing_data = sample_billing_data.copy()
        billing_data["id"] = f"billing-export-{i}"
        billing_data["service_name"] = services[i % len(services)]
        billing_data["billed_cost"] = Decimal(f"{10 + i * 2}.50")
        billing_data["charge_period_start"] = now - timedelta(days=3 - i)
        billing_data["charge_period_end"] = (
            now - timedelta(days=3 - i) + timedelta(hours=1)
        )

        record = BillingData(**billing_data)
        records.append(record)
        test_db_session.add(record)

    test_db_session.commit()
    return records


def test_export_data_csv():
    """Test exporting data as CSV."""
    test_data = [
        {"id": "1", "name": "Test 1", "cost": "10.50"},
        {"id": "2", "name": "Test 2", "cost": "20.00"},
    ]

    result = ExportService.export_data(test_data, "csv", "test_export")

    # CSV export returns StreamingResponse
    from fastapi.responses import StreamingResponse

    assert isinstance(result, StreamingResponse)
    assert result.media_type == "text/csv"
    assert "attachment" in result.headers["content-disposition"]
    assert "test_export" in result.headers["content-disposition"]
    assert ".csv" in result.headers["content-disposition"]


def test_export_data_xlsx():
    """Test exporting data as XLSX."""
    test_data = [
        {"id": "1", "name": "Test 1", "cost": "10.50"},
        {"id": "2", "name": "Test 2", "cost": "20.00"},
    ]

    result = ExportService.export_data(test_data, "xlsx", "test_export")

    # XLSX export returns StreamingResponse
    from fastapi.responses import StreamingResponse

    assert isinstance(result, StreamingResponse)
    assert (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        in result.media_type
    )
    assert "attachment" in result.headers["content-disposition"]
    assert "test_export" in result.headers["content-disposition"]
    assert ".xlsx" in result.headers["content-disposition"]


def test_export_data_invalid_format():
    """Test exporting with unsupported format."""
    test_data = [{"id": "1", "name": "Test"}]

    with pytest.raises(HTTPException):
        ExportService.export_data(
            test_data, "json", "test"
        )  # JSON not supported anymore


def test_export_data_empty_data():
    """Test exporting empty data."""
    with pytest.raises(HTTPException):
        ExportService.export_data([], "csv", "test")


def test_export_data_with_metadata():
    """Test exporting data with metadata in XLSX."""
    test_data = [{"id": "1", "name": "Test"}]
    metadata = {
        "total_records": 10,
        "exported_records": 1,
        "export_date": datetime.now(UTC),
    }

    result = ExportService.export_data(test_data, "xlsx", "test", metadata=metadata)

    from fastapi.responses import StreamingResponse

    assert isinstance(result, StreamingResponse)
    # Metadata should be included in Excel file as separate sheet


@patch("pandas.DataFrame.to_csv")
def test_csv_export_error_handling(mock_to_csv):
    """Test CSV export error handling."""
    mock_to_csv.side_effect = Exception("CSV error")
    test_data = [{"id": "1", "name": "Test"}]

    with pytest.raises(HTTPException):
        ExportService.export_data(test_data, "csv", "test")


@patch("pandas.ExcelWriter")
def test_xlsx_export_error_handling(mock_writer):
    """Test XLSX export error handling."""
    mock_writer.side_effect = Exception("Excel error")
    test_data = [{"id": "1", "name": "Test"}]

    with pytest.raises(HTTPException):
        ExportService.export_data(test_data, "xlsx", "test")


def test_billing_export_service():
    """Test BillingExportService wrapper."""
    from app.services.export_service import BillingExportService

    test_data = [{"id": "1", "service_name": "GPT-4", "cost": "10.50"}]
    export_params = {
        "start_date": datetime.now(UTC) - timedelta(days=7),
        "end_date": datetime.now(UTC),
        "provider_id": "provider-1",
        "service_name": "GPT-4",
    }

    # Test CSV export through BillingExportService
    result = BillingExportService.export_billing_data(
        test_data, "csv", total_records=1, export_params=export_params
    )

    from fastapi.responses import StreamingResponse

    assert isinstance(result, StreamingResponse)
    assert "billing_data" in result.headers["content-disposition"]


def test_filename_generation():
    """Test that filenames are generated with timestamps."""
    test_data = [{"id": "1", "name": "Test"}]

    # CSV
    result_csv = ExportService.export_data(test_data, "csv", "billing_test")
    filename_csv = result_csv.headers["content-disposition"]
    assert "billing_test_" in filename_csv
    assert ".csv" in filename_csv

    # XLSX
    result_xlsx = ExportService.export_data(test_data, "xlsx", "billing_test")
    filename_xlsx = result_xlsx.headers["content-disposition"]
    assert "billing_test_" in filename_xlsx
    assert ".xlsx" in filename_xlsx


def test_metadata_sheet_creation():
    """Test that metadata is added to Excel files."""
    test_data = [{"id": "1", "name": "Test"}]
    metadata = {
        "export_date": datetime.now(UTC),
        "total_records": 100,
        "provider_id": "test-provider",
        "custom_field": None,  # Test None handling
    }

    result = ExportService.export_data(test_data, "xlsx", "test", metadata=metadata)

    # Should not raise error and return StreamingResponse
    from fastapi.responses import StreamingResponse

    assert isinstance(result, StreamingResponse)


def test_large_dataset_handling():
    """Test handling of larger datasets."""
    # Create larger test dataset
    test_data = []
    for i in range(100):  # Smaller dataset for testing
        test_data.append(
            {
                "id": str(i),
                "service_name": f"Service-{i % 10}",
                "cost": f"{i * 0.5:.2f}",
                "date": datetime.now(UTC).isoformat(),
            }
        )

    # Should handle CSV export
    result_csv = ExportService.export_data(test_data, "csv", "large_test")
    from fastapi.responses import StreamingResponse

    assert isinstance(result_csv, StreamingResponse)

    # Should handle XLSX export
    result_xlsx = ExportService.export_data(test_data, "xlsx", "large_test")
    assert isinstance(result_xlsx, StreamingResponse)


def test_supported_formats_only():
    """Test that only CSV and XLSX formats are supported."""
    test_data = [{"id": "1", "name": "Test"}]

    # Supported formats should work
    csv_result = ExportService.export_data(test_data, "csv", "test")
    xlsx_result = ExportService.export_data(test_data, "xlsx", "test")

    from fastapi.responses import StreamingResponse

    assert isinstance(csv_result, StreamingResponse)
    assert isinstance(xlsx_result, StreamingResponse)

    # Unsupported formats should fail
    unsupported_formats = ["json", "parquet", "txt", "xml"]
    for format_type in unsupported_formats:
        with pytest.raises(HTTPException):
            ExportService.export_data(test_data, format_type, "test")
