import pytest
<<<<<<< HEAD
import asyncio
from fastapi import UploadFile
from app.property_routes.services import PropertyLotService
from app.database import SessionLocal
from app.property_routes.models import Lot, PropertyLot, Property
from sqlalchemy import text
from io import BytesIO
import json
import random


@pytest.fixture(scope="function")
def db():
    """Fixture para manejar una sesión de base de datos en pruebas con rollback"""
    db = SessionLocal()
=======
from app.property_routes.services import PropertyLotService
from app.database import SessionLocal
from app.property_routes.models import Lot, PropertyLot

@pytest.fixture(scope="module")
def db():
    """Fixture para crear una nueva sesión de base de datos para las pruebas"""
    db = SessionLocal()
    db.begin()
>>>>>>> origin/develop
    yield db
    db.rollback()
    db.close()

<<<<<<< HEAD

@pytest.fixture()
def service(db):
    """Instancia del servicio PropertyLotService para pruebas"""
    return PropertyLotService(db)


@pytest.fixture()
def setup_property(db):
    """Crea un predio de prueba si no existe y lo retorna"""
    existing_property = db.query(Property).filter_by(name="Predio de Prueba").first()
    
    if not existing_property:
        test_property = Property(
            name="Predio de Prueba",
            longitude=-74.0,
            latitude=4.0,
            extension=1000.0,
            real_estate_registration_number=random.randint(100000, 999999),  # 🔹 Genera un número aleatorio
            public_deed="test_public_deed.pdf",
            freedom_tradition_certificate="test_certificate.pdf",
        )
        db.add(test_property)
        db.commit()
        db.refresh(test_property)
    else:
        test_property = existing_property

    yield test_property

    # 🔹 Limpieza: Eliminar solo el predio si no tiene lotes asociados
    if not db.query(PropertyLot).filter_by(property_id=test_property.id).first():
        db.delete(test_property)
        db.commit()


@pytest.fixture()
def fake_upload_file():
    """Simula archivos para pruebas"""
    return UploadFile(filename="dummy.pdf", file=BytesIO(b"Fake PDF content"))


@pytest.mark.asyncio
async def test_create_and_link_lot(service, db, setup_property, fake_upload_file):
    """✅ Prueba la creación de un lote y su asociación con un predio"""

    property_id = setup_property.id  # Obtener el ID del predio de prueba

    # 🔹 Generar datos únicos para evitar colisiones en la BD
    unique_lot_name = f"Lote Prueba {random.randint(1000, 9999)}"
    unique_real_estate_registration_number = random.randint(100000, 999999)

    # **1️⃣ Crear el lote**
    lot_response = await service.create_lot(
        property_id=property_id,
        name=unique_lot_name,
        longitude=-74.1,
        latitude=4.1,
        extension=500.0,
        real_estate_registration_number=unique_real_estate_registration_number,
        public_deed=fake_upload_file,
        freedom_tradition_certificate=fake_upload_file
    )

    # Convertir el contenido de la respuesta a JSON
    response_data = json.loads(lot_response.body)

    assert lot_response.status_code == 200
    assert response_data["success"] is True

    # **2️⃣ Obtener el lote de la base de datos**
    lot_in_db = db.query(Lot).filter_by(name=unique_lot_name).first()
    assert lot_in_db is not None
    lot_id = lot_in_db.id

    # **3️⃣ Verificar que la relación se guardó en la base de datos**
    property_lot_in_db = db.query(PropertyLot).filter(
        PropertyLot.property_id == property_id, PropertyLot.lot_id == lot_id
    ).first()

    assert property_lot_in_db is not None

    # **4️⃣ Limpieza: Eliminar solo los datos creados en la prueba**
    db.execute(text("DELETE FROM property_lot WHERE lot_id = :lot_id"), {"lot_id": lot_id})
    db.commit()

    db.delete(lot_in_db)
    db.commit()
=======
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
>>>>>>> origin/develop
