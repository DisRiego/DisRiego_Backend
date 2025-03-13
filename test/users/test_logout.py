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

@pytest.fixture()
def auth_token(client, test_user):
    """Obtener un token de autenticación válido para pruebas"""
    response = client.post("/auth/login/", json={
        "email": test_user.email,
        "password": "TestPassword123"
    })
    assert response.status_code == 200
    return response.json()["access_token"]

def test_logout_success(client, auth_token):
    """✅ Prueba de logout exitoso"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.post("/auth/logout", headers=headers)
    
    assert response.status_code == 200
    assert response.json()["message"] == "Cierre de sesión exitoso"

def test_logout_invalid_token(client):
    """❌ Prueba de logout con token inválido"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.post("/auth/logout", headers=headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "Token inválido"

def test_logout_no_token(client):
    """❌ Prueba de logout sin enviar token"""
    response = client.post("/auth/logout")

    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]
