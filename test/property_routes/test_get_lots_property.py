import pytest
import json
from app.property_routes.services import PropertyLotService
from app.database import SessionLocal
from app.property_routes.models import Lot, PropertyLot, Property
from fastapi.responses import JSONResponse

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

def test_get_lots_property_success(service, db):
    """Prueba obtener los lotes asociados a un predio existente"""

    # 1️⃣ Verificar si hay un predio en la base de datos
    property_id = 1  # Asegurar que este ID existe en la tabla `property`
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        property = Property(
            id=property_id,
            name="Predio Test",
            longitude=100.0,
            latitude=50.0,
            extension=1000.0,
            real_estate_registration_number=123456789,
            public_deed="test_deed.pdf",
            freedom_tradition_certificate="test_certificate.pdf",
        )
        db.add(property)
        db.commit()

    # 2️⃣ Crear un lote y asociarlo al predio si no existe
    lot = db.query(Lot).filter(Lot.id == 2).first()  # Revisar si ya hay un lote con id=2
    if not lot:
        lot = Lot(
            id=2,  # Asegurar que este ID es válido y no genera conflictos
            name="Lote Test",
            extension=500.0,
            latitude=10.0,
            longitude=20.0,
            payment_interval=30,
            type_crop_id=1,
            planting_date="2024-01-01",
            estimated_harvest_date="2024-06-01",
            real_estate_registration_number="123456789",
            public_deed="test_lot_deed.pdf",
            freedom_tradition_certificate="test_lot_certificate.pdf"
        )
        db.add(lot)
        db.commit()

    # 3️⃣ Asociar el lote con el predio en `property_lot` si no existe
    property_lot = db.query(PropertyLot).filter(
        PropertyLot.property_id == property_id,
        PropertyLot.lot_id == lot.id
    ).first()
    if not property_lot:
        property_lot = PropertyLot(property_id=property_id, lot_id=lot.id)
        db.add(property_lot)
        db.commit()

    # 4️⃣ Llamar a `get_lots_property()`
    response = service.get_lots_property(property_id=property_id)

    # 5️⃣ Verificar la respuesta
    assert response.status_code == 200
    json_response = json.loads(response.body.decode("utf-8"))

    assert json_response["success"] is True
    assert isinstance(json_response["data"], list)
    assert any(l["id"] == lot.id for l in json_response["data"])

def test_get_lots_property_empty(service):
    """Prueba obtener lotes cuando un predio no tiene ninguno asociado"""
    response = service.get_lots_property(property_id=999)  # Un ID que no existe

    assert response.status_code == 404
    json_response = json.loads(response.body.decode("utf-8"))

    assert json_response["success"] is False
    assert json_response["data"] == []

def test_get_lots_property_server_error(service, mocker):
    """Simula un error en la base de datos al obtener lotes de un predio"""
    mocker.patch.object(service.db, "query", side_effect=Exception("Simulated DB error"))

    response = service.get_lots_property(property_id=1)
    
    assert response.status_code == 500
    json_response = json.loads(response.body.decode("utf-8"))

    assert json_response["success"] is False
    assert "Error al obtener los lotes" in json_response["data"]["message"]
