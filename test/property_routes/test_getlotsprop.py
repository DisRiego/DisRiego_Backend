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
async def test_get_lots_for_property_with_lots(db):
    """Debe obtener todos los lotes de un predio que tiene al menos un lote"""

    # Crear usuario
    user = User(
        name="LoteConsulta",
        first_last_name="Tester",
        second_last_name="Activo",
        document_number=str(random.randint(100000000, 999999999)),
        type_document_id=1
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Crear predio activo
    property_ = Property(
        name="Predio con lotes",
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

    # Asociar usuario al predio
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
                "name": "Lote de prueba",
                "longitude": "-75.1",
                "latitude": "6.1",
                "extension": "100",
                "real_estate_registration_number": str(reg_number)
            })

        assert create_response.status_code == 200
        assert create_response.json()["success"] is True

        # Consultar todos los lotes del predio
        get_response = await client.get(f"/properties/{property_.id}/lots/")
        print("📥 Lotes del predio:", get_response.json())

        assert get_response.status_code == 200
        data = get_response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 1  # Al menos un lote creado

    # 🔁 Cleanup
    lots = db.query(Lot).join(PropertyLot).filter(PropertyLot.property_id == property_.id).all()
    for lot in lots:
        db.query(PropertyLot).filter_by(lot_id=lot.id).delete()
        db.delete(lot)

    db.query(PropertyUser).filter_by(property_id=property_.id).delete()
    db.delete(property_)
    db.delete(user)
    db.commit()
