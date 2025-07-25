"""
Tests for main FastAPI application endpoints
"""


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data
    assert "version" in data


def test_api_root_endpoint(client):
    """Test the API root endpoint."""
    response = client.get("/api/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Hello from NarevAI API! 🚀"
    assert data["status"] == "working"


def test_api_test_endpoint(client):
    """Test the API test endpoint."""
    response = client.get("/api/test")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Test endpoint working!"
    assert data["data"] == ["item1", "item2", "item3"]
    assert data["timestamp"] == "2025-01-15T10:30:00Z"


def test_nonexistent_api_endpoint(client):
    """Test that non-existent API endpoints return 404."""
    response = client.get("/api/nonexistent")
    assert response.status_code == 404


def test_cors_headers(client):
    """Test that CORS headers are properly set."""
    # Send a request with Origin header to trigger CORS
    response = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    # In test environment, CORS should allow localhost:3000
    assert "access-control-allow-origin" in response.headers
