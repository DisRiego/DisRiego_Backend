import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from app.main import app
from app.database import SessionLocal
from app.my_company.models import DigitalCertificate
from datetime import date, timedelta
import os
import random

# Ruta del archivo de prueba PDF
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
async def test_create_digital_certificate(db: Session):
    # 🔢 Datos aleatorios válidos para el certificado
    serial_number = random.randint(10000000, 99999999)
    nit = random.randint(100000000, 999999999)
    start_date = date.today()
    expiration_date = start_date + timedelta(days=365)

    # 📡 Cliente HTTP usando el ASGITransport
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with open(VALID_CERT, "rb") as cert_file:
            response = await client.post("/my-company/certificates", data={
                "serial_number": str(serial_number),
                "start_date": str(start_date),
                "expiration_date": str(expiration_date),
                "nit": str(nit)
            }, files={
                "certificate_file": ("valid_certificate.pdf", cert_file, "application/pdf")
            })

    # ✅ Verificaciones de respuesta
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["success"] is True
    assert "data" in body
    cert_data = body["data"]
    assert cert_data["serial_number"] == serial_number
    assert cert_data["nit"] == nit
    assert cert_data["attached"].startswith("http")

    # 🧹 Limpieza: eliminar el certificado creado
    certificate = db.query(DigitalCertificate).filter_by(serial_number=serial_number).first()
    if certificate:
        db.delete(certificate)
        db.commit()
