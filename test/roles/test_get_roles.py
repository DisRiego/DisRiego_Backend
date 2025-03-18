import pytest
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.roles.services import RoleService
from app.roles.models import Role

@pytest.fixture(scope="function")
def db():
    """Fixture para manejar una sesión de base de datos en pruebas con rollback"""
    db = SessionLocal()
    yield db  # Proporciona la sesión a la prueba
    db.rollback()  # Revierte los cambios después de cada prueba
    db.close()

@pytest.fixture()
def role_service(db: Session):
    """Instancia del servicio de roles para pruebas"""
    return RoleService(db)

def test_get_roles(role_service, db):
    """✅ Prueba para obtener la lista de roles correctamente"""
    
    # 🔹 Obtener roles que ya existen en la base de datos
    existing_roles = db.query(Role).all()
    existing_role_names = {role.name for role in existing_roles}

    response = role_service.get_roles()

    assert response["success"] is True
    assert "data" in response

    # 🔹 Comparar que los roles obtenidos coincidan con los existentes en la BD
    response_role_names = {role["role_name"] for role in response["data"]}

    assert response_role_names == existing_role_names  # Debe coincidir con lo que hay en la BD
