from datetime import UTC, datetime
from unittest.mock import Mock

import dlt
import pytest

from pipeline.stages.extractors.base import BaseExtractor


class MockExtractor(BaseExtractor):
    """Mock extractor for testing."""

    async def extract(self, source_config, start_date, end_date):
        return [{"id": 1, "data": "test"}]

    def create_dlt_source(self, source_config, start_date, end_date):
        return Mock()


class TestBaseExtractor:
    """Test BaseExtractor abstract class."""

    @pytest.fixture
    def mock_provider(self):
        provider = Mock()
        provider.test_attr = "test_value"
        provider.config = {"api_key": "test_key"}
        return provider

    @pytest.fixture
    def mock_pipeline(self):
        return Mock(spec=dlt.Pipeline)

    @pytest.fixture
    def extractor(self, mock_provider, mock_pipeline):
        return MockExtractor(mock_provider, mock_pipeline)

    def test_extractor_initialization(self, mock_provider, mock_pipeline):
        extractor = MockExtractor(mock_provider, mock_pipeline)

        assert extractor.provider == mock_provider
        assert extractor.pipeline == mock_pipeline

    @pytest.mark.asyncio
    async def test_extract(self, extractor):
        source_config = {"name": "test", "source_type": "rest_api", "config": {}}
        start_date = datetime(2023, 1, 1, tzinfo=UTC)
        end_date = datetime(2023, 1, 31, tzinfo=UTC)

        result = await extractor.extract(source_config, start_date, end_date)

        assert len(result) == 1
        assert result[0]["id"] == 1

    def test_validate_source_config_success(self, extractor):
        source_config = {
            "name": "test_source",
            "source_type": "rest_api",
            "config": {"endpoint": "/api/test"},
        }

        extractor.validate_source_config(source_config)

    def test_validate_source_config_missing_name(self, extractor):
        source_config = {"source_type": "rest_api", "config": {}}

        with pytest.raises(ValueError, match="must have a 'name' field"):
            extractor.validate_source_config(source_config)

    def test_get_provider_value_from_attribute(self, extractor):
        result = extractor.get_provider_value("test_attr")
        assert result == "test_value"

    def test_get_provider_value_from_config(self, extractor):
        # Remove the attribute so it falls back to config
        if hasattr(extractor.provider, "api_key"):
            delattr(extractor.provider, "api_key")

        result = extractor.get_provider_value("api_key")
        assert result == "test_key"

    def test_get_provider_value_default(self, extractor):
        # Create a simple object without Mock's automatic attribute creation
        class SimpleProvider:
            def __init__(self):
                self.config = {}
                self.additional_config = {}

        extractor.provider = SimpleProvider()

        result = extractor.get_provider_value("nonexistent", "default")
        assert result == "default"
