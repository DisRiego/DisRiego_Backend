import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from app.main import app
from app.database import SessionLocal
from app.my_company.models import Company, ColorPalette, DigitalCertificate, CompanyCertificate
from datetime import date, timedelta
import random
import os

# Archivos de prueba
FILES_DIR = "files"
VALID_LOGO = os.path.join(FILES_DIR, "logo_test.png")
VALID_CERT = os.path.join(FILES_DIR, "valid_certificate.pdf")

@pytest.fixture()
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.mark.asyncio
async def test_create_company_with_real_certificate(db: Session):
    # 🔁 Forzar que no exista empresa antes de iniciar la prueba
    existing = db.query(Company).first()
    if existing:
        db.query(CompanyCertificate).filter_by(company_id=existing.id).delete()
        db.delete(existing)
        db.commit()

    # 🎨 Crear paleta de colores temporal
    palette = ColorPalette(
        primary_color="#101010",
        secondary_color="#202020",
        tertiary_color="#303030",
        primary_text="#404040",
        secondary_text="#505050",
        background_color="#606060",
        border_color="#707070"
    )
    db.add(palette)
    db.commit()
    db.refresh(palette)

    # 📄 Crear certificado real y subirlo vía API
    transport = ASGITransport(app=app)
    serial_number = random.randint(10000000, 99999999)
    nit = random.randint(100000000, 999999999)
    start_date = date.today()
    expiration_date = start_date + timedelta(days=365)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
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

        # 🏢 Crear empresa con ese certificado y logo
        with open(VALID_LOGO, "rb") as logo_file:
            company_response = await client.post("/my-company/company", data={
                "name": "Empresa Real",
                "nit": str(nit),
                "email": "real@empresa.com",
                "phone": "3010001111",
                "country": "Colombia",
                "state": "Valle",
                "city": "Cali",
                "address": "Calle 100",
                "color_palette_id": str(palette.id),
                "digital_certificate_id": str(certificate_id)
            }, files={
                "logo": ("logo_test.png", logo_file, "image/png")
            })

            # ✅ Validaciones adaptadas
            assert company_response.status_code == 201, company_response.text
            company_data = company_response.json()
            assert company_data["success"] is True
            assert "data" in company_data
            # Si se retorna info, validamos el NIT
            if company_data["data"]:
                assert company_data["data"].get("nit") == nit
            else:
                # Si no se retorna info, validamos por la base de datos
                db_company = db.query(Company).filter_by(nit=nit).first()
                assert db_company is not None
                assert db_company.nit == nit

    # 🧹 Limpieza
    company = db.query(Company).filter_by(nit=nit).first()
    if company:
        db.query(CompanyCertificate).filter_by(company_id=company.id).delete()
        db.delete(company)
        db.commit()

    cert = db.query(DigitalCertificate).filter_by(id=certificate_id).first()
    if cert:
        db.delete(cert)
        db.commit()

    db.delete(palette)
    db.commit()
