import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from app.main import app
from app.database import SessionLocal
from app.my_company.models import DigitalCertificate
from datetime import date, timedelta
import random
import os

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
async def test_get_certificate_by_id(db: Session):
    # 🔁 Limpiar certificados anteriores si es necesario
    serial_number = random.randint(10000000, 99999999)
    nit = random.randint(100000000, 999999999)
    start_date = date.today()
    expiration_date = start_date + timedelta(days=365)

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 📄 Subir certificado para luego probar su obtención
        with open(VALID_CERT, "rb") as cert_file:
            cert_response = await client.post("/my-company/certificates", data={
                "serial_number": str(serial_number),
                "start_date": str(start_date),
                "expiration_date": str(expiration_date),
                "nit": str(nit)
            }, files={
                "certificate_file": ("valid_certificate.pdf", cert_file, "application/pdf")
            })

        assert cert_response.status_code == 201, cert_response.text
        cert_data = cert_response.json()["data"]
        certificate_id = cert_data["id"]

        # ✅ Probar obtención del certificado por ID
        get_response = await client.get(f"/my-company/certificates/{certificate_id}")
        assert get_response.status_code == 200, get_response.text

        get_data = get_response.json()
        assert get_data["success"] is True
        assert get_data["data"]["id"] == certificate_id
        assert get_data["data"]["serial_number"] == serial_number
        assert get_data["data"]["nit"] == nit
        assert "attached" in get_data["data"]
        assert get_data["data"]["attached"].endswith(".pdf")

    # 🧹 Limpieza de base de datos
    cert_obj = db.query(DigitalCertificate).filter_by(id=certificate_id).first()
    if cert_obj:
        db.delete(cert_obj)
        db.commit()
