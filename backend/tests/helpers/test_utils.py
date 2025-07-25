"""
Test utility functions and helpers
"""

import csv
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from io import StringIO
from typing import Any

import pytest
from sqlalchemy.orm import Session


class TestUtils:
    """Utility functions for testing."""

    @staticmethod
    def assert_response_structure(response_data: dict, expected_keys: list[str]):
        """Assert that a response has the expected structure."""
        for key in expected_keys:
            assert key in response_data, f"Missing key: {key}"

    @staticmethod
    def assert_decimal_equal(actual: Any, expected: float, places: int = 2):
        """Assert that a decimal value equals expected float within precision."""
        if isinstance(actual, str):
            actual = Decimal(actual)
        elif isinstance(actual, float):
            actual = Decimal(str(actual))

        expected_decimal = Decimal(str(expected))
        assert abs(actual - expected_decimal) <= Decimal(f"0.{'0' * (places - 1)}1")

    @staticmethod
    def assert_datetime_close(actual: Any, expected: datetime, seconds: int = 60):
        """Assert that datetime is within specified seconds of expected."""
        if isinstance(actual, str):
            actual = datetime.fromisoformat(actual.replace("Z", "+00:00"))

        diff = abs((actual - expected).total_seconds())
        assert diff <= seconds, f"Datetime difference too large: {diff} seconds"

    @staticmethod
    def validate_csv_content(
        csv_content: str, expected_headers: list[str], min_rows: int = 1
    ):
        """Validate CSV content structure."""
        reader = csv.DictReader(StringIO(csv_content))

        # Check headers
        for header in expected_headers:
            assert header in reader.fieldnames, f"Missing CSV header: {header}"

        # Check minimum number of rows
        rows = list(reader)
        assert len(rows) >= min_rows, (
            f"Expected at least {min_rows} rows, got {len(rows)}"
        )

        return rows

    @staticmethod
    def validate_json_content(
        json_content: list[dict], expected_keys: list[str], min_items: int = 1
    ):
        """Validate JSON content structure."""
        assert isinstance(json_content, list), "JSON content should be a list"
        assert len(json_content) >= min_items, f"Expected at least {min_items} items"

        if json_content:
            for key in expected_keys:
                assert key in json_content[0], f"Missing JSON key: {key}"

        return json_content

    @staticmethod
    def create_test_file_content(format_type: str, data: list[dict]) -> Any:
        """Create test file content in specified format."""
        if format_type == "csv":
            if not data:
                return ""

            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            return output.getvalue()

        elif format_type == "json":
            return json.dumps(data, indent=2, default=str)

        else:
            raise ValueError(f"Unsupported format: {format_type}")

    @staticmethod
    def assert_pagination_response(
        response_data: dict, expected_total: int, page: int = 1, size: int = 10
    ):
        """Assert pagination response structure and values."""
        required_keys = ["data", "total", "page", "size", "pages"]
        TestUtils.assert_response_structure(response_data, required_keys)

        assert response_data["total"] == expected_total
        assert response_data["page"] == page
        assert response_data["size"] == size

        expected_pages = (expected_total + size - 1) // size  # Ceiling division
        assert response_data["pages"] == expected_pages

        # Data length should not exceed page size
        assert len(response_data["data"]) <= size

    @staticmethod
    def assert_cost_calculation(
        cost_data: dict, expected_total: float, tolerance: float = 0.01
    ):
        """Assert cost calculations are correct."""
        if "total_cost" in cost_data:
            actual_total = float(cost_data["total_cost"])
            assert abs(actual_total - expected_total) <= tolerance

        # If percentages are present, they should sum to ~100%
        if "services" in cost_data and cost_data["services"]:
            if "percentage" in cost_data["services"][0]:
                total_percentage = sum(
                    float(s.get("percentage", 0)) for s in cost_data["services"]
                )
                assert 99.0 <= total_percentage <= 101.0  # Allow for rounding

    @staticmethod
    def create_date_range_test_data(days: int = 7) -> list[datetime]:
        """Create a range of test dates."""
        now = datetime.now(UTC)
        return [now - timedelta(days=i) for i in range(days)]

    @staticmethod
    def assert_sorted_by_field(data: list[dict], field: str, ascending: bool = True):
        """Assert that data is sorted by specified field."""
        if len(data) < 2:
            return  # Can't check sorting with less than 2 items

        for i in range(len(data) - 1):
            current = data[i][field]
            next_item = data[i + 1][field]

            if ascending:
                assert current <= next_item, f"Data not sorted ascending by {field}"
            else:
                assert current >= next_item, f"Data not sorted descending by {field}"

    @staticmethod
    def count_records_by_field(data: list[dict], field: str) -> dict[Any, int]:
        """Count occurrences of each value in specified field."""
        counts = {}
        for item in data:
            value = item.get(field)
            counts[value] = counts.get(value, 0) + 1
        return counts

    @staticmethod
    def setup_test_data_in_db(session: Session, model_class, data_list: list[dict]):
        """Helper to insert test data into database."""
        objects = []
        for data in data_list:
            obj = model_class(**data)
            objects.append(obj)
            session.add(obj)

        session.commit()
        return objects

    @staticmethod
    def assert_error_response(
        response_data: dict, expected_status: int = 400, error_field: str = "detail"
    ):
        """Assert error response structure."""
        assert "detail" in response_data or error_field in response_data

        if error_field in response_data:
            assert response_data[error_field] is not None
            assert len(response_data[error_field]) > 0

    @staticmethod
    def generate_test_id(prefix: str = "test") -> str:
        """Generate a unique test ID."""
        import uuid

        return f"{prefix}-{uuid.uuid4().hex[:8]}"

    @staticmethod
    def clean_test_data(session: Session, model_classes: list):
        """Clean up test data from database."""
        for model_class in model_classes:
            session.query(model_class).delete()
        session.commit()


class MockResponse:
    """Mock HTTP response for testing."""

    def __init__(self, json_data: dict = None, status_code: int = 200, text: str = ""):
        self.json_data = json_data or {}
        self.status_code = status_code
        self.text = text
        self.headers = {}

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


class AsyncMockResponse:
    """Async mock HTTP response for testing."""

    def __init__(self, json_data: dict = None, status_code: int = 200, text: str = ""):
        self.json_data = json_data or {}
        self.status_code = status_code
        self.text = text
        self.headers = {}

    async def json(self):
        return self.json_data

    async def text(self):
        return self.text

    async def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


# Common test fixtures that can be imported
@pytest.fixture
def test_utils():
    """Provide TestUtils instance."""
    return TestUtils()


@pytest.fixture
def mock_response():
    """Provide MockResponse class."""
    return MockResponse


@pytest.fixture
def async_mock_response():
    """Provide AsyncMockResponse class."""
    return AsyncMockResponse
