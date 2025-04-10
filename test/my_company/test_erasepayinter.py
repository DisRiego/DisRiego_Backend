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
async def test_delete_payment_interval(db: Session, payment_interval: PaymentInterval):
    # Verificar si el intervalo de pago que vamos a eliminar existe
    existing_interval = db.query(PaymentInterval).filter(PaymentInterval.id == payment_interval.id).first()
    if not existing_interval:
        pytest.fail(f"Intervalo de pago con ID {payment_interval.id} no encontrado en la base de datos")

    # Crear un cliente para realizar la solicitud DELETE al endpoint
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Realizar la solicitud DELETE para eliminar el intervalo de pago
        response = await client.delete(f"/my-company/payment-intervals/{payment_interval.id}")
        
        # Validaciones
        assert response.status_code == 200, response.text
        result = response.json()
        
        assert result["success"] is True
        assert result["message"] == "Intervalo de pago eliminado correctamente"

    # Verificación adicional en la base de datos después de la eliminación
    deleted_interval = db.query(PaymentInterval).filter(PaymentInterval.id == payment_interval.id).first()
    assert deleted_interval is None, "Intervalo de pago no fue eliminado correctamente"

    # 🧹 Limpieza: eliminar el intervalo de pago creado si fue necesario
    created_interval = db.query(PaymentInterval).filter(PaymentInterval.name == payment_interval.name).first()
    if created_interval:
        db.delete(created_interval)
        db.commit()
