import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from app.main import app
from app.database import SessionLocal
from app.users.models import User
from app.users.services import UserService
from sqlalchemy.orm import Session

@pytest.fixture(scope="module")
def db():
    """Fixture para manejar una sesión de base de datos en pruebas"""
    db = SessionLocal()
    db.begin()
    yield db
    db.rollback()
    db.close()

@pytest.fixture()
def client():
    """Cliente de prueba para FastAPI"""
    return TestClient(app)

@pytest.fixture()
def user_service(db):
    """Instancia del servicio de usuario para pruebas"""
    return UserService(db)

@pytest.fixture()
def test_user(db):
    """Crear un usuario de prueba en la base de datos"""
    email = "testuser@example.com"
    user = User(
        email=email,
        name="Test",
        first_last_name="User",
        second_last_name="Example"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    yield user

    # Limpieza de usuario de prueba después del test
    db.query(User).filter(User.email == email).delete()
    db.commit()

def test_update_user_success(user_service, test_user, db):
    """✅ Prueba de actualización exitosa de usuario"""
    user_id = test_user.id
    new_data = {"name": "Updated Name", "phone": "1234567890"}

    response = user_service.update_user(user_id, **new_data)

    assert response["success"] is True
    assert response["data"] == "Usuario actualizado correctamente"

    # Verificar que los cambios se reflejan en la base de datos
    updated_user = db.query(User).filter(User.id == user_id).first()
    assert updated_user.name == "Updated Name"
    assert updated_user.phone == "1234567890"

def test_update_nonexistent_user(user_service):
    """❌ Prueba de actualización de un usuario inexistente"""
    user_id = 999999  # Un ID que no existe
    new_data = {"name": "New Name"}

    with pytest.raises(HTTPException) as exc_info:
        user_service.update_user(user_id, **new_data)

    assert exc_info.value.status_code == 500
    assert "Usuario no encontrado" in str(exc_info.value.detail)
