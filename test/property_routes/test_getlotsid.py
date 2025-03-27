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

@pytest.mark.asyncio
async def test_get_lot_by_id_success(db):
    """Debe obtener correctamente un lote existente por su ID"""

    # Crear usuario
    user = User(
        name="LoteConsulta",
        first_last_name="Test",
        second_last_name="Consulta",
        document_number=str(random.randint(100000000, 999999999)),
        type_document_id=1
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Crear predio activo
    property_ = Property(
        name="Predio consulta",
        longitude=-75.0,
        latitude=6.0,
        extension=500,
        real_estate_registration_number=random.randint(10000000, 99999999),
        public_deed="https://fakeurl.com/deed.pdf",
        freedom_tradition_certificate="https://fakeurl.com/cert.pdf",
        state=16  # Activo
    )
    db.add(property_)
    db.commit()
    db.refresh(property_)

    # Relación con usuario
    relation = PropertyUser(user_id=user.id, property_id=property_.id)
    db.add(relation)
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
                "name": "Lote a consultar",
                "longitude": "-75.2",
                "latitude": "6.2",
                "extension": "150",
                "real_estate_registration_number": str(reg_number)
            })

        assert create_response.status_code == 200
        assert create_response.json()["success"] is True

    # Obtener el lote creado desde la base de datos
    lot = db.query(Lot).filter(Lot.real_estate_registration_number == str(reg_number)).first()

    assert lot is not None

    # Consultar el lote por ID
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/properties/lot/{lot.id}")
        print("📦 GET status:", response.status_code)
        print("📦 GET JSON:", response.json())

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == lot.id
        assert data["name"] == "Lote a consultar"
        assert data["property_id"] == property_.id
        assert data["nombre_estado"] is not None

    # 🔁 Cleanup
    db.query(PropertyLot).filter_by(lot_id=lot.id).delete()
    db.delete(lot)
    db.query(PropertyUser).filter_by(property_id=property_.id).delete()
    db.delete(property_)
    db.delete(user)
    db.commit()
