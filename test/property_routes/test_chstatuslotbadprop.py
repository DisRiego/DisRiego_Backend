import pytest
import random
from datetime import date
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
async def test_activate_lot_in_inactive_property():
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

        # Crear predio (Aseguramos que el predio tenga estado 17 para que esté inactivo)
        property_ = Property(
            name="Predio Inactivo",
            longitude=-75.0,
            latitude=6.0,
            extension=300,
            real_estate_registration_number=random.randint(10000000, 99999999),
            public_deed="https://url.test/deed.pdf",
            freedom_tradition_certificate="https://url.test/cert.pdf",
            state=17  # Estado 17 significa inactivo
        )
        db.add(property_)
        db.commit()
        db.refresh(property_)

        # Relacionar usuario con predio
        db.add(PropertyUser(user_id=user.id, property_id=property_.id))
        db.commit()

        # Crear lote y asociarlo al predio
        lot = Lot(
            name="Lote de Prueba Inactivo",
            longitude=-75.2,
            latitude=6.1,
            extension=150,
            real_estate_registration_number=random.randint(10000000, 99999999),  # Aseguramos valor de 9 dígitos
            state=19  # Estado 19 significa inactivo por defecto
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

        # Intentar activar lote via API (se asume que la API está correctamente implementada para manejar la activación)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(f"/properties/lot/{lot.id}/state", data={
                "new_state": True  # Intentamos activar el lote
            })

            # Verificamos si la respuesta fue rechazada (debería ser 400 ya que el predio está inactivo)
            assert response.status_code == 400
            assert "No se puede activar el lote porque el predio está desactivado" in response.json()["detail"]

            # Verificar que el estado del lote no haya cambiado (debe permanecer inactivo)
            db.refresh(lot)
            assert lot.state == 19

        # Limpieza
        db.query(PropertyLot).filter_by(lot_id=lot.id).delete()
        db.delete(lot)
        db.query(PropertyUser).filter_by(property_id=property_.id, user_id=user.id).delete()
        db.delete(property_)
        db.delete(user)
        db.commit()

    finally:
        db.close()
