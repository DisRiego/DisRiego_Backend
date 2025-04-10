import pytest
import random
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import SessionLocal
from app.users.models import User
from app.property_routes.models import Property, PropertyUser, Lot, PropertyLot

# Estados correctos según tu lógica de negocio
STATE_PROPERTY_ACTIVE = 3
STATE_LOT_ACTIVE = 5

@pytest.mark.asyncio
async def test_activate_already_active_lot():
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

        # Crear predio con estado activo (state = 3)
        property_ = Property(
            name="Predio Activo",
            longitude=-75.0,
            latitude=6.0,
            extension=300,
            real_estate_registration_number=random.randint(10000000, 99999999),
            public_deed="https://url.test/deed.pdf",
            freedom_tradition_certificate="https://url.test/cert.pdf",
            state=STATE_PROPERTY_ACTIVE
        )
        db.add(property_)
        db.commit()
        db.refresh(property_)

        # Relacionar usuario con predio
        db.add(PropertyUser(user_id=user.id, property_id=property_.id))
        db.commit()

        # Crear lote con estado activo (state = 5)
        lot = Lot(
            name="Lote de Prueba Activo",
            longitude=-75.2,
            latitude=6.1,
            extension=150,
            real_estate_registration_number=random.randint(10000000, 99999999),
            state=STATE_LOT_ACTIVE
        )
        db.add(lot)
        db.commit()
        db.refresh(lot)

        # Relacionar lote con predio
        db.add(PropertyLot(property_id=property_.id, lot_id=lot.id))
        db.commit()

        # Intentar activar el lote nuevamente
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(f"/properties/lot/{lot.id}/state", data={"new_state": True})

            # Debe devolver 400 porque el lote ya está activo
            assert response.status_code == 400
            assert "ya está activo" in response.json()["detail"].lower() or \
                   "no se puede activar" in response.json()["detail"].lower()

        # Limpieza
        db.query(PropertyLot).filter_by(lot_id=lot.id).delete()
        db.delete(lot)
        db.query(PropertyUser).filter_by(property_id=property_.id, user_id=user.id).delete()
        db.delete(property_)
        db.delete(user)
        db.commit()

    finally:
        db.close()
