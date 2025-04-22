import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from app.main import app
from app.database import get_db
from app.users.models import User
from app.property_routes.models import Property, PropertyUser
import random
import string

client = TestClient(app)

@pytest.fixture
def db_session():
    """Fixture para obtener una sesión de base de datos"""
    session = next(get_db())
    yield session
    session.close()

def generate_random_email():
    return f"test_{''.join(random.choices(string.ascii_lowercase, k=6))}@example.com"

def generate_random_document_number():
    return random.randint(100000000, 999999999)  # 9 dígitos

def generate_random_registration_number():
    return random.randint(100000000, 999999999)

@pytest.fixture
def create_test_property(db_session: Session):
    """Crea un usuario y un predio de prueba, los elimina después de la prueba"""

    # Crear usuario
    user = User(
        name="Test",
        first_last_name="User",
        second_last_name="Example",
        email=generate_random_email(),
        password="hashed_password",
        type_document_id=1,
        document_number=generate_random_document_number(),
        phone="3216549870",
        status_id=1
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Crear predio
    property = Property(
        name="Predio Test",
        longitude=10.1234,
        latitude=-75.5678,
        extension=500.0,
        real_estate_registration_number=generate_random_registration_number(),
        public_deed="url_public_deed.pdf",
        freedom_tradition_certificate="url_certificate.pdf",
        state=16
    )
    db_session.add(property)
    db_session.commit()
    db_session.refresh(property)

    # Asociar usuario al predio
    property_user = PropertyUser(user_id=user.id, property_id=property.id)
    db_session.add(property_user)
    db_session.commit()

    yield {
        "user": user,
        "property": property,
    }

    # Eliminar datos
    db_session.execute(
        text("DELETE FROM user_property WHERE user_id = :uid AND property_id = :pid"),
        {"uid": user.id, "pid": property.id}
    )
    db_session.delete(property)
    db_session.delete(user)
    db_session.commit()

def test_get_existing_property_by_id(db_session, create_test_property):
    """Obtiene un predio por ID existente"""

    test_data = create_test_property
    prop_id = test_data["property"].id
    user = test_data["user"]

    response = client.get(f"/properties/{prop_id}")
    assert response.status_code == 200

    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["id"] == prop_id
    assert json_data["data"]["name"] == test_data["property"].name
    assert json_data["data"]["owner_document_number"] == user.document_number
    assert json_data["data"]["owner_id"] == user.id

def test_get_nonexistent_property_by_id():
    """Intentar obtener un predio con un ID inexistente"""

    fake_id = 999999  # ID que con alta probabilidad no existe
    response = client.get(f"/properties/{fake_id}")

    assert response.status_code == 404
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["data"] == "Predio no encontrado"

def test_get_all_properties(db_session, create_test_property):
    """Obtener todos los predios y validar estructura de respuesta"""

    response = client.get("/properties/")
    assert response.status_code == 200

    json_data = response.json()
    assert "success" in json_data
    assert json_data["success"] is True
    assert "data" in json_data
    assert isinstance(json_data["data"], list)
    assert len(json_data["data"]) > 0

    # Validar estructura del primer predio
    property_item = json_data["data"][0]
    expected_keys = {
        "id", "name", "longitude", "latitude", "extension",
        "real_estate_registration_number", "public_deed", "freedom_tradition_certificate",
        "state", "state_name", "owner_document_number"
    }
    assert expected_keys.issubset(property_item.keys())

def test_get_properties_for_user(db_session, create_test_property):
    """Obtener predios asignados a un usuario específico"""

    test_data = create_test_property
    user = test_data["user"]
    property_obj = test_data["property"]

    response = client.get(f"/properties/user/{user.id}")
    assert response.status_code == 200

    json_data = response.json()
    assert json_data["success"] is True
    assert "data" in json_data
    assert isinstance(json_data["data"], list)
    assert len(json_data["data"]) > 0

    # Verificar que el predio creado esté presente en los datos
    found = False
    for item in json_data["data"]:
        if item["id"] == property_obj.id:
            found = True
            expected_keys = {
                "id", "name", "longitude", "latitude", "extension",
                "real_estate_registration_number", "public_deed",
                "freedom_tradition_certificate", "state", "state_name"
            }
            assert expected_keys.issubset(item.keys())
            break

    assert found, "El predio creado no fue encontrado en la respuesta del usuario"
@pytest.fixture
def create_user_without_properties(db_session: Session):
    """Crea un usuario sin predios asignados y lo elimina después de la prueba"""

    user = User(
        name="UsuarioSinPredios",
        first_last_name="Test",
        second_last_name="Unassigned",
        email=generate_random_email(),
        password="hashed_password",
        type_document_id=1,
        document_number=generate_random_document_number(),
        phone="3000000000",
        status_id=1
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    yield user

    db_session.delete(user)
    db_session.commit()

def test_get_properties_for_user_without_properties(db_session, create_user_without_properties):
    """Debe retornar lista vacía si el usuario no tiene predios asignados"""

    user = create_user_without_properties

    response = client.get(f"/properties/user/{user.id}")
    assert response.status_code == 404

    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["data"] == []