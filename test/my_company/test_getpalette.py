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
async def test_get_color_palette_by_id(db: Session):
    # 🧹 Limpiar por color base si existe
    db.query(ColorPalette).filter_by(primary_color="#ABCDEF").delete()
    db.commit()

    # Crear paleta directamente en la base de datos
    palette = ColorPalette(
        primary_color="#ABCDEF",
        secondary_color="#BCDEFA",
        tertiary_color="#CDEFAB",
        primary_text="#DEFABC",
        secondary_text="#EFABCD",
        background_color="#FABCDE",
        border_color="#ABCDE1"
    )
    db.add(palette)
    db.commit()
    db.refresh(palette)

    palette_id = palette.id

    # 🔍 Prueba de obtención por ID
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/my-company/color-palettes/{palette_id}")

    assert response.status_code == 200, response.text
    response_json = response.json()
    assert response_json["success"] is True
    assert "data" in response_json

    data = response_json["data"]
    assert data["id"] == palette_id
    assert data["primary_color"] == "#ABCDEF"
    assert data["secondary_color"] == "#BCDEFA"
    assert data["tertiary_color"] == "#CDEFAB"
    assert data["primary_text"] == "#DEFABC"
    assert data["secondary_text"] == "#EFABCD"
    assert data["background_color"] == "#FABCDE"
    assert data["border_color"] == "#ABCDE1"

    # 🧹 Limpieza final
    db.delete(palette)
    db.commit()
