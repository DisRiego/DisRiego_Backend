import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from app.main import app
from app.database import SessionLocal
from app.my_company.models import TypeCrop, PaymentInterval


@pytest.fixture()
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def payment_interval(db: Session):
    existing_interval = db.query(PaymentInterval).filter(PaymentInterval.name == "Mensual").first()
    if not existing_interval:
        interval = PaymentInterval(name="Mensual", interval_days=30)
        db.add(interval)
        db.commit()
        db.refresh(interval)
        return interval
    return existing_interval


@pytest.fixture()
def type_crop_data(payment_interval: PaymentInterval):
    return {
        "name": "Tomate",
        "harvest_time": 90,
        "payment_interval_id": payment_interval.id
    }


@pytest.mark.asyncio
async def test_update_type_crop_state(db: Session, type_crop_data: dict):
    # 🧽 Eliminar si ya existe
    existing = db.query(TypeCrop).filter(TypeCrop.name == type_crop_data["name"]).first()
    if existing:
        db.delete(existing)
        db.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Crear tipo de cultivo
        response = await client.post("/my-company/type-crops", json=type_crop_data)
        assert response.status_code == 201, response.text
        created_type_crop = response.json()["data"]
        type_crop_id = created_type_crop["id"]

        # Verificamos creación
        assert created_type_crop["name"] == type_crop_data["name"]

        # Cambiar estado a 8 (inactivo)
        response = await client.patch(
            f"/my-company/type-crops/{type_crop_id}/state",
            data={"new_state": 8}  
        )
        assert response.status_code == 200, response.text
        updated_type_crop = response.json()["data"]
        assert updated_type_crop["state_id"] == 8

        # Confirmar en la base de datos
        type_crop_in_db = db.query(TypeCrop).filter(TypeCrop.id == type_crop_id).first()
        assert type_crop_in_db.state_id == 8

    # 🧹 Limpieza
    to_delete = db.query(TypeCrop).filter(TypeCrop.id == type_crop_id).first()
    if to_delete:
        db.delete(to_delete)
        db.commit()
