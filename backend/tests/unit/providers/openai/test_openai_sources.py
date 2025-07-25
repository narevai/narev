"""
Unit tests for OpenAI Data Sources Configuration
"""

from datetime import datetime
from unittest.mock import patch

import pytest

from pipeline.sources.base import BaseSource
from providers.openai.sources import OpenAISource


class TestOpenAISource:
    """Test suite for OpenAISource class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.start_date = datetime(2024, 1, 1, 0, 0, 0)
        self.end_date = datetime(2024, 1, 31, 23, 59, 59)

    def test_init(self):
        """Test initialization."""
        source = OpenAISource()
        assert isinstance(source, BaseSource)

    def test_get_sources_basic_structure(self):
        """Test basic source structure."""
        source = OpenAISource()

        with patch.object(source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []
            source.get_sources(self.start_date, self.end_date)

            called_args = mock_validate.call_args[0][0]
            assert len(called_args) == 6

            expected_names = [
                "completions_usage",
                "embeddings_usage",
                "images_usage",
                "audio_speeches_usage",
                "audio_transcriptions_usage",
                "moderations_usage",
            ]
            actual_names = [s["name"] for s in called_args]
            assert actual_names == expected_names

    def test_get_sources_timestamp_conversion(self):
        """Test timestamp conversion."""
        source = OpenAISource()

        with patch.object(source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []
            source.get_sources(self.start_date, self.end_date)

            called_args = mock_validate.call_args[0][0]
            first_source = called_args[0]

            params = first_source["config"]["endpoint"]["params"]
            assert params["start_time"] == int(self.start_date.timestamp())
            assert params["end_time"] == int(self.end_date.timestamp())

    def test_get_sources_common_parameters(self):
        """Test common parameters across all sources."""
        source = OpenAISource()

        with patch.object(source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []
            source.get_sources(self.start_date, self.end_date)

            called_args = mock_validate.call_args[0][0]

            for source_config in called_args:
                params = source_config["config"]["endpoint"]["params"]
                assert params["bucket_width"] == "1d"
                assert params["group_by"] == ["model", "api_key_id"]
                assert params["limit"] == 30

    def test_get_sources_completions_usage(self):
        """Test completions usage source configuration."""
        source = OpenAISource()

        with patch.object(source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []
            source.get_sources(self.start_date, self.end_date)

            called_args = mock_validate.call_args[0][0]
            completions_source = called_args[0]

            assert completions_source["name"] == "completions_usage"
            assert completions_source["source_type"] == "rest_api"

            config = completions_source["config"]
            assert config["endpoint"]["path"] == "/organization/usage/completions"
            assert config["endpoint"]["method"] == "GET"
            assert config["data_selector"] == "data"
            assert config["primary_key"] == ["bucket_start_time", "model", "api_key_id"]

    def test_get_sources_embeddings_usage(self):
        """Test embeddings usage source configuration."""
        source = OpenAISource()

        with patch.object(source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []
            source.get_sources(self.start_date, self.end_date)

            called_args = mock_validate.call_args[0][0]
            embeddings_source = called_args[1]

            assert embeddings_source["name"] == "embeddings_usage"
            assert (
                embeddings_source["config"]["endpoint"]["path"]
                == "/organization/usage/embeddings"
            )

    def test_get_sources_images_usage(self):
        """Test images usage source configuration."""
        source = OpenAISource()

        with patch.object(source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []
            source.get_sources(self.start_date, self.end_date)

            called_args = mock_validate.call_args[0][0]
            images_source = called_args[2]

            assert images_source["name"] == "images_usage"
            assert (
                images_source["config"]["endpoint"]["path"]
                == "/organization/usage/images"
            )

    def test_get_sources_audio_speeches_usage(self):
        """Test audio speeches usage source configuration."""
        source = OpenAISource()

        with patch.object(source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []
            source.get_sources(self.start_date, self.end_date)

            called_args = mock_validate.call_args[0][0]
            audio_speeches_source = called_args[3]

            assert audio_speeches_source["name"] == "audio_speeches_usage"
            assert (
                audio_speeches_source["config"]["endpoint"]["path"]
                == "/organization/usage/audio_speeches"
            )

    def test_get_sources_audio_transcriptions_usage(self):
        """Test audio transcriptions usage source configuration."""
        source = OpenAISource()

        with patch.object(source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []
            source.get_sources(self.start_date, self.end_date)

            called_args = mock_validate.call_args[0][0]
            audio_transcriptions_source = called_args[4]

            assert audio_transcriptions_source["name"] == "audio_transcriptions_usage"
            assert (
                audio_transcriptions_source["config"]["endpoint"]["path"]
                == "/organization/usage/audio_transcriptions"
            )

    def test_get_sources_moderations_usage(self):
        """Test moderations usage source configuration."""
        source = OpenAISource()

        with patch.object(source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []
            source.get_sources(self.start_date, self.end_date)

            called_args = mock_validate.call_args[0][0]
            moderations_source = called_args[5]

            assert moderations_source["name"] == "moderations_usage"
            assert (
                moderations_source["config"]["endpoint"]["path"]
                == "/organization/usage/moderations"
            )

    def test_get_sources_inherits_from_base_source(self):
        """Test that OpenAISource inherits from BaseSource."""
        source = OpenAISource()
        assert isinstance(source, BaseSource)

    def test_get_sources_calls_validate_source_configs(self):
        """Test that get_sources calls validate_source_configs."""
        source = OpenAISource()

        with patch.object(source, "validate_source_configs") as mock_validate:
            expected_return = [{"validated": True}]
            mock_validate.return_value = expected_return

            result = source.get_sources(self.start_date, self.end_date)

            assert result == expected_return
            mock_validate.assert_called_once()

    def test_get_sources_all_rest_api_type(self):
        """Test that all sources use rest_api type."""
        source = OpenAISource()

        with patch.object(source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []
            source.get_sources(self.start_date, self.end_date)

            called_args = mock_validate.call_args[0][0]

            for source_config in called_args:
                assert source_config["source_type"] == "rest_api"

    def test_get_sources_all_have_data_selector(self):
        """Test that all sources have data selector."""
        source = OpenAISource()

        with patch.object(source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []
            source.get_sources(self.start_date, self.end_date)

            called_args = mock_validate.call_args[0][0]

            for source_config in called_args:
                assert source_config["config"]["data_selector"] == "data"

    def test_get_sources_all_have_primary_key(self):
        """Test that all sources have consistent primary key."""
        source = OpenAISource()

        with patch.object(source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []
            source.get_sources(self.start_date, self.end_date)

            called_args = mock_validate.call_args[0][0]
            expected_primary_key = ["bucket_start_time", "model", "api_key_id"]

            for source_config in called_args:
                assert source_config["config"]["primary_key"] == expected_primary_key

    def test_get_sources_all_use_get_method(self):
        """Test that all sources use GET method."""
        source = OpenAISource()

        with patch.object(source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []
            source.get_sources(self.start_date, self.end_date)

            called_args = mock_validate.call_args[0][0]

            for source_config in called_args:
                assert source_config["config"]["endpoint"]["method"] == "GET"

    def test_get_sources_parameters_isolation(self):
        """Test that parameters are isolated between sources."""
        source = OpenAISource()

        with patch.object(source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []
            source.get_sources(self.start_date, self.end_date)

            called_args = mock_validate.call_args[0][0]

            params1 = called_args[0]["config"]["endpoint"]["params"]
            params2 = called_args[1]["config"]["endpoint"]["params"]

            assert params1 is not params2
            assert params1 == params2

    @pytest.mark.parametrize(
        "start_date,end_date,expected_start,expected_end",
        [
            (
                datetime(2024, 1, 1, 0, 0, 0),
                datetime(2024, 1, 31, 23, 59, 59),
                int(datetime(2024, 1, 1, 0, 0, 0).timestamp()),
                int(datetime(2024, 1, 31, 23, 59, 59).timestamp()),
            ),
            (
                datetime(2023, 12, 25, 12, 30, 45),
                datetime(2024, 1, 5, 18, 15, 30),
                int(datetime(2023, 12, 25, 12, 30, 45).timestamp()),
                int(datetime(2024, 1, 5, 18, 15, 30).timestamp()),
            ),
        ],
    )
    def test_timestamp_conversion_accuracy(
        self, start_date, end_date, expected_start, expected_end
    ):
        """Test timestamp conversion accuracy for different dates."""
        source = OpenAISource()

        with patch.object(source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []
            source.get_sources(start_date, end_date)

            called_args = mock_validate.call_args[0][0]
            first_source = called_args[0]
            params = first_source["config"]["endpoint"]["params"]

            assert params["start_time"] == expected_start
            assert params["end_time"] == expected_end

    def test_source_endpoint_paths(self):
        """Test all source endpoint paths are correct."""
        source = OpenAISource()

        with patch.object(source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []
            source.get_sources(self.start_date, self.end_date)

            called_args = mock_validate.call_args[0][0]

            expected_paths = [
                "/organization/usage/completions",
                "/organization/usage/embeddings",
                "/organization/usage/images",
                "/organization/usage/audio_speeches",
                "/organization/usage/audio_transcriptions",
                "/organization/usage/moderations",
            ]

            actual_paths = [s["config"]["endpoint"]["path"] for s in called_args]

            assert actual_paths == expected_paths

    def test_bucket_width_parameter(self):
        """Test bucket_width parameter is set correctly."""
        source = OpenAISource()

        with patch.object(source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []
            source.get_sources(self.start_date, self.end_date)

            called_args = mock_validate.call_args[0][0]

            for source_config in called_args:
                params = source_config["config"]["endpoint"]["params"]
                assert params["bucket_width"] == "1d"

    def test_group_by_parameter(self):
        """Test group_by parameter is set correctly."""
        source = OpenAISource()

        with patch.object(source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []
            source.get_sources(self.start_date, self.end_date)

            called_args = mock_validate.call_args[0][0]

            for source_config in called_args:
                params = source_config["config"]["endpoint"]["params"]
                assert params["group_by"] == ["model", "api_key_id"]

    def test_limit_parameter(self):
        """Test limit parameter is set correctly."""
        source = OpenAISource()

        with patch.object(source, "validate_source_configs") as mock_validate:
            mock_validate.return_value = []
            source.get_sources(self.start_date, self.end_date)

            called_args = mock_validate.call_args[0][0]

            for source_config in called_args:
                params = source_config["config"]["endpoint"]["params"]
                assert params["limit"] == 30
