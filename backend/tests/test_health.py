"""
Tests for application health and basic functionality
"""
import pytest
from fastapi.testclient import TestClient

class TestHealthEndpoints:
    """Test health check and basic endpoints"""
    
    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Legal Document Analyzer" in data["message"]
        assert data["status"] == "running"

    def test_health_endpoint(self, client: TestClient):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert "services" in data

    def test_openapi_docs(self, client: TestClient):
        """Test OpenAPI documentation is available"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_json(self, client: TestClient):
        """Test OpenAPI JSON schema"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "Legal Document Analyzer"