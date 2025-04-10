import pytest
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy import event
from app.database import SessionLocal, engine
from app.users.models import User, ActivationToken
from app.users.services import UserService

@pytest.fixture(scope="function")
def db_session():
    """
    Crea una sesión de prueba con rollback.
    """
    connection = engine.connect()
    trans = connection.begin()
    session = SessionLocal(bind=connection)
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, trans_inner):
        if trans_inner.nested and not trans_inner.parent:
            session.begin_nested()

    yield session

    if session.is_active:
        session.rollback()
    session.close()
    trans.rollback()
    connection.close()

@pytest.fixture
def non_activated_user(db_session):
    """
    Crea un usuario NO activado con estado 'Pendiente'.
    """
    user = User(
        email=f"nonactivated_{uuid.uuid4().hex[:6]}@example.com",
        password="somehashed",
        password_salt="somesalt",
        name="UserNotActivated",
        status_id=2,  # Pendiente
        email_status=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    yield user

    if db_session.is_active:
        db_session.delete(user)
        db_session.commit()

@pytest.fixture
def valid_activation_token(db_session, non_activated_user):
    """
    Crea un token de activación válido para el usuario NO activado.
    """
    db_session.refresh(non_activated_user)  # 🔹 Asegura que el usuario tiene un ID antes de crear el token
    assert non_activated_user.id is not None, "El usuario debe tener un ID antes de crear el token"

    token_str = str(uuid.uuid4())
    expiration = datetime.now(timezone.utc) + timedelta(days=7)
    
    token = ActivationToken(
        token=token_str,
        user_id=non_activated_user.id,  # 🚀 Se asegura de que tenga un user_id
        expires_at=expiration,
        used=False
    )

    db_session.add(token)
    db_session.commit()
    yield token_str

    if db_session.is_active:
        db_session.delete(token)
        db_session.commit()


def test_resend_activation_token_already_activated(db_session):
    """
    Verifica que un usuario YA activado NO pueda recibir un nuevo token.
    """
    user = User(
        email=f"activated_{uuid.uuid4().hex[:6]}@example.com",
        password="somehashed",
        password_salt="somesalt",
        name="UserActivated",
        status_id=1,  # Activo
        email_status=True
    )
    db_session.add(user)
    db_session.commit()

    service = UserService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        service.resend_activation_token(user)  # Sin await si no es async

    assert exc_info.value.status_code == 400
    assert "Usuario ya activado" in exc_info.value.detail

    db_session.delete(user)
    db_session.commit()

@pytest.mark.asyncio
async def test_activate_account_success(db_session, non_activated_user, valid_activation_token):
    """
    Verifica que un usuario pueda activar su cuenta con un token válido.
    """
    service = UserService(db_session)
    response = await service.activate_account(valid_activation_token)

    assert response.success is True
    assert "activada con éxito" in response.message

    token_obj = db_session.query(ActivationToken).filter_by(token=valid_activation_token).first()
    assert token_obj.used is True

    db_session.refresh(non_activated_user)
    assert non_activated_user.email_status is True
    assert non_activated_user.status_id == 1

@pytest.mark.asyncio
async def test_activate_account_invalid_token(db_session):
    """
    Verifica que no se pueda activar con un token inexistente.
    """
    service = UserService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await service.activate_account("invalid_token")

    assert exc_info.value.status_code == 500  
    assert "inválido o expirado" in exc_info.value.detail
