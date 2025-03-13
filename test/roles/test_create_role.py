import pytest
from fastapi import HTTPException
from app.database import SessionLocal
from app.roles.services import RoleService
from app.roles.schemas import RoleCreate
from app.roles.models import Role

@pytest.fixture(scope="function")
def db():
    """Fixture para manejar una sesión de base de datos en pruebas con rollback"""
    db = SessionLocal()
    
    # ❗Eliminar cualquier rol con el mismo nombre antes de ejecutar la prueba
    db.query(Role).delete()
    db.commit()
    
    yield db  # Proporciona la sesión a la prueba
    
    db.rollback()  # Revierte los cambios de la prueba
    db.close()

@pytest.fixture()
def role_service(db):
    """Instancia del servicio de roles para pruebas"""
    return RoleService(db)

def test_create_role_success(role_service, db):
    """✅ Prueba de creación exitosa de un rol"""
    role_data = RoleCreate(name="Test Role", description="Role for testing", permissions=[])

    response = role_service.create_role(role_data)

    assert response is not None
    assert response.name == "Test Role"
    assert response.description == "Role for testing"
    assert isinstance(response.id, int)  # Se asegura que el rol fue creado en la BD

    # Verificar que el rol se creó en la BD
    created_role = db.query(response.__class__).filter_by(name="Test Role").first()
    assert created_role is not None

def test_create_duplicate_role(role_service, db):
    """❌ Prueba de intento de crear un rol con un nombre duplicado"""
    role_data = RoleCreate(name="Test Role", description="Role for testing", permissions=[])

    # Crear el rol por primera vez
    role_service.create_role(role_data)

    # Intentar crearlo de nuevo y verificar que lanza un error 400
    with pytest.raises(HTTPException) as exc_info:
        role_service.create_role(role_data)

    assert exc_info.value.status_code == 400
    assert "El rol ya existe" in str(exc_info.value.detail)
