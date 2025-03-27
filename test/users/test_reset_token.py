import pytest
from fastapi import HTTPException
from app.users.models import User
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

def test_generate_reset_token_success(db_session, test_user):
    """Caso éxito: Se genera un token de restablecimiento con un email válido"""
    service = UserService(db_session)
    token = service.generate_reset_token(test_user.email)
    assert token is not None
    assert isinstance(token, str)

def test_generate_reset_token_failure(db_session):
    """Caso fallo: Se intenta generar un token con un email inexistente"""
    service = UserService(db_session)
    
    with pytest.raises(HTTPException) as exc_info:
        service.generate_reset_token("nonexistent@example.com")
    
    # Verificar que la excepción es correcta
    assert exc_info.value.status_code == 404, f"Expected 404, got {exc_info.value.status_code}"
    assert "Usuario no encontrado" in exc_info.value.detail, f"Expected error message to contain 'Usuario no encontrado', got {exc_info.value.detail}"
