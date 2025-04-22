import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import SessionLocal
from app.users.models import User
from app.property_routes.models import Property, PropertyUser
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
def test_user_and_property(db):
    user = User(
        name="Tester",
        first_last_name="Faltantes",
        second_last_name="Campos",
        document_number=str(random.randint(100000000, 999999999)),
        type_document_id=1
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    reg_number = random.randint(10000000, 99999999)
    property_ = Property(
        name="Predio incompleto",
        longitude=-75.0,
        latitude=6.0,
        extension=300,
        real_estate_registration_number=reg_number,
        public_deed="https://fakeurl.com/predio_deed.pdf",
        freedom_tradition_certificate="https://fakeurl.com/predio_cert.pdf",
        state=16
    )
    db.add(property_)
    db.commit()
    db.refresh(property_)

    db.add(PropertyUser(user_id=user.id, property_id=property_.id))
    db.commit()

    yield {"user": user, "property": property_}

    db.query(PropertyUser).filter_by(property_id=property_.id).delete()
    db.delete(property_)
    db.delete(user)
    db.commit()

@pytest.mark.asyncio
async def test_create_lot_missing_required_fields(test_user_and_property):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        property_id = test_user_and_property["property"].id
        reg_number = random.randint(10000000, 99999999)

        with open(VALID_DEED, "rb") as deed, open(VALID_CERT, "rb") as cert:
            # ❌ Falta el campo obligatorio "name"
            response = await client.post("/properties/lot/", files={
                "public_deed": ("public_deed.pdf", deed, "application/pdf"),
                "freedom_tradition_certificate": ("freedom_certificate.pdf", cert, "application/pdf")
            }, data={
                "property_id": str(property_id),
                "longitude": "-75.2",
                "latitude": "6.2",
                "extension": "150",
                "real_estate_registration_number": str(reg_number)
            })

        print("🚫 Status:", response.status_code)
        print("🚫 JSON:", response.json())

        # ✅ Verifica que el error sea por validación
        assert response.status_code == 422
        assert "detail" in response.json()
        assert any("name" in str(field.get("loc")) and "Field required" in field.get("msg") for field in response.json()["detail"])
