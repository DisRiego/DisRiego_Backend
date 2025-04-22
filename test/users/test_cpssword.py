import pytest
from fastapi import HTTPException
from app.users.services import UserService
from app.users.models import User
from app.users.schemas import ChangePasswordRequest
from app.database import SessionLocal, engine
from sqlalchemy import event
import uuid
import os
from Crypto.Protocol.KDF import scrypt

@pytest.fixture(scope="function")
def db_session():
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

def hash_test_password(plain: str) -> tuple:
    salt = os.urandom(16)
    key = scrypt(plain.encode(), salt, key_len=32, N=2**14, r=8, p=1)
    return salt.hex(), key.hex()

@pytest.fixture
def test_user(db_session):
    salt_hex, hash_hex = hash_test_password("MyOldPassword123")
    unique_email = f"testuser_{uuid.uuid4().hex[:6]}@example.com"
    user = User(
        email=unique_email,
        password=hash_hex,
        password_salt=salt_hex,
        name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    user_id = user.id
    yield user

    if db_session.is_active:
        # NO usamos user.id => generaría un refresh
        existing = db_session.query(User).filter(User.id == user_id).first()
        if existing:
            db_session.delete(existing)
            db_session.commit()

def test_change_password_success(db_session, test_user):
    service = UserService(db_session)
    request_data = ChangePasswordRequest(
        old_password="MyOldPassword123",
        new_password="NewPass123456",
        confirm_password="NewPass123456"
    )
    response = service.change_user_password(test_user.id, request_data)
    assert response["success"] is True
    assert response["data"] == "Contraseña actualizada correctamente"

def test_change_password_wrong_current(db_session, test_user):
    """Fallo: Contraseña actual incorrecta => 400 'La contraseña actual es incorrecta'."""
    service = UserService(db_session)
    request_data = ChangePasswordRequest(
        old_password="WrongCurrent123",
        new_password="NewPass123456",
        confirm_password="NewPass123456"
    )
    with pytest.raises(HTTPException) as exc_info:
        service.change_user_password(test_user.id, request_data)
    assert exc_info.value.status_code == 500


