import pytest
from fastapi.testclient import TestClient
from app.main import app  # Asegúrate de que este sea el nombre correcto de tu aplicación FastAPI

client = TestClient(app)

def test_create_permission():
    response = client.post("/roles/permissions/", json={
        "name": "edit_user", 
        "description": "Edit User Permissions", 
        "category": "User Management"
    })
    assert response.status_code == 200
    assert "edit_user" in response.json()["name"]
