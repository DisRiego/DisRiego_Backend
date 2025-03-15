import pytest
import json
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.property_routes.services import PropertyLotService
from app.property_routes.models import Property
from fastapi import UploadFile
from io import BytesIO

@pytest.fixture(scope="module")
def db():
    """Fixture para crear una nueva sesión de base de datos para las pruebas"""
    db = SessionLocal()
    db.begin()
    yield db
    
    db.close()

@pytest.fixture()
def client():
    """Crear una instancia del cliente de pruebas"""
    return TestClient(app)

@pytest.mark.asyncio
async def test_create_property_success(db):
    """Prueba la creación exitosa de un predio"""
    service = PropertyLotService(db)

    # Simular archivos subidos
    public_deed = UploadFile(filename="test_deed.pdf", file=BytesIO(b"dummy data"))
    freedom_tradition_certificate = UploadFile(filename="test_certificate.pdf", file=BytesIO(b"dummy data"))

    # Llamar a la función asíncrona usando `await`
    response = await service.create_property(
        name="casta property",
        longitude=223.45,
        latitude=87.89,
        extension=2000.0,
        real_estate_registration_number=173258789,
        public_deed=public_deed,
        freedom_tradition_certificate=freedom_tradition_certificate
    )

    # Obtener JSON correctamente
    json_response = json.loads(response.body.decode("utf-8"))

    # Imprimir la respuesta para depuración
    print("\nRESPONSE JSON:", json_response)

    # Validar si hay un error inesperado
    if response.status_code != 200:
        pytest.fail(f"Error inesperado: {json_response}")

    # Verificar la respuesta esperada
    assert response.status_code == 200
    assert json_response["success"] is True
    assert json_response["data"]["title"] == "Creacion de predios"

@pytest.mark.asyncio
async def test_create_property_duplicate(db):
    """Prueba de error si el predio ya existe en la base de datos"""
    service = PropertyLotService(db)

    public_deed = UploadFile(filename="duplicate_deed.pdf", file=BytesIO(b"dummy data"))
    freedom_tradition_certificate = UploadFile(filename="duplicate_certificate.pdf", file=BytesIO(b"dummy data"))

    response = await service.create_property(
        name="Duplicate Property",
        longitude=25.67,
        latitude=99.01,
        extension=510.0,
        real_estate_registration_number=173258789,  # Mismo número que el test anterior
        public_deed=public_deed,
        freedom_tradition_certificate=freedom_tradition_certificate
    )

    json_response = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 400
    assert json_response["success"] is False
    assert json_response["data"]["title"] == "Creacion de predios"
    assert "El registro de predio ya existe en el sistema" in json_response["data"]["message"]

@pytest.mark.asyncio
async def test_create_property_missing_fields(db):
    """Prueba de error cuando faltan campos obligatorios"""
    service = PropertyLotService(db)

    public_deed = UploadFile(filename="missing_deed.pdf", file=BytesIO(b"dummy data"))
    freedom_tradition_certificate = UploadFile(filename="missing_certificate.pdf", file=BytesIO(b"dummy data"))

    response = await service.create_property(
        name=None,
        longitude=45.67,
        latitude=89.01,
        extension=500.0,
        real_estate_registration_number=287654321,
        public_deed=public_deed,
        freedom_tradition_certificate=freedom_tradition_certificate
    )

    json_response = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 400
    assert json_response["success"] is False
    assert json_response["data"]["title"] == "Creacion de predios"
    assert "Faltan campos requeridos." in json_response["data"]["message"]

@pytest.mark.asyncio
async def test_create_property_missing_files(db):
    """Prueba de error cuando faltan archivos requeridos"""
    service = PropertyLotService(db)

    response = await service.create_property(
        name="Property Without Files",
        longitude=10.12,
        latitude=20.34,
        extension=200.0,
        real_estate_registration_number=555555555,
        public_deed=None,
        freedom_tradition_certificate=UploadFile(filename="valid_certificate.pdf", file=BytesIO(b"dummy data"))
    )

    json_response = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 400
    assert json_response["success"] is False
    assert json_response["data"]["title"] == "Creacion de predios"
    assert "Faltan los archivos requeridos para el predio." in json_response["data"]["message"]

@pytest.mark.asyncio
async def test_create_property_server_error(db, mocker):
    """Simula un error interno del servidor al intentar crear un predio"""
    service = PropertyLotService(db)

    public_deed = UploadFile(filename="error_deed.pdf", file=BytesIO(b"dummy data"))
    freedom_tradition_certificate = UploadFile(filename="error_certificate.pdf", file=BytesIO(b"dummy data"))

    # Usamos `mocker` para simular que `save_file` lanza una excepción
    mocker.patch.object(service, "save_file", side_effect=Exception("Simulated error"))

    response = await service.create_property(
        name="Error Property",
        longitude=17.34,
        latitude=59.78,
        extension=300.0,
        real_estate_registration_number=666866666,
        public_deed=public_deed,
        freedom_tradition_certificate=freedom_tradition_certificate
    )

    json_response = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 500
    assert json_response["success"] is False
    assert json_response["data"]["title"] == "Creacion de predios"
    assert "Error al crear el predio, Contacta al administrador" in json_response["data"]["message"]
