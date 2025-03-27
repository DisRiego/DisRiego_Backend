import pytest
import random
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import SessionLocal
from app.users.models import User
from app.property_routes.models import Property, PropertyUser, Lot, PropertyLot
from app.roles.models import Vars
from app.firebase_config import FIREBASE_STORAGE_BUCKET

VALID_DEED = "files/public_deed.pdf"
VALID_CERT = "files/freedom_certificate.pdf"

@pytest.mark.asyncio
async def test_deactivate_already_inactive_lot():
    db = SessionLocal()
    try:
        # Crear usuario
        user = User(
            name="LoteInactivo",
            first_last_name="Prueba",
            second_last_name="Usuario",
            document_number=str(random.randint(100000000, 999999999)),  # Aseguramos un valor de 9 dígitos
            type_document_id=1
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Crear predio (Aseguramos que el predio tenga estado 16 para que esté activo)
        property_ = Property(
            name="Predio Activo",
            longitude=-75.0,
            latitude=6.0,
            extension=300,
            real_estate_registration_number=random.randint(10000000, 99999999),
            public_deed="https://url.test/deed.pdf",
            freedom_tradition_certificate="https://url.test/cert.pdf",
            state=16  # Estado 16 significa activo
        )
        db.add(property_)
        db.commit()
        db.refresh(property_)

        # Relacionar usuario con predio
        db.add(PropertyUser(user_id=user.id, property_id=property_.id))
        db.commit()

        # Crear lote con estado 19 (inactivo) y asociarlo al predio
        lot = Lot(
            name="Lote de Prueba Inactivo",
            longitude=-75.2,
            latitude=6.1,
            extension=150,
            real_estate_registration_number=random.randint(10000000, 99999999),  # Aseguramos valor de 9 dígitos
            state=19  # Estado 19 significa inactivo
        )
        db.add(lot)
        db.commit()
        db.refresh(lot)

        # Relacionar lote con predio
        property_lot = PropertyLot(
            property_id=property_.id,
            lot_id=lot.id
        )
        db.add(property_lot)
        db.commit()

        # Intentar desactivar el lote nuevamente (lo cual no debería ser permitido porque ya está inactivo)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(f"/properties/lot/{lot.id}/state", data={
                "new_state": False  # Intentamos desactivar el lote que ya está inactivo
            })

            # Verificamos que la respuesta sea exitosa (estado 200) y que el lote no haya cambiado de estado
            assert response.status_code == 200
            assert response.json()["data"]["state"] == 19  # El lote debería seguir inactivo (19)

            # Verificar que el estado del lote siga siendo inactivo
            db.refresh(lot)
            assert lot.state == 19  # Verificamos que el lote siga inactivo

        # Limpieza
        db.query(PropertyLot).filter_by(lot_id=lot.id).delete()
        db.delete(lot)
        db.query(PropertyUser).filter_by(property_id=property_.id, user_id=user.id).delete()
        db.delete(property_)
        db.delete(user)
        db.commit()

    finally:
        db.close()
