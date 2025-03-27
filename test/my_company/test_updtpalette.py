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
async def test_update_color_palette_valid(db: Session):
    # 🧪 Crear una paleta inicial
    original_palette = ColorPalette(
        primary_color="#111111",
        secondary_color="#222222",
        tertiary_color="#333333",
        primary_text="#444444",
        secondary_text="#555555",
        background_color="#666666",
        border_color="#777777"
    )
    db.add(original_palette)
    db.commit()
    db.refresh(original_palette)

    palette_id = original_palette.id

    # 📝 Datos nuevos para actualización
    updated_palette_data = {
        "primary_color": "#AAAAAA",
        "secondary_color": "#BBBBBB",
        "tertiary_color": "#CCCCCC",
        "primary_text": "#DDDDDD",
        "secondary_text": "#EEEEEE",
        "background_color": "#FFFFFF",
        "border_color": "#999999"
    }

    # 🚀 Petición PUT para actualizar la paleta
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/my-company/color-palettes/{palette_id}",
            json=updated_palette_data
        )

    # ✅ Validaciones de respuesta
    assert response.status_code == 200, response.text
    response_json = response.json()
    assert response_json["success"] is True
    assert response_json["message"] == "Paleta de colores actualizada correctamente"
    assert "data" in response_json
    data = response_json["data"]
    assert data["id"] == palette_id
    for key in updated_palette_data:
        assert data[key] == updated_palette_data[key]

    # 🔄 Refrescar para que refleje los cambios hechos por FastAPI (otra sesión)
    db.refresh(original_palette)

    # 🔍 Verificar en base de datos
    for key, value in updated_palette_data.items():
        assert getattr(original_palette, key) == value

    # 🧹 Limpieza
    db.delete(original_palette)
    db.commit()
