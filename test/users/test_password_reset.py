import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.users.models import User, PasswordReset
from app.users import schemas
import uuid
from datetime import datetime, timedelta
from passlib.context import CryptContext


# Configuración para el hashing de contraseñas (usamos scrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.fixture(scope="module")
def db():
    """Fixture para crear una nueva sesión de base de datos para las pruebas"""
    db = SessionLocal()
    db.begin()
    yield db
    db.rollback()
    db.close()


@pytest.fixture()
def test_user(db):
    """Fixture para crear un usuario de prueba"""
    existing_user = db.query(User).filter(User.email == "test@example.com").first()
    if existing_user:
        return existing_user
    
    # Crear un usuario de prueba si no existe
    user = User(
        email="test@example.com",
        name="Test User",
    )
    user.hashed_password = "testpassword"  # Generar el hash de la contraseña
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def generate_reset_token(db, test_user):
    """Generar un token de restablecimiento de contraseña para las pruebas"""
    token = str(uuid.uuid4())
    password_reset = PasswordReset(
        email=test_user.email, token=token, expiration=datetime.utcnow() + timedelta(hours=1)
    )
    db.add(password_reset)
    db.commit()
    db.refresh(password_reset)
    return token, password_reset


@pytest.fixture()
def expired_reset_token(db, test_user):
    """Crear un token expirado para las pruebas"""
    token = str(uuid.uuid4())
    password_reset = PasswordReset(
        email=test_user.email, token=token, expiration=datetime.utcnow() - timedelta(hours=1)
    )
    db.add(password_reset)
    db.commit()
    db.refresh(password_reset)
    return token, password_reset


@pytest.fixture()
def client():
    """Crear una instancia del cliente de pruebas"""
    return TestClient(app)


# Test: Solicitar restablecimiento de contraseña
def test_request_reset_password(client: TestClient, db, test_user):
    response = client.post(
        "/users/request-reset-password",
        json={"email": test_user.email}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Reset link generated", "token": response.json()["token"]}


# Test: Restablecer contraseña con un token válido
def test_reset_password(client: TestClient, db, test_user, generate_reset_token):
    token, _ = generate_reset_token
    new_password = "newpassword123"
    
    response = client.post(
        f"/users/reset-password/{token}",
        json={"token": token, "new_password": new_password}
    )
    
    assert response.status_code == 200
    assert response.json() == {"message": "Password successfully updated", "token": token}
    


# Test: Intentar restablecer la contraseña con un token inválido
def test_reset_password_invalid_token(client: TestClient, db, test_user):
    invalid_token = str(uuid.uuid4())  # Un token que no existe
    response = client.post(
        f"/users/reset-password/{invalid_token}",
        json={"token": invalid_token, "new_password": "newpassword123"}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Invalid or expired token"}


# Test: Intentar restablecer la contraseña con un token expirado
def test_reset_password_expired_token(client: TestClient, db, expired_reset_token):
    token, _ = expired_reset_token
    response = client.post(
        f"/users/reset-password/{token}",
        json={"token": token, "new_password": "newpassword123"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Token expired"}
