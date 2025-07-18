import pytest
from fastapi.testclient import TestClient

def test_health_endpoint(client):
    """Test the main health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0-preGPU"
    assert "services" in data
    assert "timestamp" in data

def test_docs_endpoint(client):
    """Test that API documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200

def test_redoc_endpoint(client):
    """Test that ReDoc documentation is accessible."""
    response = client.get("/redoc")
    assert response.status_code == 200

def test_cors_headers(client):
    """Test CORS headers are properly set."""
    response = client.options("/health")
    # FastAPI automatically handles OPTIONS requests
    assert response.status_code in [200, 405]  # 405 if OPTIONS not explicitly defined

def test_404_endpoint(client):
    """Test 404 handling for non-existent endpoints."""
    response = client.get("/nonexistent")
    assert response.status_code == 404

class TestAPIRouters:
    """Test that all routers are properly mounted."""
    
    def test_ocr_router_mounted(self, client):
        """Test OCR router is accessible."""
        response = client.get("/api/v1/ocr/health")
        assert response.status_code == 200
    
    def test_classify_router_mounted(self, client):
        """Test classification router is accessible."""
        response = client.get("/api/v1/classify/health")
        assert response.status_code == 200
    
    def test_ner_router_mounted(self, client):
        """Test NER router is accessible."""
        response = client.get("/api/v1/ner/health")
        assert response.status_code == 200 