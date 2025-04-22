import pytest
import os
import random
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from app.main import app
from app.database import SessionLocal
from app.users.models import User
from app.property_routes.models import Property, PropertyUser, Lot, PropertyLot

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

@pytest.fixture()
def test_user_and_inactive_property(db):
    # Crear usuario
    user = User(
        name="Tester",
        first_last_name="Lote",
        second_last_name="Inactivo",
        document_number=str(random.randint(100000000, 999999999)),
        type_document_id=1
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Crear predio con estado inactivo (17)
    reg_number = random.randint(10000000, 99999999)
    property_ = Property(
        name="Predio Inactivo",
        longitude=-75.0,
        latitude=6.0,
        extension=300,
        real_estate_registration_number=reg_number,
        public_deed="https://mock/deed.pdf",
        freedom_tradition_certificate="https://mock/cert.pdf",
        state=17  # INACTIVO
    )
    db.add(property_)
    db.commit()
    db.refresh(property_)

    # Relación usuario-predio
    db.add(PropertyUser(user_id=user.id, property_id=property_.id))
    db.commit()

    yield {"user": user, "property": property_}

    # 🔁 Limpieza
    lots = db.query(Lot).join(PropertyLot).filter(PropertyLot.property_id == property_.id).all()
    for lot in lots:
        db.query(PropertyLot).filter_by(lot_id=lot.id).delete()
        db.delete(lot)

    db.query(PropertyUser).filter_by(property_id=property_.id).delete()
    db.delete(property_)
    db.delete(user)
    db.commit()

@pytest.mark.asyncio
async def test_create_lot_on_inactive_property(test_user_and_inactive_property):
    """Debe rechazar creación de lote en predio inactivo"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        property_id = test_user_and_inactive_property["property"].id
        reg_number = random.randint(10000000, 99999999)

        with open(VALID_DEED, "rb") as deed, open(VALID_CERT, "rb") as cert:
            response = await client.post("/properties/lot/", files={
                "public_deed": ("public_deed.pdf", deed, "application/pdf"),
                "freedom_tradition_certificate": ("freedom_certificate.pdf", cert, "application/pdf")
            }, data={
                "property_id": str(property_id),
                "name": "Lote Rechazado",
                "longitude": "-75.3",
                "latitude": "6.3",
                "extension": "200",
                "real_estate_registration_number": str(reg_number)
            })

        print("🚫 Status:", response.status_code)
        print("🚫 JSON:", response.json())

        assert response.status_code == 400
        assert response.json()["success"] is False
        assert "inactivo" in response.json()["data"]["message"].lower()
