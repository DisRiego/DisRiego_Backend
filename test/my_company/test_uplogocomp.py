import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from app.main import app
from app.database import SessionLocal
from app.my_company.models import Company, ColorPalette, DigitalCertificate, CompanyCertificate
from datetime import date, timedelta
import random
import os

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
async def test_update_company_logo(db: Session):
    # 🔁 Eliminar empresa previa si existe
    existing = db.query(Company).first()
    if existing:
        db.query(CompanyCertificate).filter_by(company_id=existing.id).delete()
        db.delete(existing)
        db.commit()

    # 🎨 Crear paleta de colores
    palette = ColorPalette(
        primary_color="#111111",
        secondary_color="#222222",
        tertiary_color="#333333",
        primary_text="#444444",
        secondary_text="#555555",
        background_color="#666666",
        border_color="#777777"
    )
    db.add(palette)
    db.commit()
    db.refresh(palette)

    # 📄 Crear certificado digital real
    serial_number = random.randint(10000000, 99999999)
    nit = random.randint(100000000, 999999999)
    start_date = date.today()
    expiration_date = start_date + timedelta(days=365)

    transport = ASGITransport(app=app)
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
            certificate_id = cert_response.json()["data"]["id"]

        # 🏢 Crear empresa con ese certificado
        with open(VALID_LOGO, "rb") as logo_file:
            company_response = await client.post("/my-company/company", data={
                "name": "Empresa Inicial",
                "nit": str(nit),
                "email": "empresa@logo.com",
                "phone": "3200000000",
                "country": "Colombia",
                "state": "Cundinamarca",
                "city": "Bogotá",
                "address": "Calle Falsa 123",
                "color_palette_id": str(palette.id),
                "digital_certificate_id": str(certificate_id)
            }, files={
                "logo": ("logo_test.png", logo_file, "image/png")
            })

            assert company_response.status_code == 201, company_response.text

        # 🔄 Actualizar solo el logo de la empresa
        with open(VALID_LOGO, "rb") as new_logo_file:
            update_response = await client.patch("/my-company/company/logo", files={
                "logo": ("logo_test.png", new_logo_file, "image/png")
            })

            assert update_response.status_code == 200, update_response.text
            update_data = update_response.json()
            assert update_data["success"] is True
            assert "data" in update_data
            assert update_data["data"].endswith(".png") or update_data["data"].startswith("http")

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
