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
async def test_delete_certificate(db: Session):
    # 📅 Crear datos válidos
    serial_number = random.randint(10000000, 99999999)
    nit = random.randint(100000000, 999999999)
    start_date = date.today()
    expiration_date = start_date + timedelta(days=365)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 📄 Crear certificado real
        with open(VALID_CERT, "rb") as cert_file:
            response = await client.post("/my-company/certificates", data={
                "serial_number": str(serial_number),
                "start_date": str(start_date),
                "expiration_date": str(expiration_date),
                "nit": str(nit)
            }, files={
                "certificate_file": ("valid_certificate.pdf", cert_file, "application/pdf")
            })

            assert response.status_code == 201, response.text
            cert_data = response.json()["data"]
            certificate_id = cert_data["id"]

        # ✅ Verificar que el certificado fue creado en la base de datos
        cert_in_db = db.query(DigitalCertificate).filter_by(id=certificate_id).first()
        assert cert_in_db is not None

        # 🗑️ Eliminar el certificado
        delete_response = await client.delete(f"/my-company/certificates/{certificate_id}")
        assert delete_response.status_code == 200, delete_response.text
        delete_data = delete_response.json()
        assert delete_data["success"] is True
        assert delete_data["message"] == "Certificado eliminado correctamente"

        # 🧪 Verificar que fue eliminado de la base de datos
        cert_after_delete = db.query(DigitalCertificate).filter_by(id=certificate_id).first()
        assert cert_after_delete is None
