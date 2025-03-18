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

    # Lista para rastrear los roles creados en la prueba
    created_role_ids = []

    yield db, created_role_ids  # Proporciona la sesión y la lista de roles creados
    
    # 🔹 Eliminar solo los roles creados en la prueba
    if created_role_ids:
        db.query(Role).filter(Role.id.in_(created_role_ids)).delete(synchronize_session=False)
        db.commit()

    db.rollback()  # Revierte otros cambios de la prueba
    db.close()

@pytest.fixture()
def role_service(db):
    """Instancia del servicio de roles para pruebas"""
    return RoleService(db[0])  # Pasamos solo la sesión de la base de datos

def test_create_role_success(role_service, db):
    """✅ Prueba de creación exitosa de un rol"""
    db_session, created_role_ids = db  # Extraer la sesión y la lista de roles creados

    role_data = RoleCreate(name="Test1 Role", description="Role1 for testing", permissions=[])

    response = role_service.create_role(role_data)

    assert response is not None
    assert response.name == "Test1 Role"
    assert response.description == "Role1 for testing"
    assert isinstance(response.id, int)  # Se asegura que el rol fue creado en la BD

    # Guardamos el ID del rol creado para eliminarlo al final
    created_role_ids.append(response.id)

    # Verificar que el rol se creó en la BD
    created_role = db_session.query(Role).filter_by(name="Test1 Role").first()
    assert created_role is not None

def test_create_duplicate_role(role_service, db):
    """❌ Prueba de intento de crear un rol con un nombre duplicado"""
    db_session, created_role_ids = db  # Extraer la sesión y la lista de roles creados

    role_data = RoleCreate(name="Test1 Role", description="Role1 for testing", permissions=[])

    # Crear el rol por primera vez
    response = role_service.create_role(role_data)
    created_role_ids.append(response.id)  # Guardamos el ID para eliminarlo después

    # Intentar crearlo de nuevo y verificar que lanza un error 400
    with pytest.raises(HTTPException) as exc_info:
        role_service.create_role(role_data)

    assert exc_info.value.status_code == 400
    assert "El rol ya existe" in str(exc_info.value.detail)
