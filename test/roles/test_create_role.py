import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal

client = TestClient(app)

@pytest.fixture(scope="function")
def setup_db():
    """Fixture para configurar la base de datos y hacer rollback después de cada prueba"""
    # Aquí puedes configurar la base de datos y hacer rollback después de cada prueba.
    db = SessionLocal()
    db.begin()
    yield db
    db.rollback()
    db.close()

def test_create_role(setup_db):
    response = client.post("/roles/", json={
        "name": "admin",
        "description": "Admin role",
        "permissions": [1, 2]
    })
    assert response.status_code == 200
    assert response.json()["name"] == "admin"
    assert "permissions" in response.json()
    assert len(response.json()["permissions"]) > 0

        

def test_create_role_with_existing_name(setup_db):
    # Intentar crear un rol con el mismo nombre debería devolver un error
    client.post("/roles/", json={
        "name": "admin",
        "description": "Admin role",
        "permissions": [1, 2]
    })
    
    response = client.post("/roles/", json={
        "name": "admin",
        "description": "Admin role duplicate",
        "permissions": [2, 3]
    })
    assert response.status_code == 400
    assert response.json()["detail"]["data"] == "El rol ya existe."
    assert response.json()["detail"]["success"] == False
