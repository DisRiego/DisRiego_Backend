import pytest
import json
from sqlalchemy.sql import text  # 🔹 Para ejecutar consultas SQL sin problemas
from fastapi.testclient import TestClient
from app.property_routes.services import PropertyLotService
from app.database import SessionLocal
from app.property_routes.models import Lot, PropertyLot, Property
from app.main import app

@pytest.fixture(scope="module")
def client():
    """Cliente de prueba para interactuar con la API."""
    return TestClient(app)

@pytest.fixture(scope="module")
def db():
    """Fixture para manejar una sesión de base de datos para las pruebas."""
    db = SessionLocal()
    yield db
    db.rollback()
    db.close()

@pytest.fixture()
def service(db):
    """Crear una instancia del servicio para pruebas."""
    return PropertyLotService(db)

@pytest.fixture()
def setup_test_property_and_lot(db):
    """Crea un predio y un lote de prueba si no existen."""
    property_id = 1
    lot_id = 2

    # 🔹 Asegurar que el predio existe
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

    # 🔹 Asegurar que el lote existe
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not lot:
        lot = Lot(
            id=lot_id,
            name="Lote Test",
            extension=500.0,
            latitude=10.0,
            longitude=20.0,
            real_estate_registration_number=123456789,
            public_deed="test_lot_deed.pdf",
            freedom_tradition_certificate="test_lot_certificate.pdf"
        )
        db.add(lot)
        db.commit()

    # 🔹 Asociar el lote con el predio si no está asociado
    property_lot = db.query(PropertyLot).filter(
        PropertyLot.property_id == property_id,
        PropertyLot.lot_id == lot_id
    ).first()

    if not property_lot:
        property_lot = PropertyLot(property_id=property_id, lot_id=lot_id)
        db.add(property_lot)
        db.commit()

    yield property_id, lot_id

    # 🔹 Limpieza de los datos después de la prueba
    db.execute(text("DELETE FROM property_lot WHERE property_id = :property_id"), {"property_id": property_id})
    db.execute(text("DELETE FROM lot WHERE id = :lot_id"), {"lot_id": lot_id})
    db.execute(text("DELETE FROM property WHERE id = :property_id"), {"property_id": property_id})
    db.commit()

def test_get_lots_property_success(service, setup_test_property_and_lot):
    """Prueba obtener los lotes asociados a un predio existente."""
    property_id, lot_id = setup_test_property_and_lot

    # 🔹 Llamar a `get_lots_property()`
    response = service.get_lots_property(property_id=property_id)

    # 🔹 Verificar la respuesta
    assert response.status_code == 200
    json_response = json.loads(response.body.decode("utf-8"))

    assert json_response["success"] is True
    assert isinstance(json_response["data"], list)
    assert any(l["id"] == lot_id for l in json_response["data"])

def test_get_lots_property_empty(service):
    """Prueba obtener lotes cuando un predio no tiene ninguno asociado."""
    response = service.get_lots_property(property_id=999)  # Un ID que no existe

    assert response.status_code == 404
    json_response = json.loads(response.body.decode("utf-8"))

    assert json_response["success"] is False
    assert json_response["data"] == []

def test_get_lots_property_server_error(service, mocker):
    """Simula un error en la base de datos al obtener lotes de un predio."""
    mocker.patch.object(service.db, "query", side_effect=Exception("Simulated DB error"))

    response = service.get_lots_property(property_id=1)

    assert response.status_code == 500
    json_response = json.loads(response.body.decode("utf-8"))

    assert json_response["success"] is False
    assert "Error al obtener los lotes" in json_response["data"]["message"]
