import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import SessionLocal
import os
import random

from app.users.models import User
from app.property_routes.models import Property, PropertyUser

VALID_DEED = "files/public_deed.pdf"
VALID_CERT = "files/freedom_certificate.pdf"

@pytest.fixture()
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.mark.asyncio
async def test_edit_nonexistent_lot(db):
    """Intentar editar un lote que no existe debe retornar 400"""

    # Crear usuario y predio para evitar conflictos
    user = User(
        name="LoteInexistente",
        first_last_name="Test",
        second_last_name="Usuario",
        document_number=str(random.randint(100000000, 999999999)),
        type_document_id=1
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    property_ = Property(
        name="Predio test",
        longitude=-75.0,
        latitude=6.0,
        extension=100,
        real_estate_registration_number=random.randint(10000000, 99999999),
        public_deed="https://fakeurl.com/deed.pdf",
        freedom_tradition_certificate="https://fakeurl.com/cert.pdf",
        state=16
    )
    db.add(property_)
    db.commit()
    db.refresh(property_)

    db.add(PropertyUser(user_id=user.id, property_id=property_.id))
    db.commit()

    # ID de lote que no existe
    nonexistent_lot_id = 999999

    # Intentar editar el lote con ese ID
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        new_reg_number = random.randint(10000000, 99999999)

        with open(VALID_DEED, "rb") as deed, open(VALID_CERT, "rb") as cert:
            response = await client.put(f"/properties/lot/{nonexistent_lot_id}", files={
                "public_deed": ("public_deed.pdf", deed, "application/pdf"),
                "freedom_tradition_certificate": ("freedom_certificate.pdf", cert, "application/pdf")
            }, data={
                "name": "Lote no existente",
                "longitude": "-75.5",
                "latitude": "6.5",
                "extension": "200",
                "real_estate_registration_number": str(new_reg_number)
            })

    print("❌ Status:", response.status_code)
    print("❌ JSON:", response.json())

    assert response.status_code == 400
    assert response.json()["success"] is False
    assert "no existe" in response.json()["data"]["message"].lower()

    # Cleanup en orden correcto
    db.query(PropertyUser).filter_by(property_id=property_.id, user_id=user.id).delete()
    db.delete(property_)
    db.delete(user)
    db.commit()

