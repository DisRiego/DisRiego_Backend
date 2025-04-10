import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.auth.services import AuthService
from sqlalchemy.orm import Session
from sqlalchemy.sql import text  # Importar `text` para consultas en SQLAlchemy
from app.users.models import User, Status  # Asegurar que `Status` está correcto

client = TestClient(app)

@pytest.fixture
def db_session():
    """Fixture para obtener una sesión de base de datos"""
    session = next(get_db())
    yield session
    session.close()

@pytest.fixture
def ensure_status_exists(db_session: Session):
    """Asegura que los estados requeridos existan antes de la prueba"""
    required_statuses = [
        (0, "Inactivo"),
        (1, "Activo")
    ]
    for status_id, status_name in required_statuses:
        status = db_session.query(Status).filter_by(id=status_id).first()
        if not status:
            db_session.add(Status(id=status_id, name=status_name))
    db_session.commit()

@pytest.fixture
def create_test_user(db_session: Session, ensure_status_exists):
    """Crea un usuario de prueba en la base de datos y lo elimina después de la prueba"""
    auth_service = AuthService(db_session)
    password_salt, password_hash = auth_service.hash_password("TestPassword123!")

    existing_user = db_session.query(User).filter_by(email="testemail123456789@example.com").first()
    if existing_user:
        db_session.execute(
            text("DELETE FROM activation_tokens WHERE user_id = :user_id"),  # 🔹 Se usa `text()`
            {"user_id": existing_user.id}
        )
        db_session.delete(existing_user)
        db_session.commit()

    user = User(
        email="testemail123456789@example.com",
        password=password_hash,
        password_salt=password_salt,
        status_id=1,
        email_status=True,
        first_login_complete=True
    )

    db_session.add(user)
    db_session.commit()

    yield user  # Devuelve el usuario para ser usado en la prueba

    db_session.execute(
        text("DELETE FROM activation_tokens WHERE user_id = :user_id"),  # 🔹 Se usa `text()`
        {"user_id": user.id}
    )
    db_session.delete(user)
    db_session.commit()

def test_login_successful(create_test_user):
    """Prueba de inicio de sesión exitoso con credenciales correctas"""
    response = client.post("/auth/login/", json={"email": "testemail123456789@example.com", "password": "TestPassword123!"})
    assert response.status_code == 200
    json_response = response.json()
    assert "access_token" in json_response
    assert json_response["token_type"] == "bearer"

def test_login_invalid_email():
    """Prueba de inicio de sesión con un correo incorrecto"""
    response = client.post("/auth/login/", json={"email": "wronguser@example.com", "password": "TestPassword123!"})
    assert response.status_code == 401
    assert "Usuario no encontrado" in response.json()["detail"]

def test_login_invalid_password(create_test_user):
    """Prueba de inicio de sesión con una contraseña incorrecta"""
    response = client.post("/auth/login/", json={"email": "testemail123456789@example.com", "password": "WrongPassword!"})
    assert response.status_code == 401
    assert "Credenciales inválidas" in response.json()["detail"]

def test_login_inactive_account(db_session, create_test_user):
    """Prueba de inicio de sesión con una cuenta inactiva"""
    create_test_user.status_id = 0  # Cambiar el estado a inactivo
    db_session.commit()

    response = client.post("/auth/login/", json={"email": "testemail123456789@example.com", "password": "TestPassword123!"})
    assert response.status_code == 401
    assert "Cuenta inactiva" in response.json()["detail"]

def test_login_unverified_email(db_session, create_test_user):
    """Prueba de inicio de sesión con una cuenta no verificada"""
    create_test_user.email_status = False  # Cambiar el estado a no verificado
    db_session.commit()

    response = client.post("/auth/login/", json={"email": "testemail123456789@example.com", "password": "TestPassword123!"})
    assert response.status_code == 401

    # 🔹 Corrección: Acceder a `detail["message"]` en lugar de `message`
    assert "Cuenta no activada" in response.json()["detail"]["message"]


