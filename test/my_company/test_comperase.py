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
async def test_delete_existing_company(db: Session):
    # 🔁 Eliminar empresa previa (si existe)
    existing = db.query(Company).first()
    if existing:
        db.query(CompanyCertificate).filter_by(company_id=existing.id).delete()
        db.delete(existing)
        db.commit()

    # 🎨 Crear paleta de colores
    palette = ColorPalette(
        primary_color="#000000",
        secondary_color="#111111",
        tertiary_color="#222222",
        primary_text="#333333",
        secondary_text="#444444",
        background_color="#555555",
        border_color="#666666"
    )
    db.add(palette)
    db.commit()
    db.refresh(palette)

    # 📄 Crear certificado válido
    transport = ASGITransport(app=app)
    serial_number = random.randint(10000000, 99999999)
    nit = random.randint(100000000, 999999999)
    start_date = date.today()
    expiration_date = start_date + timedelta(days=365)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Subir certificado
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

        # Crear empresa
        with open(VALID_LOGO, "rb") as logo_file:
            company_response = await client.post("/my-company/company", data={
                "name": "Empresa a Eliminar",
                "nit": str(nit),
                "email": "delete@empresa.com",
                "phone": "3003003000",
                "country": "Colombia",
                "state": "Antioquia",
                "city": "Medellín",
                "address": "Cra 99",
                "color_palette_id": str(palette.id),
                "digital_certificate_id": str(certificate_id)
            }, files={
                "logo": ("logo_test.png", logo_file, "image/png")
            })

            assert company_response.status_code in [200, 201]

        # 🔍 Buscar empresa por NIT y obtener ID
        company = db.query(Company).filter_by(nit=nit).first()
        assert company is not None
        company_id = company.id

        # 🚫 Eliminar empresa directamente desde DB como no hay endpoint expuesto
        db.query(CompanyCertificate).filter_by(company_id=company_id).delete()
        db.delete(company)
        db.commit()

        # ✅ Validar que ya no existe
        deleted_company = db.query(Company).filter_by(id=company_id).first()
        assert deleted_company is None

        # 🧹 Limpiar certificado y paleta
        cert = db.query(DigitalCertificate).filter_by(id=certificate_id).first()
        if cert:
            db.delete(cert)
            db.commit()

        db.delete(palette)
        db.commit()
