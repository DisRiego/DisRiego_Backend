import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from app.main import app
from app.database import SessionLocal
from app.users.models import User
from app.property_routes.models import Property, PropertyUser, Lot, PropertyLot
from app.roles.models import Vars
import os
import random

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

@pytest.fixture(scope="session", autouse=True)
def ensure_vars_exist():
    db = SessionLocal()
    try:
        required_states = {
            16: ("Predio Activo", "property", "Predio habilitado para operaciones"),
            17: ("Predio Inactivo", "property", "Predio inhabilitado temporalmente"),
            18: ("Lote Activo", "lot", "Lote activo dentro del predio"),
        }

        for state_id, (name, var_type, description) in required_states.items():
            if not db.query(Vars).filter_by(id=state_id).first():
                db.add(Vars(id=state_id, name=name, type=var_type, description=description))
        db.commit()
    finally:
        db.close()

@pytest.fixture()
def test_user(db: Session):
    document_number = "987654321"
    user = db.query(User).filter_by(document_number=document_number).first()
    created = False

    if not user:
        user = User(
            name="Test Lotes",
            first_last_name="Activos",
            second_last_name="User",
            document_number=document_number,
            type_document_id=1,
            email="userlotactive@test.com"
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
async def test_cannot_deactivate_property_with_active_lots(db, test_user):
    # Crear el predio
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg_number = random.randint(10000000, 99999999)
        with open(VALID_DEED, "rb") as deed, open(VALID_CERT, "rb") as cert:
            response = await client.post("/properties/", files={
                "public_deed": ("public_deed.pdf", deed, "application/pdf"),
                "freedom_tradition_certificate": ("freedom_certificate.pdf", cert, "application/pdf")
            }, data={
                "user_id": str(test_user.id),
                "name": "Predio Con Lotes Activos",
                "longitude": "-74.5",
                "latitude": "4.7",
                "extension": "120",
                "real_estate_registration_number": str(reg_number)
            })

            assert response.status_code == 200
            assert response.json()["success"] is True

        # Obtener el predio
        property = db.query(Property).filter_by(real_estate_registration_number=reg_number).first()
        assert property is not None

        # Crear el lote activo
        lot = Lot(
            name="Lote Activo",
            longitude=4.5,
            latitude=-74.7,
            extension=40.0,
            real_estate_registration_number=random.randint(10000000, 99999999),
            public_deed="url_falsa_lote_deed.pdf",
            freedom_tradition_certificate="url_falsa_lote_cert.pdf",
            state=18
        )
        db.add(lot)
        db.commit()
        db.refresh(lot)

        # Relación lote-predio
        db.add(PropertyLot(property_id=property.id, lot_id=lot.id))
        db.commit()

        # Intentar desactivar el predio
        response = await client.put(
            f"/properties/{property.id}/state",
            data={"new_state": False}
        )
        assert response.status_code == 400
        assert "lotes activos" in response.text

        # Limpieza
        db.query(PropertyLot).filter_by(property_id=property.id, lot_id=lot.id).delete()
        db.delete(lot)
        db.query(PropertyUser).filter_by(property_id=property.id).delete()
        db.delete(property)
        db.commit()
