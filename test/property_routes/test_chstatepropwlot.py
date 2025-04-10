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
            3: ("Activo", "predio_status", "Estado que indica que el predio está habilitado."),
            4: ("Inactivo", "predio_status", "Estado que indica que el predio está deshabilitado."),
            5: ("Activo", "lote_status", "Estado que indica que el lote está habilitado."),
            6: ("Inactivo", "lote_status", "Estado que indica que el lote está deshabilitado.")
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
    """No debe permitir desactivar un predio si tiene lotes activos asociados (estado 5)"""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg_number = random.randint(10000000, 99999999)

        # Crear el predio
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

        # Obtener el predio recién creado
        property = db.query(Property).filter_by(real_estate_registration_number=reg_number).first()
        assert property is not None

        # Crear lote con estado ACTIVO (5)
        lot = Lot(
            name="Lote Activo",
            longitude=4.5,
            latitude=-74.7,
            extension=40.0,
            real_estate_registration_number=random.randint(10000000, 99999999),
            public_deed="url_falsa_lote_deed.pdf",
            freedom_tradition_certificate="url_falsa_lote_cert.pdf",
            state=5  # Estado activo según lote_status
        )
        db.add(lot)
        db.commit()
        db.refresh(lot)

        # Asociar lote al predio
        db.add(PropertyLot(property_id=property.id, lot_id=lot.id))
        db.commit()

        # Intentar desactivar el predio (debe fallar porque tiene lotes activos)
        response = await client.put(
            f"/properties/{property.id}/state",
            data={"new_state": False}
        )
        assert response.status_code == 400
        assert "lotes activos" in response.text.lower()

        # Limpieza
        db.query(PropertyLot).filter_by(property_id=property.id, lot_id=lot.id).delete()
        db.delete(lot)
        db.query(PropertyUser).filter_by(property_id=property.id).delete()
        db.delete(property)
        db.commit()
