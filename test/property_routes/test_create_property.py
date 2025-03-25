import pytest
<<<<<<< HEAD
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.sql import text  # 🔹 Import necesario para consultas SQL directas
from app.main import app  # Importar la aplicación FastAPI
from app.database import get_db
from app.users.models import User
from app.property_routes.models import Property, PropertyUser

@pytest.fixture
def client():
    """Cliente de prueba para hacer solicitudes a la API"""
    return TestClient(app)

@pytest.fixture
def db_session():
    """Fixture para manejar una sesión de base de datos en pruebas"""
    db = next(get_db())  # Obtener una sesión de la base de datos configurada
    yield db
    db.rollback()  # Asegurar que no persistan cambios
    db.close()

@pytest.fixture
def setup_test_user(db_session: Session):
    """Crea un usuario de prueba en la base de datos si no existe"""
    test_user = db_session.query(User).filter_by(email="test_user@example.com").first()

    if not test_user:
        test_user = User(
            email="test_user@example.com",
            password="test123"  # Usa el campo correcto en el modelo
        )
        db_session.add(test_user)
        db_session.commit()
        db_session.refresh(test_user)

    yield test_user

    # 🔹 Eliminar referencias en `user_property` antes de borrar el usuario
    db_session.execute(
        text("DELETE FROM user_property WHERE user_id = :user_id"),
        {"user_id": test_user.id}
    )
    db_session.commit()

    # 🔹 Ahora podemos eliminar el usuario sin conflictos
    db_session.delete(test_user)
    db_session.commit()

    # 🔹 Limpiar propiedades creadas en la prueba
    db_session.execute(text("DELETE FROM property WHERE name = 'Predio de prueba'"))
    db_session.execute(text("DELETE FROM property WHERE real_estate_registration_number = 123456"))
    db_session.commit()

def test_create_property_success(client, setup_test_user, db_session):
    """Prueba para crear un predio con datos válidos"""

    # 🔹 Asegurar que no haya un predio con el mismo número de registro
    db_session.execute(text("DELETE FROM property WHERE real_estate_registration_number = 123456"))
    db_session.commit()

    data = {
        "user_id": setup_test_user.id,
        "name": "Predio de prueba",
        "longitude": -75.691,
        "latitude": 4.1492,
        "extension": 500.5,
        "real_estate_registration_number": 123456,
    }

    files = {
        "public_deed": ("public_deed.pdf", b"fake pdf content", "application/pdf"),
        "freedom_tradition_certificate": ("freedom_tradition.pdf", b"fake pdf content", "application/pdf"),
    }

    response = client.post("/properties/", data=data, files=files)

    # 🔹 Ver respuesta del servidor para identificar errores
    print("Response Status Code:", response.status_code)
    print("Response JSON:", response.json())

    assert response.status_code == 200, f"Error en la creación del predio: {response.json()}"
    
    response_json = response.json()
    assert response_json["success"] is True
    assert "Se ha creado el predio satisfactoriamente" in response_json["data"]["message"]

    # 🔹 Verificar que la propiedad se creó en la BD
    created_property = db_session.query(Property).filter_by(name="Predio de prueba").first()
    assert created_property is not None

    # 🔹 Verificar que la relación con el usuario existe
    user_property_relation = db_session.query(PropertyUser).filter_by(property_id=created_property.id).first()
    assert user_property_relation is not None
    assert user_property_relation.user_id == setup_test_user.id

    # 🔹 Limpiar después de la prueba
    db_session.execute(text("DELETE FROM user_property WHERE property_id = :property_id"), {"property_id": created_property.id})
    db_session.execute(text("DELETE FROM property WHERE id = :property_id"), {"property_id": created_property.id})
    db_session.commit()
=======
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
>>>>>>> origin/develop
