import pytest
from fastapi import HTTPException
from datetime import datetime, timedelta, timezone
from app.users.models import User, PasswordReset
from app.users.services import UserService
import uuid
from app.database import SessionLocal, engine
from sqlalchemy import event

@pytest.fixture(scope="function")
def db_session():
    """Crea una sesión de prueba con rollback"""
    connection = engine.connect()
    trans = connection.begin()
    session = SessionLocal(bind=connection)
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, trans_inner):
        if trans_inner.nested and not trans_inner.parent:
            session.begin_nested()

    yield session
    session.rollback()
    session.close()
    trans.rollback()
    connection.close()

@pytest.fixture
def test_user(db_session):
    """Crea un usuario de prueba y lo elimina al finalizar"""
    unique_email = f"testuser_{uuid.uuid4().hex[:6]}@example.com"
    user = User(
        email=unique_email,
        password="hashedpassword",
        password_salt="randomsalt",
        name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    yield user

    if db_session.query(User).filter(User.id == user.id).first():
        db_session.delete(user)
        db_session.commit()

@pytest.fixture
def expired_token(db_session, test_user):
    token = PasswordReset(
        email=test_user.email,
        token=str(uuid.uuid4()),
        expiration=datetime.utcnow() - timedelta(hours=1)  # naive
    )
    db_session.add(token)
    db_session.commit()
    yield token
    db_session.delete(token)
    db_session.commit()

@pytest.fixture
def valid_token(db_session, test_user):
    token = PasswordReset(
        email=test_user.email,
        token=str(uuid.uuid4()),
        expiration=datetime.utcnow() + timedelta(hours=1)  # naive
    )
    db_session.add(token)
    db_session.commit()
    yield token
    db_session.delete(token)
    db_session.commit()

def test_reset_password_success(db_session, valid_token):
    """Caso éxito: Se restablece la contraseña con un token válido"""
    service = UserService(db_session)
    # Llamamos con solo 2 parámetros (no confirm_password)
    response = service.update_password(valid_token.token, "NewPass123456")
    assert response["message"] == "Contraseña actualizada correctamente"

def test_reset_password_expired_token(db_session, expired_token):
    """Caso fallo: Se intenta restablecer la contraseña con un token expirado"""
    service = UserService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        service.update_password(expired_token.token, "NewPass123456")
    assert exc_info.value.status_code == 400
    assert "El token ha expirado" in exc_info.value.detail

def test_reset_password_invalid_token(db_session):
    """Caso fallo: Se intenta restablecer la contraseña con un token inválido"""
    service = UserService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        service.update_password("invalid_token", "NewPass123456")
    # La lógica lanza 404 si el token no existe
    assert exc_info.value.status_code == 404
    assert "Token inválido" in exc_info.value.detail

def test_reset_password_mismatch_passwords(db_session, valid_token):
    """Caso fallo: Se intenta restablecer la contraseña con new_password y confirm_password diferentes"""
    service = UserService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        # Llamamos con 3 parámetros
        service.update_password(valid_token.token, "NewPass123456", "DifferentPass123456")
    # Lanza 400 si las contraseñas no coinciden
    assert exc_info.value.status_code == 400
    assert "Las contraseñas no coinciden" in exc_info.value.detail
