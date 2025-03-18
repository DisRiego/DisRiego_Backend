import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.sql import text  # 🔹 Import necesario para consultas SQL directas
from app.main import app  # Importar la aplicación FastAPI
from app.database import get_db
from app.users.models import User
from app.property_routes.models import Property, PropertyUser

@pytest.fixture
def client():
    """Cliente de prueba para hacer solicitudes a la API"""
    return TestClient(app)

@pytest.fixture
def db_session():
    """Fixture para manejar una sesión de base de datos en pruebas"""
    db = next(get_db())  # Obtener una sesión de la base de datos configurada
    yield db
    db.rollback()  # Asegurar que no persistan cambios
    db.close()

@pytest.fixture
def setup_test_user(db_session: Session):
    """Crea un usuario de prueba en la base de datos si no existe"""
    test_user = db_session.query(User).filter_by(email="test_user@example.com").first()

    if not test_user:
        test_user = User(
            email="test_user@example.com",
            password="test123"  # Usa el campo correcto en el modelo
        )
        db_session.add(test_user)
        db_session.commit()
        db_session.refresh(test_user)

    yield test_user

    # 🔹 Eliminar referencias en `user_property` antes de borrar el usuario
    db_session.execute(
        text("DELETE FROM user_property WHERE user_id = :user_id"),
        {"user_id": test_user.id}
    )
    db_session.commit()

    # 🔹 Ahora podemos eliminar el usuario sin conflictos
    db_session.delete(test_user)
    db_session.commit()

    # 🔹 Limpiar propiedades creadas en la prueba
    db_session.execute(text("DELETE FROM property WHERE name = 'Predio de prueba'"))
    db_session.execute(text("DELETE FROM property WHERE real_estate_registration_number = 123456"))
    db_session.commit()

def test_create_property_success(client, setup_test_user, db_session):
    """Prueba para crear un predio con datos válidos"""

    # 🔹 Asegurar que no haya un predio con el mismo número de registro
    db_session.execute(text("DELETE FROM property WHERE real_estate_registration_number = 123456"))
    db_session.commit()

    data = {
        "user_id": setup_test_user.id,
        "name": "Predio de prueba",
        "longitude": -75.691,
        "latitude": 4.1492,
        "extension": 500.5,
        "real_estate_registration_number": 123456,
    }

    files = {
        "public_deed": ("public_deed.pdf", b"fake pdf content", "application/pdf"),
        "freedom_tradition_certificate": ("freedom_tradition.pdf", b"fake pdf content", "application/pdf"),
    }

    response = client.post("/properties/", data=data, files=files)

    # 🔹 Ver respuesta del servidor para identificar errores
    print("Response Status Code:", response.status_code)
    print("Response JSON:", response.json())

    assert response.status_code == 200, f"Error en la creación del predio: {response.json()}"
    
    response_json = response.json()
    assert response_json["success"] is True
    assert "Se ha creado el predio satisfactoriamente" in response_json["data"]["message"]

    # 🔹 Verificar que la propiedad se creó en la BD
    created_property = db_session.query(Property).filter_by(name="Predio de prueba").first()
    assert created_property is not None

    # 🔹 Verificar que la relación con el usuario existe
    user_property_relation = db_session.query(PropertyUser).filter_by(property_id=created_property.id).first()
    assert user_property_relation is not None
    assert user_property_relation.user_id == setup_test_user.id

    # 🔹 Limpiar después de la prueba
    db_session.execute(text("DELETE FROM user_property WHERE property_id = :property_id"), {"property_id": created_property.id})
    db_session.execute(text("DELETE FROM property WHERE id = :property_id"), {"property_id": created_property.id})
    db_session.commit()
