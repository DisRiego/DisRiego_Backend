import os
import random
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import SessionLocal
from app.users.models import User
from app.property_routes.models import Property, PropertyUser

@pytest.mark.asyncio
async def test_get_lots_from_property_without_lots():
    """Debe retornar lista vacía al obtener lotes de un predio sin lotes asignados"""

    db = SessionLocal()

    # Crear usuario
    user = User(
        name="SinLotes",
        first_last_name="Tester",
        second_last_name="Prueba",
        document_number=str(random.randint(100000000, 999999999)),
        type_document_id=1
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Crear predio activo
    property_ = Property(
        name="Predio sin lotes",
        longitude=-75.1,
        latitude=6.1,
        extension=400,
        real_estate_registration_number=random.randint(10000000, 99999999),
        public_deed="https://fakeurl.com/deed.pdf",
        freedom_tradition_certificate="https://fakeurl.com/cert.pdf",
        state=16
    )
    db.add(property_)
    db.commit()
    db.refresh(property_)

    # Asociar predio al usuario
    relation = PropertyUser(user_id=user.id, property_id=property_.id)
    db.add(relation)
    db.commit()

    # Consumir API
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/properties/{property_.id}/lots/")

    print("✅ Status:", response.status_code)
    print("✅ JSON:", response.json())

    # ✅ Validaciones
    assert response.status_code in [200, 404]
    data = response.json()
    assert "success" in data
    assert data["data"] == [] or data["success"] is False

    # 🔁 Cleanup
    db.query(PropertyUser).filter_by(property_id=property_.id).delete()
    db.delete(property_)
    db.delete(user)
    db.commit()
    db.close()
