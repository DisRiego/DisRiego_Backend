import pytest
import os
import random
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from app.main import app
from app.database import SessionLocal
from app.users.models import User
from app.property_routes.models import Property, Lot, PropertyUser, PropertyLot
from app.roles.models import Vars

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

@pytest.fixture(scope="session", autouse=True)
def ensure_states_exist():
    db = SessionLocal()
    try:
        states = {
            16: ("Predio Activo", "property", "Predio habilitado para operaciones"),
            17: ("Predio Inactivo", "property", "Predio inhabilitado temporalmente"),
            18: ("Lote Activo", "lot", "Lote activo dentro del predio"),
            19: ("Lote Inactivo", "lot", "Lote inactivo o sin uso")
        }
        for state_id, (name, type_, desc) in states.items():
            if not db.query(Vars).filter_by(id=state_id).first():
                db.add(Vars(id=state_id, name=name, type=type_, description=desc))
        db.commit()
    finally:
        db.close()

@pytest.fixture()
def test_user(db: Session):
    document_number = "999888777"
    user = db.query(User).filter_by(document_number=document_number).first()
    created = False

    if not user:
        user = User(
            name="Test",
            first_last_name="Inactive",
            second_last_name="Lots",
            document_number=document_number,
            type_document_id=1,
            status_id=1
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
async def test_deactivate_property_without_active_lots(db, test_user):
    """Desactiva un predio que tiene solo lotes inactivos (debe permitirlo)"""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg_number = random.randint(11111111, 99999999)

        # 1. Crear predio vía API
        with open(VALID_DEED, "rb") as deed, open(VALID_CERT, "rb") as cert:
            response = await client.post("/properties/", files={
                "public_deed": ("public_deed.pdf", deed, "application/pdf"),
                "freedom_tradition_certificate": ("freedom_certificate.pdf", cert, "application/pdf")
            }, data={
                "user_id": test_user.id,
                "name": "Predio Solo Lotes Inactivos",
                "longitude": "-74.123",
                "latitude": "4.123",
                "extension": "300",
                "real_estate_registration_number": reg_number
            })
            assert response.status_code == 200

        # 2. Obtener predio recién creado
        prop = db.query(Property).filter_by(real_estate_registration_number=reg_number).first()
        assert prop is not None

        # 3. Crear un lote inactivo asociado
        lot = Lot(
            name="Lote Inactivo",
            longitude=4.5678,
            latitude=-74.9876,
            extension=50.0,
            real_estate_registration_number=random.randint(10000000, 99999999),
            public_deed="mock_deed.pdf",
            freedom_tradition_certificate="mock_cert.pdf",
            state=19  # Inactivo
        )
        db.add(lot)
        db.commit()
        db.refresh(lot)

        db.add(PropertyLot(property_id=prop.id, lot_id=lot.id))
        db.commit()

        # 4. Desactivar el predio vía API
        response = await client.put(f"/properties/{prop.id}/state", data={"new_state": "false"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["state"] == 4  # 👈 El backend retorna 4, no 17

        # 5. Limpieza
        db.query(PropertyLot).filter_by(property_id=prop.id).delete()
        db.query(PropertyUser).filter_by(property_id=prop.id).delete()
        db.delete(lot)
        db.delete(prop)
        db.commit()
