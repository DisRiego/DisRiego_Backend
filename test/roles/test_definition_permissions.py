import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal

client = TestClient(app)

@pytest.fixture(scope="function")
def setup_db():
    """Fixture para configurar la base de datos y hacer rollback después de cada prueba"""
    db = SessionLocal()
    db.begin()
    yield db
    db.rollback()
    db.close()

def test_create_permission(setup_db):
    response = client.post("/roles/permissions/", json={
        "name": "edit_user",
        "description": "Edit User Permissions",
        "category": "User Management"
    })
    assert response.status_code == 200
    assert "El permiso se ha creado correctamente" in response.json()["data"]

def test_create_permission_with_existing_name(setup_db):
    # Intentar crear un permiso con el mismo nombre debería devolver un error
    client.post("/roles/permissions/", json={
        "name": "edit_user",
        "description": "Edit User Permissions",
        "category": "User Management"
    })
    
    response = client.post("/roles/permissions/", json={
        "name": "edit_user",
        "description": "Duplicate permission",
        "category": "User Management"
    })
    assert response.status_code == 400
    assert response.json()["detail"]["data"] == "El permiso ya existe asignado a ese nombre"
    assert response.json()["detail"]["success"] == False
