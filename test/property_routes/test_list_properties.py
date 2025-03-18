import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal

@pytest.fixture(scope="module")
def db():
    """Fixture para crear una nueva sesión de base de datos para las pruebas"""
    db = SessionLocal()
    db.begin()
    yield db
    db.rollback()
    db.close()

@pytest.fixture()
def client():
    """Crear una instancia del cliente de pruebas"""
    return TestClient(app)

# Test: Obtener todas las propiedades con datos en la base de datos
def test_get_all_properties(client: TestClient, db):
    response = client.get("/properties/")
    assert response.status_code in [200, 400]  # Puede ser 200 si hay datos, o 400 si no hay propiedades
    json_response = response.json()

    # Verificamos que la estructura de respuesta sea correcta
    assert "success" in json_response
    assert "data" in json_response

    # Si hay propiedades, `data` debe ser una lista
    if response.status_code == 200:
        assert json_response["success"] is True
        assert isinstance(json_response["data"], list)

    # Si no hay propiedades, debe devolver success=False y una lista vacía
    if response.status_code == 400:
        assert json_response["success"] is False
        assert json_response["data"] == []
