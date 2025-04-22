import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from app.main import app
from app.database import SessionLocal
from app.my_company.models import ColorPalette

@pytest.fixture()
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.mark.asyncio
async def test_create_color_palette_valid(db: Session):
    # 🔁 Limpiar posibles paletas duplicadas con mismo color base (por si ya existe por test anterior)
    db.query(ColorPalette).filter_by(primary_color="#123456").delete()
    db.commit()

    # Datos válidos para creación
    palette_data = {
        "primary_color": "#123456",
        "secondary_color": "#234567",
        "tertiary_color": "#345678",
        "primary_text": "#456789",
        "secondary_text": "#56789A",
        "background_color": "#6789AB",
        "border_color": "#789ABC"
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/my-company/color-palettes", json=palette_data)

    # ✅ Validaciones
    assert response.status_code == 201, response.text
    response_json = response.json()
    assert response_json["success"] is True
    assert "data" in response_json
    data = response_json["data"]

    for key in palette_data:
        assert data[key] == palette_data[key]

    palette_id = data["id"]

    # 🔍 Verificar que existe en la base de datos
    created_palette = db.query(ColorPalette).filter_by(id=palette_id).first()
    assert created_palette is not None
    assert created_palette.primary_color == palette_data["primary_color"]

    # 🧹 Limpieza
    db.delete(created_palette)
    db.commit()
