import pytest
import random
import os
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import SessionLocal
from app.users.models import User
from app.property_routes.models import Property, Lot, PropertyUser, PropertyLot

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

@pytest.mark.asyncio
async def test_edit_lot_success(db):
    """Debe editar correctamente un lote existente"""

    # Crear usuario
    user = User(
        name="EditarLote",
        first_last_name="Usuario",
        second_last_name="Prueba",
        document_number=str(random.randint(100000000, 999999999)),
        type_document_id=1
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Crear predio
    property_ = Property(
        name="Predio edición",
        longitude=-75.0,
        latitude=6.0,
        extension=300,
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

    # Crear lote vía API
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg_number = random.randint(10000000, 99999999)

        with open(VALID_DEED, "rb") as deed, open(VALID_CERT, "rb") as cert:
            create_response = await client.post("/properties/lot/", files={
                "public_deed": ("public_deed.pdf", deed, "application/pdf"),
                "freedom_tradition_certificate": ("freedom_certificate.pdf", cert, "application/pdf")
            }, data={
                "property_id": str(property_.id),
                "name": "Lote original",
                "longitude": "-75.1",
                "latitude": "6.1",
                "extension": "120",
                "real_estate_registration_number": str(reg_number)
            })

        assert create_response.status_code == 200
        assert create_response.json()["success"] is True

        # Obtener lote creado
        lot = db.query(Lot).filter(Lot.real_estate_registration_number == str(reg_number)).first()

        # Editar el lote
        new_reg_number = random.randint(10000000, 99999999)

        with open(VALID_DEED, "rb") as deed2, open(VALID_CERT, "rb") as cert2:
            edit_response = await client.put(f"/properties/lot/{lot.id}", files={
                "public_deed": ("public_deed.pdf", deed2, "application/pdf"),
                "freedom_tradition_certificate": ("freedom_certificate.pdf", cert2, "application/pdf")
            }, data={
                "name": "Lote editado",
                "longitude": "-75.3",
                "latitude": "6.3",
                "extension": "180",
                "real_estate_registration_number": str(new_reg_number)
            })

        print("📘 Respuesta edición:", edit_response.json())
        assert edit_response.status_code == 200
        assert edit_response.json()["success"] is True

    # 🔁 Limpieza
    db.query(PropertyLot).filter_by(lot_id=lot.id).delete()
    db.delete(lot)
    db.query(PropertyUser).filter_by(property_id=property_.id).delete()
    db.delete(property_)
    db.delete(user)
    db.commit()
