"""Sample test for User API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data


def test_create_user():
    """Test creating a new user."""
    user_data = {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "bio": "Test user bio",
    }
    
    response = client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == user_data["email"]
    assert data["data"]["first_name"] == user_data["first_name"]
    
    # Store user ID for other tests
    return data["data"]["id"]


def test_get_all_users():
    """Test getting all users."""
    # First create a user
    test_create_user()
    
    response = client.get("/api/v1/users/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


def test_get_user_by_id():
    """Test getting a user by ID."""
    # First create a user
    user_id = test_create_user()
    
    response = client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == user_id


def test_update_user():
    """Test updating a user."""
    # First create a user
    user_id = test_create_user()
    
    update_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "bio": "Updated bio",
    }
    
    response = client.put(f"/api/v1/users/{user_id}", json=update_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["data"]["first_name"] == update_data["first_name"]


def test_delete_user():
    """Test deleting a user."""
    # First create a user
    user_id = test_create_user()
    
    response = client.delete(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["data"]["deleted"] is True
