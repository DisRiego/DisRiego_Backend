import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from app.main import app
from app.database import SessionLocal
from app.my_company.models import ColorPalette
import os

# Archivos de prueba
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
async def test_create_company_without_nit(db: Session):
    # 🎨 Crear paleta de colores temporal
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

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with open(VALID_LOGO, "rb") as logo_file:
            # Enviamos los datos SIN incluir el campo "nit"
            response = await client.post("/my-company/company", data={
                "name": "Empresa sin NIT",
                "email": "sin_nit@empresa.com",
                "phone": "3000000000",
                "country": "Colombia",
                "state": "Cundinamarca",
                "city": "Bogotá",
                "address": "Carrera 1",
                "color_palette_id": str(palette.id),
                "digital_certificate_id": "1"  # ID arbitrario (debería fallar antes)
            }, files={
                "logo": ("logo_test.png", logo_file, "image/png")
            })

    # ✅ Validar respuesta
    assert response.status_code == 422  # Unprocessable Entity por faltar campo requerido
    data = response.json()
    assert "detail" in data
    nit_error = next((err for err in data["detail"] if err.get("loc", [])[1] == "nit"), None)
    assert nit_error is not None
    assert nit_error["msg"].lower().startswith("field required")

    # 🧹 Limpieza
    db.delete(palette)
    db.commit()
