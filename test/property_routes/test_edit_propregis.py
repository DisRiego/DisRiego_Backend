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
def create_two_properties(db_session: Session):
    """Crea dos predios distintos con el mismo usuario, cada uno con número de matrícula único"""

    # Crear usuario
    user = User(
        name="Usuario",
        first_last_name="Prueba",
        second_last_name="Caso",
        email=generate_random_email(),
        password="hashed_password",
        type_document_id=1,
        document_number=generate_random_document_number(),
        phone="3001234567",
        status_id=1
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Predio 1
    property1 = Property(
        name="Predio Uno",
        longitude=1.1,
        latitude=1.1,
        extension=100.0,
        real_estate_registration_number=generate_random_registration_number(),
        public_deed="predio1_deed.pdf",
        freedom_tradition_certificate="predio1_cert.pdf",
        state=16
    )
    db_session.add(property1)
    db_session.commit()
    db_session.refresh(property1)

    db_session.add(PropertyUser(user_id=user.id, property_id=property1.id))

    # Predio 2
    property2 = Property(
        name="Predio Dos",
        longitude=2.2,
        latitude=2.2,
        extension=200.0,
        real_estate_registration_number=generate_random_registration_number(),
        public_deed="predio2_deed.pdf",
        freedom_tradition_certificate="predio2_cert.pdf",
        state=16
    )
    db_session.add(property2)
    db_session.commit()
    db_session.refresh(property2)

    db_session.add(PropertyUser(user_id=user.id, property_id=property2.id))
    db_session.commit()

    yield {
        "user": user,
        "property1": property1,
        "property2": property2
    }

    # Limpieza
    db_session.execute(
        text("DELETE FROM user_property WHERE user_id = :uid"),
        {"uid": user.id}
    )
    db_session.delete(property1)
    db_session.delete(property2)
    db_session.delete(user)
    db_session.commit()

def test_edit_property_with_duplicate_registration_number(db_session, create_two_properties):
    """Intentar editar un predio usando el número de matrícula de otro predio existente"""

    data = create_two_properties
    user = data["user"]
    property1 = data["property1"]
    property2 = data["property2"]

    # Usamos el número de matrícula de property1 para editar property2
    duplicate_number = property1.real_estate_registration_number

    update_data = {
        "user_id": user.id,
        "name": "Predio Modificado",
        "longitude": 9.9,
        "latitude": 9.9,
        "extension": 300.0,
        "real_estate_registration_number": duplicate_number  # Este ya existe en otro predio
    }

    response = client.put(
        f"/properties/{property2.id}",
        data=update_data,
        files={
            "public_deed": ("dummy.pdf", b"PDF content", "application/pdf"),
            "freedom_tradition_certificate": ("dummy.pdf", b"PDF content", "application/pdf"),
        }
    )

    assert response.status_code == 400
    json_data = response.json()
    assert json_data["success"] is False
    assert "data" in json_data
    assert "número de registro" in json_data["data"]["message"].lower() or "ya existe" in json_data["data"]["message"].lower()
