import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.database import get_db
from app.users.models import User
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
def user_for_invalid_edit(db_session: Session):
    user = User(
        name="Usuario Prueba",
        first_last_name="Apellido1",
        second_last_name="Apellido2",
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

def test_edit_nonexistent_property(db_session, user_for_invalid_edit):
    """Intentar editar un predio inexistente"""

    user = user_for_invalid_edit

    nonexistent_property_id = 999999  # ID que no existe en la base de datos

    new_data = {
        "user_id": user.id,
        "name": "Predio Fantasma",
        "longitude": 10.1234,
        "latitude": -75.5678,
        "extension": 200.0,
        "real_estate_registration_number": generate_random_registration_number()
    }

    response = client.put(
        f"/properties/{nonexistent_property_id}",
        data=new_data,
        files={
            "public_deed": ("dummy.pdf", b"PDF content", "application/pdf"),
            "freedom_tradition_certificate": ("dummy.pdf", b"PDF content", "application/pdf"),
        }
    )

    assert response.status_code == 400
    json_data = response.json()
    assert json_data["success"] is False
    assert "El predio no existe" in json_data["data"]["message"]
