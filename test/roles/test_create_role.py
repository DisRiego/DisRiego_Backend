import pytest
from fastapi.testclient import TestClient
from app.main import app  # Asegúrate de que este sea el nombre correcto de tu aplicación FastAPI

client = TestClient(app)

def test_create_role():
    response = client.post("/roles/", json={"name": "admin", "description": "Admin role", "permissions": [1, 2]})
    assert response.status_code == 200
    assert "admin" in response.json()["name"]
    assert len(response.json()["permissions"]) > 0
