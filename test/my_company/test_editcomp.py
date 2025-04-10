import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from app.main import app
from app.database import SessionLocal
from app.my_company.models import ColorPalette, DigitalCertificate, Company, CompanyCertificate
from app.roles.models import Vars
from datetime import date, timedelta
import os

FILES_DIR = "files"
VALID_LOGO = os.path.join(FILES_DIR, "logo_test.png")

@pytest.fixture()
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.mark.asyncio
async def test_update_company_basic_info(db: Session):
    # 🧩 Asegurar que el estado "Activo" (id=22) existe en `vars`
    active_status = db.query(Vars).filter(Vars.id == 22).first()
    created_status = False
    if not active_status:
        active_status = Vars(id=22, name="Activo", type="certificate_status")
        db.add(active_status)
        db.commit()
        created_status = True

    # 🖌 Crear paleta de colores temporal
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

    # 📜 Crear certificado digital activo
    certificate = DigitalCertificate(
        serial_number=12345678,
        start_date=date.today() - timedelta(days=1),
        expiration_date=date.today() + timedelta(days=365),
        attached="fake_path.pdf",
        nit=999999999,
        status_id=22
    )
    db.add(certificate)
    db.commit()
    db.refresh(certificate)

    # 🏢 Crear empresa inicial
    company = Company(
        name="Empresa Original",
        nit=111111111,
        email="original@empresa.com",
        phone="3001234567",
        country="Colombia",
        state="Cundinamarca",
        city="Bogotá",
        address="Carrera 1",
        logo="original_logo_url",
        color_palette_id=palette.id
    )
    db.add(company)
    db.commit()
    db.refresh(company)

    # Crear relación CompanyCertificate
    company_cert = CompanyCertificate(
        company_id=company.id,
        digital_certificate_id=certificate.id
    )
    db.add(company_cert)
    db.commit()

    # 🚀 Ejecutar llamada al endpoint PATCH
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch("/my-company/company/basic", data={
            "name": "Empresa Actualizada",
            "nit": 222222222,
            "digital_certificate_id": str(certificate.id)
        })

    # ✅ Validar la respuesta
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Información básica actualizada correctamente"
    assert data["data"] == "Empresa Actualizada"

    # 🧼 Limpieza completa
    db.delete(company_cert)
    db.delete(company)
    db.delete(certificate)
    db.delete(palette)
    if created_status:
        db.delete(active_status)
    db.commit()
