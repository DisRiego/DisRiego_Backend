import pytest
import random
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import SessionLocal
from app.users.models import User
from app.property_routes.models import Property, PropertyUser, Lot, PropertyLot

@pytest.mark.asyncio
async def test_activate_lot_in_active_property():
    db = SessionLocal()
    try:
        # Crear usuario
        user = User(
            name="LoteActivo",
            first_last_name="Prueba",
            second_last_name="Usuario",
            document_number=str(random.randint(100000000, 999999999)),
            type_document_id=1
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Crear predio con estado ACTIVO (3)
        property_ = Property(
            name="Predio Activo",
            longitude=-75.0,
            latitude=6.0,
            extension=300,
            real_estate_registration_number=random.randint(10000000, 99999999),
            public_deed="https://url.test/deed.pdf",
            freedom_tradition_certificate="https://url.test/cert.pdf",
            state=3  # Correcto para predio activo
        )
        db.add(property_)
        db.commit()
        db.refresh(property_)

        db.add(PropertyUser(user_id=user.id, property_id=property_.id))
        db.commit()

        # Crear lote con estado INACTIVO (6)
        lot = Lot(
            name="Lote de Prueba Activo",
            longitude=-75.2,
            latitude=6.1,
            extension=150,
            real_estate_registration_number=random.randint(10000000, 99999999),
            state=6  # Correcto para lote inactivo
        )
        db.add(lot)
        db.commit()
        db.refresh(lot)

        db.add(PropertyLot(property_id=property_.id, lot_id=lot.id))
        db.commit()

        # Activar lote vía API
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(f"/properties/lot/{lot.id}/state", data={
                "new_state": True  # Activar
            })

            assert response.status_code == 200
            assert response.json()["success"] is True

        # Verificar que el lote ahora esté activo (5)
        db.refresh(lot)
        assert lot.state == 5

        # Limpieza
        db.query(PropertyLot).filter_by(lot_id=lot.id).delete()
        db.delete(lot)
        db.query(PropertyUser).filter_by(property_id=property_.id, user_id=user.id).delete()
        db.delete(property_)
        db.delete(user)
        db.commit()

    finally:
        db.close()
