import pytest
import uuid
from sqlalchemy import event
from app.database import SessionLocal, engine
from app.users.models import User
from app.users.services import UserService
from app.users.schemas import UserUpdateInfo
from sqlalchemy.exc import InvalidRequestError

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

    yield session  # Se usa como sesión de la base de datos

    try:
        if session.is_active:
            session.rollback()
    except InvalidRequestError:
        pass  # La sesión ya pudo haber sido cerrada
    finally:
        session.close()
        trans.rollback()
        connection.close()

@pytest.fixture
def existing_user(db_session):
    """
    Crea un usuario de prueba en la base de datos.
    """
    user = User(
        email=f"user_{uuid.uuid4().hex[:6]}@example.com",
        password="somehashed",
        password_salt="somesalt",
        name="TestUser",
        status_id=1,  # Activo
        email_status=True,
        country="Colombia",
        department="Antioquia",
        city=1,
        address="Calle falsa 123",
        phone="123456789"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    yield user  # Devuelve el usuario creado para la prueba

    # Solo intenta eliminar el usuario si aún está en la sesión activa
    try:
        if db_session.is_active:
            db_session.delete(user)
            db_session.commit()
    except InvalidRequestError:
        pass  # La sesión ya pudo haber sido cerrada

@pytest.mark.asyncio
async def test_update_profile_success(db_session, existing_user):
    """
    ✅ Caso éxito: Se actualiza el perfil de un usuario con datos válidos.
    """
    service = UserService(db_session)
    update_data = UserUpdateInfo(
        country="Argentina",
        department="Buenos Aires",
        city=2,
        address="Nueva dirección 456",
        phone="987654321"
    )

    response = await service.update_basic_profile(
        user_id=existing_user.id,
        country=update_data.country,
        department=update_data.department,
        city=update_data.city,
        address=update_data.address,
        phone=update_data.phone,
    )

    assert response["success"] is True
    assert "Perfil actualizado" in response["data"]["title"]
    
    db_session.refresh(existing_user)
    assert existing_user.country == "Argentina"
    assert existing_user.department == "Buenos Aires"
    assert existing_user.city == 2
    assert existing_user.address == "Nueva dirección 456"
    assert existing_user.phone == "987654321"

@pytest.mark.asyncio
async def test_update_profile_nonexistent_user(db_session):
    """
    ❌ Caso fallo: Se intenta actualizar el perfil de un usuario inexistente.
    """
    service = UserService(db_session)
    with pytest.raises(Exception) as exc_info:
        await service.update_basic_profile(
            user_id=999999,  # ID inexistente
            country="Chile",
            department="Santiago",
            city=3,
            address="Avenida siempre viva",
            phone="000000000"
        )
    
    assert "Usuario no encontrado" in str(exc_info.value)

@pytest.mark.asyncio
async def test_update_profile_invalid_data(db_session, existing_user):
    """
    ❌ Caso fallo: Se intenta actualizar el perfil con datos inválidos.
    """
    service = UserService(db_session)
    with pytest.raises(Exception) as exc_info:
        await service.update_basic_profile(
            user_id=existing_user.id,
            country=None,  # Valor inválido
            department="",
            city="abc",  # No es un número
            address=None,
            phone="123ABC"  # Contiene letras
        )
    
    assert "Error al actualizar el perfil" in str(exc_info.value)
