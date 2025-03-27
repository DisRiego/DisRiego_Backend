import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import SessionLocal

@pytest.fixture()
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.mark.asyncio
async def test_get_lot_by_invalid_id(db):
    """Debe retornar 404 si se consulta un lote inexistente"""

    # Usamos un ID alto que no debería existir
    invalid_lot_id = 999999

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/properties/lot/{invalid_lot_id}")

    print("❌ Status:", response.status_code)
    print("❌ JSON:", response.json())

    assert response.status_code == 404
    assert response.json()["success"] is False
    assert "no encontrado" in response.json()["data"].lower()
