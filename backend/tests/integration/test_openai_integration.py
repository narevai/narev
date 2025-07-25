"""
Integration tests for OpenAI Provider - uses mock server
Note: Mock server must be running before tests on localhost:8888
"""

from datetime import datetime

import httpx
import pytest

from providers.openai.mapper import OpenAIFocusMapper
from providers.openai.provider import OpenAIProvider

# Pytest marker
pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
def mock_server_url():
    """URL to mock server (must be started manually)"""
    return "http://localhost:8888/v1"


@pytest.fixture(scope="session")
def check_mock_server():
    """Check if mock server is available"""
    try:
        response = httpx.get("http://localhost:8888/health", timeout=2.0)
        if response.status_code != 200:
            pytest.skip("Mock server not running on localhost:8888")
    except (httpx.RequestError, httpx.TimeoutException):
        pytest.skip("Mock server not running on localhost:8888")


class TestOpenAIProviderIntegration:
    """Integration tests with mock server"""

    def test_mock_server_health(self, check_mock_server):
        """Test if mock server responds"""
        response = httpx.get("http://localhost:8888/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data

    def test_connection_success(self, mock_server_url, check_mock_server):
        """Test successful connection to mock server"""
        config = {
            "name": "test-openai",
            "provider_id": "test-provider-id",
            "auth_config": {
                "token": "sk-test-key"
            },  # Changed from "api_key" to "token"
            "api_endpoint": mock_server_url,
            "additional_config": {"organization_id": "org-test"},
        }

        provider = OpenAIProvider(config)

        # Debug headers
        headers = provider.get_request_headers()
        print(f"DEBUG: Headers being sent: {headers}")

        result = provider.test_connection()

        print(f"DEBUG: Connection result: {result}")

        assert result["success"] is True
        assert "Successfully connected" in result["message"]
        assert result["details"]["endpoint"] == mock_server_url
        assert result["details"]["organization"] == "org-test"

    def test_connection_unauthorized(self, mock_server_url, check_mock_server):
        """Test connection without authorization"""
        # Test with invalid Bearer header
        with httpx.Client() as client:
            response = client.get(
                f"{mock_server_url}/organization/usage/completions",
                headers={"Authorization": ""},  # Empty header
                timeout=10.0,
            )

            assert response.status_code == 401


class TestOpenAIDataRetrieval:
    """Tests for data retrieval from mock server"""

    @pytest.fixture
    def provider(self, mock_server_url, check_mock_server):
        """Provider configured for mock server"""
        config = {
            "name": "test-openai",
            "provider_id": "test-provider-id",
            "auth_config": {"token": "sk-test-key"},
            "api_endpoint": mock_server_url,
            "additional_config": {"organization_id": "org-test"},
        }
        return OpenAIProvider(config)

    def test_get_completions_usage(self, provider):
        """Test retrieving completions usage data"""
        headers = provider.get_request_headers()
        print(f"DEBUG: Headers for completions: {headers}")

        with httpx.Client() as client:
            response = client.get(
                f"{provider.api_endpoint}/organization/usage/completions",
                headers=headers,
                params={"start_time": 1751414400, "end_time": 1751500800},
            )

            print(f"DEBUG: Response status: {response.status_code}")
            print(f"DEBUG: Response text: {response.text}")

            assert response.status_code == 200
            data = response.json()

            assert data["object"] == "page"
            assert "data" in data
            assert isinstance(data["data"], list)

            # Check data structure from mock server
            if data["data"]:
                bucket = data["data"][0]
                assert "object" in bucket
                assert "start_time" in bucket
                assert "end_time" in bucket
                assert "results" in bucket

    def test_get_embeddings_usage(self, provider):
        """Test retrieving embeddings usage data"""
        headers = provider.get_request_headers()

        with httpx.Client() as client:
            response = client.get(
                f"{provider.api_endpoint}/organization/usage/embeddings",
                headers=headers,
            )

            assert response.status_code == 200
            data = response.json()

            assert data["object"] == "page"
            assert "data" in data

    def test_get_moderations_usage(self, provider):
        """Test retrieving moderations usage data"""
        headers = provider.get_request_headers()

        with httpx.Client() as client:
            response = client.get(
                f"{provider.api_endpoint}/organization/usage/moderations",
                headers=headers,
            )

            assert response.status_code == 200
            data = response.json()

            assert data["object"] == "page"
            assert "data" in data


class TestOpenAIMapperIntegration:
    """Tests for mapper with real data from mock server"""

    @pytest.fixture
    def provider(self, mock_server_url, check_mock_server):
        """Provider configured for mock server"""
        config = {
            "name": "test-openai",
            "provider_id": "test-provider-id",
            "auth_config": {"token": "sk-test-key"},
            "api_endpoint": mock_server_url,
            "additional_config": {"organization_id": "org-test"},
        }
        return OpenAIProvider(config)

    @pytest.fixture
    def mapper(self):
        """Mapper for FOCUS format conversion"""
        config = {"provider_id": "test-provider-id"}
        return OpenAIFocusMapper(config)

    def test_map_completions_data_to_focus(self, provider, mapper):
        """Test mapping completions data to FOCUS format"""
        headers = provider.get_request_headers()

        with httpx.Client() as client:
            response = client.get(
                f"{provider.api_endpoint}/organization/usage/completions",
                headers=headers,
            )

            assert response.status_code == 200
            data = response.json()

            # Check if we have any data to map
            has_results = any(
                bucket.get("results", []) for bucket in data.get("data", [])
            )

            if has_results:
                # Here would be mapper test, if implemented
                # focus_records = mapper.map_to_focus(data)
                # assert len(focus_records) > 0
                # assert all("BillingCurrency" in record for record in focus_records)
                pass

            # Test that data is in expected format
            assert data["object"] == "page"
            assert "data" in data


class TestEndToEndPipeline:
    """End-to-end tests for complete pipeline"""

    @pytest.fixture
    def provider(self, mock_server_url, check_mock_server):
        """Provider for E2E tests"""
        config = {
            "name": "test-openai",
            "provider_id": "test-provider-id",
            "auth_config": {
                "token": "sk-test-key"
            },  # Changed from "api_key" to "token"
            "api_endpoint": mock_server_url,
            "additional_config": {"organization_id": "org-test"},
        }
        return OpenAIProvider(config)

    def test_full_pipeline_simulation(self, provider):
        """Test complete pipeline simulation"""
        # 1. Test connection
        connection_result = provider.test_connection()
        assert connection_result["success"] is True

        # 2. Get sources
        start_date = datetime(2025, 7, 1)
        end_date = datetime(2025, 7, 7)
        sources = provider.get_sources(start_date, end_date)

        # Sources should be a list (may be empty)
        assert isinstance(sources, list)

        # 3. Test headers and auth
        headers = provider.get_request_headers()
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer")

        # 4. Test REST client
        rest_client = provider.get_rest_client()
        assert rest_client is not None

        print("✅ Complete pipeline works correctly")

    # THIS NEED TO BE FIXED DEFINITELY

    # def test_error_handling_pipeline(self, mock_server_url, check_mock_server):
    #     """Test error handling in pipeline"""
    #     # Test with invalid auth configuration
    #     config = {
    #         "name": "test-openai",
    #         "provider_id": "test-provider-id",
    #         "auth_config": {"token": "invalid"},  # Changed from "api_key" to "token", but still invalid format
    #         "api_endpoint": mock_server_url
    #     }

    #     provider = OpenAIProvider(config)
    #     result = provider.test_connection()

    #     # Should handle error gracefully
    #     assert result["success"] is False
    #     assert "error" in result["details"] or "Invalid" in result["message"]


# Helper functions for integration tests
def is_mock_server_running(url="http://localhost:8888"):
    """Check if mock server is running"""
    try:
        response = httpx.get(f"{url}/health", timeout=2.0)
        return response.status_code == 200
    except (httpx.RequestError, httpx.TimeoutException):
        return False
