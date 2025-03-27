import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from app.main import app
from app.database import SessionLocal
from app.my_company.models import TypeCrop, PaymentInterval
import random

# Para los datos de prueba
@pytest.fixture()
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture()
def payment_interval(db: Session):
    """Fixture para crear un intervalo de pago necesario para el tipo de cultivo"""
    # Verificar si ya existe el intervalo de pago "Mensual"
    existing_interval = db.query(PaymentInterval).filter(PaymentInterval.name == "Mensual").first()
    if not existing_interval:
        interval = PaymentInterval(
            name="Mensual",
            interval_days=30
        )
        db.add(interval)
        db.commit()
        db.refresh(interval)
        return interval
    else:
        return existing_interval  # Devolver el intervalo existente si ya está en la base de datos

@pytest.fixture()
def type_crop_data():
    """Datos de prueba para el tipo de cultivo"""
    return {
        "name": "Tomate",
        "harvest_time": 90,  # 3 meses
        "payment_interval_id": 1  # Usaremos un intervalo de pago válido
    }

@pytest.fixture()
def updated_type_crop_data():
    """Datos actualizados para el tipo de cultivo"""
    return {
        "name": "Tomate Actualizado",
        "harvest_time": 120,  # 4 meses
        "payment_interval_id": 1  # Usaremos el mismo intervalo de pago
    }

@pytest.mark.asyncio
async def test_update_type_crop(db: Session, type_crop_data: dict, updated_type_crop_data: dict, payment_interval: PaymentInterval):
    # 🔁 Forzar que no exista el tipo de cultivo antes de la prueba
    existing = db.query(TypeCrop).filter(TypeCrop.name == type_crop_data["name"]).first()
    if existing:
        db.delete(existing)
        db.commit()

    # Crear un tipo de cultivo utilizando los datos de prueba
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Usamos el intervalo de pago previamente creado
        type_crop_data["payment_interval_id"] = payment_interval.id
        
        # Realizar la solicitud para crear el tipo de cultivo
        response = await client.post("/my-company/type-crops", json=type_crop_data)
        
        # Validaciones para la creación
        assert response.status_code == 201, response.text
        created_type_crop = response.json()["data"]
        
        assert "id" in created_type_crop
        assert created_type_crop["name"] == type_crop_data["name"]
        assert created_type_crop["harvest_time"] == type_crop_data["harvest_time"]
        assert created_type_crop["payment_interval_id"] == payment_interval.id

        # Obtener el ID del tipo de cultivo recién creado
        type_crop_id = created_type_crop["id"]
        
        # Realizar la actualización de los datos del tipo de cultivo
        response = await client.put(f"/my-company/type-crops/{type_crop_id}", json=updated_type_crop_data)
        
        # Validaciones para la actualización
        assert response.status_code == 200, response.text
        updated_type_crop = response.json()["data"]
        
        assert updated_type_crop["id"] == type_crop_id
        assert updated_type_crop["name"] == updated_type_crop_data["name"]
        assert updated_type_crop["harvest_time"] == updated_type_crop_data["harvest_time"]
        assert updated_type_crop["payment_interval_id"] == updated_type_crop_data["payment_interval_id"]

    # 🧹 Limpieza: eliminar el tipo de cultivo creado
    created_type_crop = db.query(TypeCrop).filter(TypeCrop.name == type_crop_data["name"]).first()
    if created_type_crop:
        db.delete(created_type_crop)
        db.commit()
