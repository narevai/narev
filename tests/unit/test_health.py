def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data
    assert "version" in data
