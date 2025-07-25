from datetime import UTC, datetime

import pytest

from pipeline.sources.base import BaseSource


class MockSource(BaseSource):
    """Mock source for testing."""

    def get_sources(self, start_date, end_date):
        return [
            {
                "name": "test_source",
                "source_type": "rest_api",
                "config": {"endpoint": "/api/data"},
            }
        ]


class TestBaseSource:
    """Test BaseSource abstract class."""

    @pytest.fixture
    def source(self):
        return MockSource()

    def test_get_sources(self, source):
        start_date = datetime(2023, 1, 1, tzinfo=UTC)
        end_date = datetime(2023, 1, 31, tzinfo=UTC)

        sources = source.get_sources(start_date, end_date)

        assert len(sources) == 1
        assert sources[0]["name"] == "test_source"
        assert sources[0]["source_type"] == "rest_api"

    def test_validate_source_configs_success(self, source):
        sources = [
            {
                "name": "valid_source",
                "source_type": "rest_api",
                "config": {"endpoint": "/api/test"},
            }
        ]

        result = source.validate_source_configs(sources)
        assert result == sources

    def test_validate_source_configs_missing_name(self, source):
        sources = [{"source_type": "rest_api", "config": {}}]

        with pytest.raises(ValueError, match="Source 0 missing required field: name"):
            source.validate_source_configs(sources)

    def test_validate_source_configs_invalid_source_type(self, source):
        sources = [{"name": "test_source", "source_type": "invalid_type", "config": {}}]

        with pytest.raises(ValueError, match="invalid source_type"):
            source.validate_source_configs(sources)
