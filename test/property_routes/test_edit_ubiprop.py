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
def create_property_for_editing(db_session: Session):
    user = User(
        name="Original",
        first_last_name="Owner",
        second_last_name="Test",
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

    property = Property(
        name="Predio Original",
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

    property_user = PropertyUser(user_id=user.id, property_id=property.id)
    db_session.add(property_user)
    db_session.commit()

    yield {
        "user": user,
        "property": property,
    }

    db_session.execute(
        text("DELETE FROM user_property WHERE user_id = :uid AND property_id = :pid"),
        {"uid": user.id, "pid": property.id}
    )
    db_session.delete(property)
    db_session.delete(user)
    db_session.commit()


def test_edit_property_with_out_of_range_coordinates(db_session, create_property_for_editing):
    """Intentar editar un predio con latitud y longitud fuera del rango permitido"""

    test_data = create_property_for_editing
    property_obj = test_data["property"]
    user = test_data["user"]

    # Valores fuera de rango
    invalid_longitude = 200.0  # > 180
    invalid_latitude = -95.0   # < -90

    new_data = {
        "user_id": user.id,
        "name": "Predio Coordenadas Inválidas",
        "longitude": invalid_longitude,
        "latitude": invalid_latitude,
        "extension": 150.0,
        "real_estate_registration_number": generate_random_registration_number()
    }

    response = client.put(
        f"/properties/{property_obj.id}",
        data=new_data,
        files={
            "public_deed": ("dummy.pdf", b"PDF content", "application/pdf"),
            "freedom_tradition_certificate": ("dummy.pdf", b"PDF content", "application/pdf"),
        }
    )
    # Asegura que el backend rechace coordenadas inválidas
    assert response.status_code == 400, response.text

    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["data"]["title"] == "Edición de predio"
    assert "coordenadas" in json_data["data"]["message"].lower()

