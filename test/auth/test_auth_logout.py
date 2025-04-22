import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.main import app
from app.database import get_db
from app.auth.services import AuthService
from app.auth.models import RevokedToken
from app.users.models import User

client = TestClient(app)

@pytest.fixture
def db_session():
    """Fixture para obtener una sesión de base de datos"""
    session = next(get_db())
    yield session
    session.close()

@pytest.fixture
def create_test_user(db_session: Session):
    """Crea un usuario de prueba y lo limpia después de la prueba"""
    auth_service = AuthService(db_session)
    password_salt, password_hash = auth_service.hash_password("TestPassword123!")

    # Verifica si el usuario ya existe y lo borra antes de crearlo
    existing_user = db_session.query(User).filter_by(email="testuser123456789@example.com").first()
    if existing_user:
        db_session.delete(existing_user)
        db_session.commit()

    user = User(
        email="testuser123456789@example.com",
        password=password_hash,
        password_salt=password_salt,
        status_id=1,  
        email_status=True,
        first_login_complete=True
    )

    db_session.add(user)
    db_session.commit()
    yield user  

    # 🔴 Elimina el usuario de prueba después de la prueba
    db_session.delete(user)
    db_session.commit()

@pytest.fixture
def create_token(db_session: Session, create_test_user):
    """Crea un token de prueba y lo borra después de la prueba"""
    auth_service = AuthService(db_session)
    token_data = {
        "sub": create_test_user.email,
        "id": create_test_user.id,
        "email": create_test_user.email,
        "exp": datetime.utcnow() + timedelta(minutes=10),
    }
    token = auth_service.create_access_token(data=token_data)
    
    yield token  # Devuelve el token para usar en la prueba

    # 🔴 Limpia los tokens de la base de datos después de la prueba
    db_session.query(RevokedToken).filter(RevokedToken.token == token).delete()
    db_session.commit()

def test_logout_successful(db_session, create_token):
    """Prueba de cierre de sesión exitoso"""
    response = client.post("/auth/logout", headers={"Authorization": f"Bearer {create_token}"})
    assert response.status_code == 200
    assert response.json()["message"] == "Cierre de sesión exitoso"

    # Verificar que el token fue revocado
    revoked_token = db_session.query(RevokedToken).filter_by(token=create_token).first()
    assert revoked_token is not None

def test_reuse_revoked_token(db_session, create_token):
    """Prueba de intento de uso de un token revocado"""
    
    # Cerrar sesión con el token válido
    client.post("/auth/logout", headers={"Authorization": f"Bearer {create_token}"})

    # Intentar acceder a una ruta protegida usando el token revocado
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {create_token}"})  # Usa una ruta protegida real
    
    assert response.status_code == 404


def test_invalid_token():
    """Prueba de cierre de sesión con un token inválido"""
    response = client.post("/auth/logout", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Token inválido"
