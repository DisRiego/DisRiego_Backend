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

def test_update_role_permissions(setup_db):
    role_id = 1  # Asegúrate de que este ID corresponde a un rol existente en la base de datos
    new_permissions = [2, 3]
    
    response = client.put(f"/roles/{role_id}/permissions", json={"permissions": new_permissions})
    assert response.status_code == 200
    assert "Permisos actualizados correctamente" in response.json()["message"]

def test_update_role_permissions_with_nonexistent_permission(setup_db):
    role_id = 1  # Asegúrate de que este ID corresponde a un rol existente en la base de datos
    new_permissions = [999]  # ID de permiso inexistente
    
    response = client.put(f"/roles/{role_id}/permissions", json={"permissions": new_permissions})
    assert response.status_code == 400
    assert "Los siguientes permisos no existen" in response.json()["detail"]["data"]
    
def test_update_role_permissions_with_nonexistent_rol(setup_db):
    role_id = 15  # Asegúrate de que este ID corresponde a un rol inexistente en la base de datos
    new_permissions = [999]  # ID de permiso inexistente
    
    response = client.put(f"/roles/{role_id}/permissions", json={"permissions": new_permissions})
    assert response.status_code == 404
    assert "Rol no encontrado." in response.json()["detail"]["data"]