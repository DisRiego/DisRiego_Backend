import pytest
import os
from fastapi import UploadFile
from io import BytesIO
from app.property_routes.services import PropertyLotService
from app.database import SessionLocal

@pytest.fixture(scope="module")
def db():
    """Fixture para crear una nueva sesión de base de datos para las pruebas"""
    db = SessionLocal()
    db.begin()
    yield db
    db.rollback()
    db.close()

@pytest.fixture()
def service(db):
    """Crear una instancia del servicio para pruebas"""
    return PropertyLotService(db)

@pytest.mark.asyncio
async def test_save_file_success(service):
    """Prueba guardar un archivo correctamente"""
    file_content = b"Archivo de prueba"
    test_file = UploadFile(filename="test_file.txt", file=BytesIO(file_content))

    # Guardar archivo
    file_path = await service.save_file(test_file)

    # Verificar que el archivo se haya guardado
    assert os.path.exists(file_path)

    # Verificar contenido del archivo
    with open(file_path, "rb") as f:
        assert f.read() == file_content

    # Eliminar archivo después de la prueba
    os.remove(file_path)

@pytest.mark.asyncio
async def test_save_file_failure(service, mocker):
    """Prueba de error al intentar guardar un archivo"""
    test_file = UploadFile(filename="error_file.txt", file=BytesIO(b"data"))

    # Simular un error en `open()`
    mocker.patch("builtins.open", side_effect=OSError("Simulated file error"))

    with pytest.raises(Exception) as exc_info:
        await service.save_file(test_file)

    assert "Error al guardar el archivo" in str(exc_info.value)
