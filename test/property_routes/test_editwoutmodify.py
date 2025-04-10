import pytest
import random
from datetime import date
from sqlalchemy import cast, String  # 👈 IMPORTANTE
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import SessionLocal
from app.users.models import User
from app.property_routes.models import Property, PropertyUser, Lot, PropertyLot
from app.firebase_config import FIREBASE_STORAGE_BUCKET

VALID_DEED = "files/public_deed.pdf"
VALID_CERT = "files/freedom_certificate.pdf"

@pytest.mark.asyncio
async def test_edit_lot_without_optional_fields():
    db = SessionLocal()
    try:
        # Crear usuario
        user = User(
            name="SinOpcionales",
            first_last_name="Lote",
            second_last_name="Prueba",
            document_number=str(random.randint(100000000, 999999999)),
            type_document_id=1
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Crear predio
        property_ = Property(
            name="Predio sin opcionales",
            longitude=-75.0,
            latitude=6.0,
            extension=300,
            real_estate_registration_number=random.randint(10000000, 99999999),
            public_deed="https://url.test/deed.pdf",
            freedom_tradition_certificate="https://url.test/cert.pdf",
            state=16
        )
        db.add(property_)
        db.commit()
        db.refresh(property_)

        # Relacionar usuario con predio
        db.add(PropertyUser(user_id=user.id, property_id=property_.id))
        db.commit()

        # Crear lote vía API
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            real_estate_number = random.randint(10000000, 99999999)
            with open(VALID_DEED, "rb") as deed, open(VALID_CERT, "rb") as cert:
                response = await client.post("/properties/lot/", files={
                    "public_deed": ("deed.pdf", deed, "application/pdf"),
                    "freedom_tradition_certificate": ("cert.pdf", cert, "application/pdf")
                }, data={
                    "property_id": str(property_.id),
                    "name": "Lote de prueba",
                    "longitude": "-75.2",
                    "latitude": "6.1",
                    "extension": "150",
                    "real_estate_registration_number": str(real_estate_number)
                })

            assert response.status_code == 200
            assert response.json()["success"] is True

            # ✅ Cast explícito del campo en la consulta
            lot = db.query(Lot).filter(cast(Lot.real_estate_registration_number, String) == str(real_estate_number)).first()

            # Editar el lote sin campos opcionales
            edit_response = await client.put(f"/properties/lot/{lot.id}", data={
                "name": "Lote actualizado sin opcionales",
                "longitude": "-75.3",
                "latitude": "6.2",
                "extension": "160",
                "real_estate_registration_number": str(real_estate_number)
            })

            assert edit_response.status_code == 200
            assert edit_response.json()["success"] is True

            db.refresh(lot)
            assert lot.name == "Lote actualizado sin opcionales"
            assert lot.payment_interval is None
            assert lot.type_crop_id is None
            assert lot.planting_date is None
            assert lot.estimated_harvest_date is None

        # Limpieza
        db.query(PropertyLot).filter_by(lot_id=lot.id).delete()
        db.delete(lot)
        db.query(PropertyUser).filter_by(property_id=property_.id, user_id=user.id).delete()
        db.delete(property_)
        db.delete(user)
        db.commit()

    finally:
        db.close()
