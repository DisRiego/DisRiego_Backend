import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from app.main import app
from app.database import SessionLocal
from app.my_company.models import DigitalCertificate
from app.roles.models import Vars
from datetime import date, timedelta
import os
import random

# Archivos de prueba
FILES_DIR = "files"
VALID_CERT = os.path.join(FILES_DIR, "valid_certificate.pdf")

@pytest.fixture()
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.mark.asyncio
async def test_update_digital_certificate(db: Session):
    # 🧩 Asegurar que exista el estado Activo (id=22)
    active_status = db.query(Vars).filter(Vars.id == 22).first()
    if not active_status:
        active_status = Vars(id=22, name="Activo", type="estado_certificado")
        db.add(active_status)
        db.commit()

    # Crear un certificado original para luego actualizarlo
    original_serial = random.randint(10000000, 99999999)
    original_nit = random.randint(100000000, 999999999)
    start_date = date.today()
    expiration_date = start_date + timedelta(days=365)

    original_certificate = DigitalCertificate(
        serial_number=original_serial,
        start_date=start_date,
        expiration_date=expiration_date,
        attached="mock/path/original_cert.pdf",
        nit=original_nit,
        status_id=22  # Activo
    )
    db.add(original_certificate)
    db.commit()
    db.refresh(original_certificate)

    # Datos nuevos para actualización
    updated_serial = random.randint(10000000, 99999999)
    updated_nit = random.randint(100000000, 999999999)
    updated_start = start_date + timedelta(days=1)
    updated_exp = expiration_date + timedelta(days=30)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with open(VALID_CERT, "rb") as cert_file:
            response = await client.put(f"/my-company/certificates/{original_certificate.id}", data={
                "serial_number": str(updated_serial),
                "start_date": str(updated_start),
                "expiration_date": str(updated_exp),
                "nit": str(updated_nit)
            }, files={
                "certificate_file": ("valid_certificate.pdf", cert_file, "application/pdf")
            })

    assert response.status_code == 200, response.text
    json_response = response.json()
    assert json_response["success"] is True
    assert json_response["message"] == "Certificado actualizado correctamente"
    data = json_response["data"]
    assert data["serial_number"] == updated_serial
    assert data["nit"] == updated_nit

    # 🧹 Limpieza
    cert = db.query(DigitalCertificate).filter_by(id=original_certificate.id).first()
    if cert:
        db.delete(cert)
        db.commit()
