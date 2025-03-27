import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from app.main import app
from app.database import SessionLocal
from app.my_company.models import ColorPalette, Company

@pytest.fixture()
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.mark.asyncio
async def test_delete_color_palette_in_use(db: Session):
    # 🧪 Crear una paleta de colores
    in_use_palette = ColorPalette(
        primary_color="#111111",
        secondary_color="#222222",
        tertiary_color="#333333",
        primary_text="#444444",
        secondary_text="#555555",
        background_color="#666666",
        border_color="#777777"
    )
    db.add(in_use_palette)
    db.commit()
    db.refresh(in_use_palette)

    # 🧪 Asociar la paleta a una empresa ficticia
    company = Company(
        name="Empresa de Prueba",
        nit=123456789,
        email="empresa@test.com",
        phone="3001234567",
        country="Colombia",
        state="Cundinamarca",
        city="Bogotá",
        address="Calle Falsa 123",
        logo="logo.png",
        color_palette_id=in_use_palette.id
    )
    db.add(company)
    db.commit()
    db.refresh(company)

    # 🚀 Intentar eliminar la paleta
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(f"/my-company/color-palettes/{in_use_palette.id}")

    # ❌ Validaciones de error esperadas
    assert response.status_code == 400, response.text
    response_json = response.json()
    assert response_json["success"] is False
    assert "no se puede eliminar" in response_json["message"].lower()

    # 🔍 Verificar que sigue existiendo
    still_exists = db.query(ColorPalette).filter_by(id=in_use_palette.id).first()
    assert still_exists is not None

    # 🧹 Limpieza manual
    db.delete(company)
    db.delete(in_use_palette)
    db.commit()
