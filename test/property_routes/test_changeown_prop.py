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
    session = next(get_db())
    yield session
    session.close()

def generate_random_email():
    return f"test_{''.join(random.choices(string.ascii_lowercase, k=6))}@example.com"

def generate_random_document_number():
    return random.randint(100000000, 999999999)

def generate_random_registration_number():
    return random.randint(100000000, 999999999)

@pytest.fixture
def setup_property_with_two_users(db_session: Session):
    # Usuario original (dueño actual)
    user1 = User(
        name="Dueño",
        first_last_name="Original",
        second_last_name="User",
        email=generate_random_email(),
        password="hashed_password",
        type_document_id=1,
        document_number=generate_random_document_number(),
        phone="3000000000",
        status_id=1
    )
    db_session.add(user1)
    db_session.commit()
    db_session.refresh(user1)

    # Usuario nuevo (nuevo dueño)
    user2 = User(
        name="Nuevo",
        first_last_name="Propietario",
        second_last_name="User",
        email=generate_random_email(),
        password="hashed_password",
        type_document_id=1,
        document_number=generate_random_document_number(),
        phone="3000000001",
        status_id=1
    )
    db_session.add(user2)
    db_session.commit()
    db_session.refresh(user2)

    # Crear predio
    property = Property(
        name="Predio para Cambio de Dueño",
        longitude=5.1234,
        latitude=-73.5678,
        extension=100.0,
        real_estate_registration_number=generate_random_registration_number(),
        public_deed="original_deed.pdf",
        freedom_tradition_certificate="original_cert.pdf",
        state=16
    )
    db_session.add(property)
    db_session.commit()
    db_session.refresh(property)

    # Asociación original
    property_user = PropertyUser(user_id=user1.id, property_id=property.id)
    db_session.add(property_user)
    db_session.commit()

    yield {
        "original_user": user1,
        "new_user": user2,
        "property": property
    }

    # Limpiar al finalizar
    db_session.execute(
        text("DELETE FROM user_property WHERE property_id = :pid"),
        {"pid": property.id}
    )
    db_session.delete(property)
    db_session.delete(user1)
    db_session.delete(user2)
    db_session.commit()

def test_change_property_owner(db_session, setup_property_with_two_users):
    """Editar un predio y cambiar el dueño, validando persistencia"""

    data = setup_property_with_two_users
    original_user = data["original_user"]
    new_user = data["new_user"]
    property_obj = data["property"]

    new_data = {
        "user_id": new_user.id,  # Aquí cambiamos el dueño
        "name": "Predio con Nuevo Dueño",
        "longitude": 6.9999,
        "latitude": -74.2222,
        "extension": 180.0,
        "real_estate_registration_number": generate_random_registration_number()
    }

    response = client.put(
        f"/properties/{property_obj.id}",
        data=new_data,
        files={
            "public_deed": ("updated.pdf", b"Updated content", "application/pdf"),
            "freedom_tradition_certificate": ("updated.pdf", b"Updated content", "application/pdf"),
        }
    )

    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert "editado satisfactoriamente" in json_data["data"]["message"]

    # Validar en la base de datos el cambio de propietario
    updated_relation = db_session.query(PropertyUser).filter_by(property_id=property_obj.id).first()
    assert updated_relation is not None
    assert updated_relation.user_id == new_user.id
