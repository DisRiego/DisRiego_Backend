import pytest
from fastapi import HTTPException
from app.database import SessionLocal
from app.roles.services import PermissionService
from app.roles.schemas import PermissionBase
from app.roles.models import Permission  # Importamos el modelo real de SQLAlchemy

@pytest.fixture(scope="function")
def db():
    """Fixture para manejar una sesión de base de datos en pruebas con rollback"""
    db = SessionLocal()
    
    # 🔴 Limpia cualquier permiso de pruebas antes de ejecutar el test
    db.query(Permission).filter(Permission.name == "test_permission").delete()
    db.commit()

    yield db  # Proporciona la sesión a la prueba

    db.rollback()  # Revierte los cambios después de la prueba
    db.close()

@pytest.fixture()
def permission_service(db):
    """Instancia del servicio de permisos para pruebas"""
    return PermissionService(db)

def test_create_permission_success(permission_service, db):
    """✅ Prueba de creación exitosa de un permiso"""
    permission_data = PermissionBase(
        name="test_permission",
        description="Permiso de prueba",
        category="TestCategory"
    )

    response = permission_service.create_permission(permission_data)

    assert response.success is True
    assert response.data == "El permiso se ha creado correctamente"

    # 🔧 Corrección: Verificar en la base de datos usando el modelo correcto
    created_permission = db.query(Permission).filter_by(name="test_permission").first()
    assert created_permission is not None
    assert created_permission.description == "Permiso de prueba"
    assert created_permission.category == "TestCategory"

def test_create_duplicate_permission(permission_service, db):
    """❌ Prueba de intento de crear un permiso con un nombre duplicado"""
    permission_data = PermissionBase(
        name="test_permission",
        description="Permiso de prueba",
        category="TestCategory"
    )

    # Crear el permiso por primera vez
    permission_service.create_permission(permission_data)

    # Intentar crearlo de nuevo y verificar que lanza un error 400
    with pytest.raises(HTTPException) as exc_info:
        permission_service.create_permission(permission_data)

    assert exc_info.value.status_code == 400
    assert "El permiso ya existe asignado a ese nombre" in str(exc_info.value.detail)
