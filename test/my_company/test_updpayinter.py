import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from app.main import app
from app.database import SessionLocal
from app.my_company.models import PaymentInterval
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
async def test_update_payment_interval(db: Session, payment_interval: PaymentInterval):
    # Verificar que el intervalo de pago que vamos a actualizar exista
    existing_interval = db.query(PaymentInterval).filter(PaymentInterval.id == payment_interval.id).first()
    if not existing_interval:
        pytest.fail(f"Intervalo de pago con ID {payment_interval.id} no encontrado en la base de datos")

    # Datos para actualizar el intervalo de pago
    updated_data = {
        "name": f"Mensual_Actualizado_{random.randint(1000, 9999)}",  # Cambiar el nombre para asegurar que es un cambio    
        "interval_days": 45  # Cambiar los días del intervalo
    }

    # Crear un cliente para realizar la solicitud PUT al endpoint
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Realizar la solicitud PUT para actualizar el intervalo de pago
        response = await client.put(f"/my-company/payment-intervals/{payment_interval.id}", json=updated_data)
        
        # Validaciones
        assert response.status_code == 200, response.text
        interval = response.json()["data"]
        
        assert "id" in interval
        assert interval["id"] == payment_interval.id
        assert interval["name"] == updated_data["name"]
        assert interval["interval_days"] == updated_data["interval_days"]

    # Verificación adicional en la base de datos después de la actualización
    # Refrescar la instancia para obtener los datos actualizados
    db.refresh(existing_interval)

    updated_interval = db.query(PaymentInterval).filter(PaymentInterval.id == payment_interval.id).first()
    assert updated_interval is not None, "Intervalo de pago no encontrado después de la actualización"
    assert updated_interval.name == updated_data["name"], "El nombre del intervalo no se actualizó correctamente"
    assert updated_interval.interval_days == updated_data["interval_days"], "Los días del intervalo no se actualizaron correctamente"
