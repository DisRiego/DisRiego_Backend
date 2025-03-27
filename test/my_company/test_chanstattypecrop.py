import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from app.main import app
from app.database import SessionLocal
from app.my_company.models import TypeCrop, PaymentInterval, Vars

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
def type_crop_data(db: Session, payment_interval: PaymentInterval):
    """Fixture para crear datos de prueba para el tipo de cultivo"""
    return {
        "name": "Tomate",
        "harvest_time": 90,  # 3 meses
        "payment_interval_id": payment_interval.id
    }

@pytest.fixture()
def active_state(db: Session):
    """Fixture para crear un estado activo (20) para el tipo de cultivo"""
    existing_state = db.query(Vars).filter(Vars.id == 20).first()
    if not existing_state:
        state = Vars(id=20, name="Activo")
        db.add(state)
        db.commit()
        db.refresh(state)
        return state
    else:
        return existing_state

@pytest.fixture()
def inactive_state(db: Session):
    """Fixture para crear un estado inactivo (21) para el tipo de cultivo"""
    existing_state = db.query(Vars).filter(Vars.id == 21).first()
    if not existing_state:
        state = Vars(id=21, name="Inactivo")
        db.add(state)
        db.commit()
        db.refresh(state)
        return state
    else:
        return existing_state

@pytest.mark.asyncio
async def test_update_type_crop_state(db: Session, type_crop_data: dict, payment_interval: PaymentInterval, active_state: Vars, inactive_state: Vars):
    # 🔁 Forzar que no exista el tipo de cultivo antes de la prueba
    existing = db.query(TypeCrop).filter(TypeCrop.name == type_crop_data["name"]).first()
    if existing:
        db.delete(existing)
        db.commit()

    # Crear el tipo de cultivo utilizando los datos de prueba
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        type_crop_data["payment_interval_id"] = payment_interval.id
        type_crop_data["state_id"] = active_state.id
        
        # Realizar la solicitud para crear el tipo de cultivo
        response = await client.post("/my-company/type-crops", json=type_crop_data)
        
        # Validaciones para la creación
        assert response.status_code == 201, response.text
        created_type_crop = response.json()["data"]
        type_crop_id = created_type_crop["id"]
        
        # Verificar que el tipo de cultivo ha sido creado con el estado "Activo"
        assert created_type_crop["name"] == type_crop_data["name"]
        assert created_type_crop["state_id"] == active_state.id

        # Realizar la solicitud para cambiar el estado a "Inactivo" (21)
        response = await client.patch(f"/my-company/type-crops/{type_crop_id}/state", data={"new_state": inactive_state.id})

        # Validaciones para la actualización del estado
        assert response.status_code == 200, response.text
        updated_type_crop = response.json()["data"]
        
        assert updated_type_crop["state_id"] == inactive_state.id

        # Verificar que el estado en la base de datos haya cambiado
        type_crop_in_db = db.query(TypeCrop).filter(TypeCrop.id == type_crop_id).first()
        assert type_crop_in_db.state_id == inactive_state.id

    # 🧹 Limpieza: eliminar el tipo de cultivo creado
    created_type_crop = db.query(TypeCrop).filter(TypeCrop.name == type_crop_data["name"]).first()
    if created_type_crop:
        db.delete(created_type_crop)
        db.commit()
