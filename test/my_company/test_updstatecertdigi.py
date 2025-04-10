import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from datetime import date, timedelta
import os
import random

from app.main import app
from app.database import SessionLocal
from app.my_company.models import DigitalCertificate

# Ruta al archivo de certificado de prueba
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
async def test_update_certificate_status_to_inactive(db: Session):
    # Crear cliente de prueba
    transport = ASGITransport(app=app)
    serial_number = random.randint(10000000, 99999999)
    nit = random.randint(100000000, 999999999)
    start_date = date.today()
    expiration_date = start_date + timedelta(days=365)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Crear certificado digital
        with open(VALID_CERT, "rb") as cert_file:
            cert_response = await client.post("/my-company/certificates", data={
                "serial_number": str(serial_number),
                "start_date": str(start_date),
                "expiration_date": str(expiration_date),
                "nit": str(nit)
            }, files={
                "certificate_file": ("valid_certificate.pdf", cert_file, "application/pdf")
            })

        assert cert_response.status_code == 201
        cert_data = cert_response.json()["data"]
        certificate_id = cert_data["id"]

        # Verificar que el estado inicial sea Activo (9)
        cert_in_db = db.query(DigitalCertificate).filter_by(id=certificate_id).first()
        assert cert_in_db is not None
        assert cert_in_db.status_id == 9  # default actual

        # Actualizar estado a Inactivo (10)
        status_response = await client.patch(
            f"/my-company/certificates/{certificate_id}/status",
            data={"new_status": 10}
        )

        assert status_response.status_code == 200, status_response.text
        response_data = status_response.json()
        assert response_data["success"] is True
        assert response_data["data"]["status_id"] == 10
        assert response_data["data"]["nombre_estado"] == "Inactivo"

    # Limpieza
    cert = db.query(DigitalCertificate).filter_by(id=certificate_id).first()
    if cert:
        db.delete(cert)
        db.commit()
