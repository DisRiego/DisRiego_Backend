import pytest
import uuid
from sqlalchemy import event
from app.database import SessionLocal, engine
from app.users.models import User, Status
from app.roles.models import Role
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

    session.rollback()
    session.close()
    trans.rollback()
    connection.close()


@pytest.fixture
def existing_user(db_session):
    """
    Crea un usuario de prueba en la base de datos y lo devuelve sin eliminarlo al final.
    """
    active_status = db_session.query(Status).filter_by(name="Activo").first()
    if not active_status:
        active_status = Status(name="Activo", description="Usuario activo")
        db_session.add(active_status)
        db_session.commit()

    user = User(
        email=f"user_{uuid.uuid4().hex[:6]}@example.com",
        password="somehashed",
        password_salt="somesalt",
        name="TestUser",
        status_id=active_status.id,  # Estado activo
        email_status=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    yield user  # Devuelve el usuario creado sin eliminarlo

    # No eliminamos al usuario directamente en el fixture.
    # En su lugar, la sesión de prueba hará rollback al final.


@pytest.fixture
def existing_roles(db_session):
    """
    Crea roles de prueba en la base de datos y los elimina después de la prueba.
    """
    role_admin = Role(name="Administrador", description="Rol con permisos administrativos", status=True)
    role_user = Role(name="Usuario", description="Rol estándar", status=True)

    db_session.add_all([role_admin, role_user])
    db_session.commit()

    roles = db_session.query(Role).all()

    yield roles  # Se usan en la prueba

    # No eliminamos explícitamente, confiamos en el rollback de db_session


@pytest.mark.asyncio
async def test_change_user_status_success(db_session, existing_user):
    """
    ✅ Caso éxito: Se cambia el estado de un usuario a un valor válido.
    """
    service = UserService(db_session)
    new_status_id = 2  # Ejemplo: Estado "Inactivo"

    response = service.change_user_status(existing_user.id, new_status_id)

    assert response["success"] is True
    assert "Estado de usuario actualizado correctamente." in response["data"]

    db_session.refresh(existing_user)
    assert existing_user.status_id == new_status_id


@pytest.mark.asyncio
async def test_change_user_status_invalid(db_session, existing_user):
    """
    ❌ Caso fallo: Se intenta cambiar el estado a un valor no permitido.
    """
    service = UserService(db_session)
    invalid_status_id = 999  # Estado inexistente

    with pytest.raises(Exception) as exc_info:
        service.change_user_status(existing_user.id, invalid_status_id)

    assert "Estado no válido." in str(exc_info.value)
