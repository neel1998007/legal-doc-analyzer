"""
Tests for authentication endpoints
"""
import pytest
from fastapi.testclient import TestClient

class TestAuthEndpoints:
    """Test authentication functionality"""
    
    def test_register_new_user(self, client: TestClient):
        """Test user registration"""
        user_data = {
            "email": "newuser@example.com",
            "password": "newpass123",
            "full_name": "New User"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_register_duplicate_email(self, client: TestClient, test_user):
        """Test registration with existing email fails"""
        user_data = {
            "email": test_user["email"],  # Use dict access
            "password": "newpass123",
            "full_name": "Duplicate User"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email"""
        user_data = {
            "email": "invalid-email",
            "password": "testpass123",
            "full_name": "Test User"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 422

    def test_login_success(self, client: TestClient, test_user, test_user_data):
        """Test successful login"""
        login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
        
        response = client.post("/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 50

    def test_login_wrong_password(self, client: TestClient, test_user, test_user_data):
        """Test login with wrong password"""
        login_data = {
            "username": test_user_data["email"],
            "password": "wrongpassword"
        }
        
        response = client.post("/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user"""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "somepassword"
        }
        
        response = client.post("/auth/login", data=login_data)
        
        assert response.status_code == 401

    def test_get_current_user(self, client: TestClient, test_user, auth_headers):
        """Test getting current user info"""
        response = client.get("/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user["email"]  # Use dict access
        assert data["full_name"] == test_user["full_name"]  # Use dict access
        assert data["is_active"] is True

    def test_get_current_user_no_token(self, client: TestClient):
        """Test getting current user without token"""
        response = client.get("/auth/me")
        
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401

    def test_auth_test_endpoint(self, client: TestClient, test_user, auth_headers):
        """Test protected auth test endpoint"""
        response = client.get("/auth/test-auth", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "Hello" in data["message"]
        assert data["authenticated"] is True
        assert "user_id" in data