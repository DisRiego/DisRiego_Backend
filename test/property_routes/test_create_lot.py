import pytest
from app.property_routes.services import PropertyLotService
from app.database import SessionLocal
from app.property_routes.models import Lot, PropertyLot

@pytest.fixture(scope="module")
def db():
    """Fixture para crear una nueva sesión de base de datos para las pruebas"""
    db = SessionLocal()
    db.begin()
    yield db
    db.rollback()
    db.close()

@pytest.fixture()
def service(db):
    """Crear una instancia del servicio para pruebas"""
    return PropertyLotService(db)

def test_create_and_link_lot(service, db):
    """Prueba la creación de un lote y su asociación con un predio"""

    # **1️⃣ Crear el lote**
    lot_response = service.create_lot(name="Lote Prueba", extension=500.0, property_id=1)
    
    assert lot_response["success"] is True
    assert "data" in lot_response
    lot_id = lot_response["data"].id  # Obtener el ID del lote recién creado

    # **2️⃣ Verificar que el lote se guardó en la base de datos**
    lot_in_db = db.query(Lot).filter(Lot.id == lot_id).first()
    assert lot_in_db is not None
    assert lot_in_db.name == "Lote Prueba"

    # **3️⃣ Asociar el lote con un predio**
    link_response = service.link_property_lot(property_id=1, lot_id=lot_id)
    
    assert link_response["success"] is True
    assert link_response["data"] == "Predio y lote asociados correctamente."

    # **4️⃣ Verificar que la relación se guardó en la base de datos**
    property_lot_in_db = db.query(PropertyLot).filter(
        PropertyLot.property_id == 1, PropertyLot.lot_id == lot_id
    ).first()
    
    assert property_lot_in_db is not None
