import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from app.main import app
from app.database import SessionLocal
from app.my_company.models import PaymentInterval
from app.property_routes.models import Lot
import random
import string

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
    """Fixture para crear un intervalo de pago si no existe"""
    # Generar un nombre único para evitar conflictos con la restricción de unicidad
    unique_name = "Mensual_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

    # Verificar si ya existe un intervalo de pago con el nombre generado
    existing_interval = db.query(PaymentInterval).filter(PaymentInterval.name == unique_name).first()
    if not existing_interval:
        interval = PaymentInterval(
            name=unique_name,
            interval_days=30
        )
        db.add(interval)
        db.commit()
        db.refresh(interval)
        return interval
    else:
        return existing_interval  # Devolver el intervalo existente si ya está en la base de datos

@pytest.mark.asyncio
async def test_create_payment_interval(db: Session, payment_interval: PaymentInterval):
    # Verificar si el intervalo de pago ya existe antes de la prueba
    existing = db.query(PaymentInterval).filter(PaymentInterval.name == payment_interval.name).first()
    if existing:
        # No eliminamos el intervalo si está siendo referenciado por otro registro
        if not db.query(Lot).filter(Lot.payment_interval == existing.id).first():  # Usamos `existing.id` en lugar de `existing`
            db.delete(existing)
            db.commit()  # Solo eliminar si no está siendo referenciado

    # Crear un nuevo intervalo de pago con datos válidos
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Datos del intervalo de pago
        payment_interval_data = {
            "name": payment_interval.name,
            "interval_days": 30
        }
        
        # Realizar la solicitud para crear el intervalo de pago
        response = await client.post("/my-company/payment-intervals", json=payment_interval_data)
        
        # Validaciones
        assert response.status_code == 201, response.text
        interval = response.json()["data"]
        
        assert "id" in interval
        assert interval["name"] == payment_interval_data["name"]
        assert interval["interval_days"] == payment_interval_data["interval_days"]

    # 🧹 Limpieza: eliminar el intervalo de pago creado si fue necesario
    created_interval = db.query(PaymentInterval).filter(PaymentInterval.name == payment_interval_data["name"]).first()
    if created_interval:
        # Solo eliminar el intervalo si no está siendo referenciado
        if not db.query(Lot).filter(Lot.payment_interval == created_interval.id).first():
            try:
                db.delete(created_interval)
                db.commit()
            except Exception as e:
                print(f"Error al intentar eliminar el intervalo de pago: {e}")
