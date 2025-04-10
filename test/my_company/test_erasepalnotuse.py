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
async def test_delete_color_palette_not_in_use(db: Session):
    # 🧪 Crear una paleta de prueba que no esté asociada a ninguna empresa
    test_palette = ColorPalette(
        primary_color="#DEAD00",
        secondary_color="#BEEF00",
        tertiary_color="#C0FFEE",
        primary_text="#FAFAFA",
        secondary_text="#CCCCCC",
        background_color="#EEEEEE",
        border_color="#DDDDDD"
    )
    db.add(test_palette)
    db.commit()
    db.refresh(test_palette)
    palette_id = test_palette.id

    # 🚀 Ejecutar DELETE al endpoint
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(f"/my-company/color-palettes/{palette_id}")

    # ✅ Validaciones de respuesta
    assert response.status_code == 200, response.text
    response_json = response.json()
    assert response_json["success"] is True
    assert response_json["message"] == "Paleta de colores eliminada correctamente"
    assert response_json["data"] is None

    # 🔍 Verificar que ya no exista en la base de datos
    deleted = db.query(ColorPalette).filter_by(id=palette_id).first()
    assert deleted is None
