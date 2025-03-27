import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from app.main import app
from app.database import SessionLocal
from app.users.models import User
from app.property_routes.models import Property, PropertyUser
from app.roles.models import Vars
import random
import os

# Archivos válidos para subir a Firebase
FILE_DIR = "files"
VALID_DEED = os.path.join(FILE_DIR, "public_deed.pdf")
VALID_CERT = os.path.join(FILE_DIR, "freedom_certificate.pdf")

@pytest.fixture()
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def ensure_states_exist():
    """Crea los estados 16 (Activo) y 17 (Inactivo) si no existen"""
    db = SessionLocal()
    required = {
        16: ("Predio Activo", "property", "Predio habilitado"),
        17: ("Predio Inactivo", "property", "Predio desactivado")
    }
    for state_id, (name, tipo, desc) in required.items():
        if not db.query(Vars).filter_by(id=state_id).first():
            db.add(Vars(id=state_id, name=name, type=tipo, description=desc))
    db.commit()
    db.close()

@pytest.fixture()
def test_user(db: Session):
    document_number = "999888777"
    user = db.query(User).filter_by(document_number=document_number).first()
    created = False

    if not user:
        user = User(
            name="Predio",
            first_last_name="Inactivo",
            second_last_name="Test",
            document_number=document_number,
            type_document_id=1
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        created = True

    yield user

    if created:
        db.delete(user)
        db.commit()

@pytest.mark.asyncio
async def test_activate_inactive_property(ensure_states_exist, db, test_user):
    transport = ASGITransport(app=app)
    reg_number = random.randint(10000000, 99999999)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Crear el predio inicialmente
        with open(VALID_DEED, "rb") as deed, open(VALID_CERT, "rb") as cert:
            response = await client.post("/properties/", files={
                "public_deed": ("public_deed.pdf", deed, "application/pdf"),
                "freedom_tradition_certificate": ("freedom_certificate.pdf", cert, "application/pdf")
            }, data={
                "user_id": str(test_user.id),
                "name": "Predio Inactivo",
                "longitude": "-75.5",
                "latitude": "6.5",
                "extension": "100",
                "real_estate_registration_number": str(reg_number)
            })

            assert response.status_code == 200

        # Obtener el ID del predio
        created_property = db.query(Property).filter_by(real_estate_registration_number=reg_number).first()
        assert created_property is not None

        # Desactivarlo manualmente (simula que ya estaba inactivo)
        created_property.state = 17  # Inactivo
        db.commit()

        # Activarlo vía API
        response = await client.put(
            f"/properties/{created_property.id}/state",
            data={"new_state": True}  # Activar
        )

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["data"]["state"] == 16  # Activo

        # Cleanup
        db.query(PropertyUser).filter_by(property_id=created_property.id).delete()
        db.delete(created_property)
        db.commit()
