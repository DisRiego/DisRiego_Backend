import pytest
from fastapi import UploadFile
from io import BytesIO
from app.database import SessionLocal, engine
from app.users.models import User, Status
from app.users.services import UserService
from sqlalchemy import event

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
    Crea un usuario de prueba en la base de datos, asegurando que no haya conflictos de unicidad.
    """
    # Verificar si ya existe un usuario con el mismo correo y eliminarlo
    existing = db_session.query(User).filter_by(email="testuser@example.com").first()
    if existing:
        db_session.delete(existing)
        db_session.commit()

    # Verificar o crear el estado "Activo"
    active_status = db_session.query(Status).filter_by(name="Activo").first()
    if not active_status:
        active_status = Status(name="Activo", description="Usuario activo")
        db_session.add(active_status)
        db_session.commit()

    # Crear el usuario de prueba
    user = User(
        email="testuser@example.com",
        password="somehashed",
        password_salt="somesalt",
        name="TestUser",
        status_id=active_status.id,
        email_status=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    yield user  # Devuelve el usuario creado para su uso en las pruebas

    # Eliminar el usuario después de la prueba para evitar residuos en la base de datos
    db_session.delete(user)
    db_session.commit()


@pytest.mark.asyncio
async def test_upload_non_image_file(db_session, existing_user):
    """
    ❌ Caso fallo: Se intenta subir un archivo que no es una imagen.
    """
    service = UserService(db_session)
    file_content = BytesIO(b"testdocumentcontent")
    upload_file = UploadFile(filename="test_document.pdf", file=file_content)  # Eliminado content_type
    
    with pytest.raises(Exception) as exc_info:
        await service.save_profile_picture(upload_file)
    
    assert "Error al guardar la imagen de perfil" in str(exc_info.value)

@pytest.mark.asyncio
async def test_upload_invalid_image_format(db_session, existing_user):
    """
    ❌ Caso fallo: Se intenta subir una imagen con un formato no permitido.
    """
    service = UserService(db_session)
    file_content = BytesIO(b"invalidimagecontent")
    upload_file = UploadFile(filename="test_image.tiff", file=file_content)  # Eliminado content_type
    
    with pytest.raises(Exception) as exc_info:
        await service.save_profile_picture(upload_file)
    
    assert "Error al guardar la imagen de perfil" in str(exc_info.value)
