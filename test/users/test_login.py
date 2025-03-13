import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.users.models import User
from app.auth.services import AuthService
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
def auth_service(db):
    """Instancia del servicio de autenticación para pruebas"""
    return AuthService(db)

@pytest.fixture()
def test_user(db):
    """Crear un usuario de prueba en la base de datos"""
    email = "testuser@example.com"
    password = "TestPassword123"
    
    auth_service = AuthService(db)
    salt, hashed_password = auth_service.hash_password(password)
    
    user = User(email=email, password=hashed_password, password_salt=salt)
    db.add(user)
    db.commit()
    db.refresh(user)

    yield user

    # Limpieza de usuario de prueba después del test
    db.query(User).filter(User.email == email).delete()
    db.commit()

def test_login_success(client, test_user):
    """✅ Prueba de inicio de sesión exitoso"""
    response = client.post("/auth/login/", json={
        "email": test_user.email,
        "password": "TestPassword123"
    })

    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    assert json_data["token_type"] == "bearer"

def test_login_invalid_password(client, test_user):
    """❌ Prueba de inicio de sesión con contraseña incorrecta"""
    response = client.post("/auth/login/", json={
        "email": test_user.email,
        "password": "WrongPassword123"
    })

    assert response.status_code == 401
    assert "Credenciales inválidas" in response.json()["detail"]

def test_login_non_existent_user(client):
    """❌ Prueba de inicio de sesión con un usuario inexistente"""
    response = client.post("/auth/login/", json={
        "email": "nonexistent@example.com",
        "password": "SomePassword123"
    })

    assert response.status_code == 401  # Adaptado a la respuesta actual del backend
    assert "Usuario no encontrado" in response.json()["detail"]
