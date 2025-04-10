import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import SessionLocal
from app.users.models import User
from app.property_routes.models import Property, Lot, PropertyLot, PropertyUser
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

@pytest.fixture()
def test_user_and_property_with_lot(db):
    # Crear usuario
    user = User(
        name="LoteTester",
        first_last_name="Ejemplo",
        second_last_name="Duplicado",
        document_number=str(random.randint(100000000, 999999999)),
        type_document_id=1
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Crear predio
    reg_number = random.randint(10000000, 99999999)
    property_ = Property(
        name="Predio con lote",
        longitude=-75.0,
        latitude=6.0,
        extension=500,
        real_estate_registration_number=reg_number,
        public_deed="https://fakeurl.com/deed.pdf",
        freedom_tradition_certificate="https://fakeurl.com/cert.pdf",
        state=16
    )
    db.add(property_)
    db.commit()
    db.refresh(property_)

    # Relacionar usuario con predio
    relation = PropertyUser(user_id=user.id, property_id=property_.id)
    db.add(relation)
    db.commit()

    # Crear lote con matrícula conocida
    existing_reg_number = random.randint(10000000, 99999999)
    lot = Lot(
        name="Lote existente",
        longitude=-75.05,
        latitude=6.05,
        extension=250,
        real_estate_registration_number=existing_reg_number,
        public_deed="https://fakeurl.com/lot_deed.pdf",
        freedom_tradition_certificate="https://fakeurl.com/lot_cert.pdf",
        state=18
    )
    db.add(lot)
    db.commit()
    db.refresh(lot)

    # Relación lote-predio
    db.add(PropertyLot(property_id=property_.id, lot_id=lot.id))
    db.commit()

    yield {
        "user": user,
        "property": property_,
        "existing_reg_number": existing_reg_number
    }

    # 🔁 Cleanup
    db.query(PropertyLot).filter_by(property_id=property_.id).delete()
    db.query(Lot).filter_by(real_estate_registration_number=str(existing_reg_number)).delete()
    db.query(PropertyUser).filter_by(property_id=property_.id).delete()
    db.delete(property_)
    db.delete(user)
    db.commit()

@pytest.mark.asyncio
async def test_create_lot_with_existing_registration_number(test_user_and_property_with_lot):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        property_id = test_user_and_property_with_lot["property"].id
        duplicate_reg_number = test_user_and_property_with_lot["existing_reg_number"]

        with open(VALID_DEED, "rb") as deed, open(VALID_CERT, "rb") as cert:
            response = await client.post("/properties/lot/", files={
                "public_deed": ("public_deed.pdf", deed, "application/pdf"),
                "freedom_tradition_certificate": ("freedom_certificate.pdf", cert, "application/pdf")
            }, data={
                "property_id": str(property_id),
                "name": "Lote duplicado",
                "longitude": "-75.1",
                "latitude": "6.1",
                "extension": "100",
                "real_estate_registration_number": str(duplicate_reg_number)
            })

        print("🚫 Status:", response.status_code)
        print("🚫 JSON:", response.json())

        assert response.status_code == 400
        assert response.json()["success"] is False
        assert "ya existe" in response.json()["data"]["message"].lower()
