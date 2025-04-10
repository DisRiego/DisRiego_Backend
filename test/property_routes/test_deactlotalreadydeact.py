import pytest
import random
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import SessionLocal
from app.users.models import User
from app.property_routes.models import Property, PropertyUser, Lot, PropertyLot

@pytest.mark.asyncio
async def test_deactivate_already_inactive_lot():
    db = SessionLocal()
    try:
        # Crear usuario
        user = User(
            name="LoteInactivo",
            first_last_name="Prueba",
            second_last_name="Usuario",
            document_number=str(random.randint(100000000, 999999999)),
            type_document_id=1
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Crear predio con estado 3 (Activo en predio_status)
        property_ = Property(
            name="Predio Activo",
            longitude=-75.0,
            latitude=6.0,
            extension=300,
            real_estate_registration_number=random.randint(10000000, 99999999),
            public_deed="https://url.test/deed.pdf",
            freedom_tradition_certificate="https://url.test/cert.pdf",
            state=3
        )
        db.add(property_)
        db.commit()
        db.refresh(property_)

        db.add(PropertyUser(user_id=user.id, property_id=property_.id))
        db.commit()

        # Crear lote ya inactivo (state = 6)
        lot = Lot(
            name="Lote Inactivo",
            longitude=-75.2,
            latitude=6.1,
            extension=150,
            real_estate_registration_number=random.randint(10000000, 99999999),
            state=6
        )
        db.add(lot)
        db.commit()
        db.refresh(lot)

        db.add(PropertyLot(property_id=property_.id, lot_id=lot.id))
        db.commit()

        # Intentar desactivar un lote ya inactivo
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(f"/properties/lot/{lot.id}/state", data={
                "new_state": False
            })

            # Debe seguir siendo exitoso pero no cambiar estado
            assert response.status_code == 200
            assert response.json()["success"] is True
            assert response.json()["data"]["state"] == 6

            # Validar en base de datos
            db.refresh(lot)
            assert lot.state == 6

        # Limpieza
        db.query(PropertyLot).filter_by(lot_id=lot.id).delete()
        db.delete(lot)
        db.query(PropertyUser).filter_by(property_id=property_.id, user_id=user.id).delete()
        db.delete(property_)
        db.delete(user)
        db.commit()

    finally:
        db.close()
