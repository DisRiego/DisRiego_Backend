import pytest
from fastapi import HTTPException
from app.database import SessionLocal
from app.roles.services import PermissionService
from app.roles.schemas import PermissionBase
from app.roles.models import Permission

@pytest.fixture(scope="function")
def db():
    """Fixture para manejar una sesión de base de datos en pruebas con rollback"""
    db = SessionLocal()
    
    # 🔹 Lista para rastrear los permisos creados en la prueba
    created_permission_ids = []

    yield db, created_permission_ids  # Proporciona la sesión y la lista de permisos creados

    # 🔹 Eliminar solo los permisos creados en la prueba
    if created_permission_ids:
        db.query(Permission).filter(Permission.id.in_(created_permission_ids)).delete(synchronize_session=False)
        db.commit()

    db.rollback()  # Revierte otros cambios de la prueba
    db.close()

@pytest.fixture()
def permission_service(db):
    """Instancia del servicio de permisos para pruebas"""
    return PermissionService(db[0])  # Pasamos solo la sesión de la base de datos

def test_create_permission_success(permission_service, db):
    """✅ Prueba de creación exitosa de un permiso"""
    db_session, created_permission_ids = db  # Extraer la sesión y la lista de permisos creados

    permission_data = PermissionBase(
        name="tes2_permission",
        description="Permis2o de prueba",
        category="TestCategory"
    )

    response = permission_service.create_permission(permission_data)

    assert response.success is True
    assert response.data == "El permiso se ha creado correctamente"

    # Verificar en la base de datos usando el modelo correcto
    created_permission = db_session.query(Permission).filter_by(name="tes2_permission").first()
    assert created_permission is not None
    assert created_permission.description == "Permis2o de prueba"
    assert created_permission.category == "TestCategory"

    # 🔹 Guardamos el ID del permiso creado para eliminarlo después
    created_permission_ids.append(created_permission.id)

def test_create_duplicate_permission(permission_service, db):
    """❌ Prueba de intento de crear un permiso con un nombre duplicado"""
    db_session, created_permission_ids = db  # Extraer la sesión y la lista de permisos creados

    permission_data = PermissionBase(
        name="tes2_permission",
        description="Permis2o de prueba",
        category="TestCategory"
    )

    # Crear el permiso por primera vez
    permission_service.create_permission(permission_data)

    # Obtener el permiso creado manualmente desde la base de datos
    created_permission = db_session.query(Permission).filter_by(name="tes2_permission").first()
    
    # Asegurar que el permiso se creó correctamente
    assert created_permission is not None

    # Guardamos el ID del permiso creado para eliminarlo después
    created_permission_ids.append(created_permission.id)

    # Intentar crearlo de nuevo y verificar que lanza un error 400
    with pytest.raises(HTTPException) as exc_info:
        permission_service.create_permission(permission_data)

    assert exc_info.value.status_code == 400
    assert "El permiso ya existe asignado a ese nombre" in str(exc_info.value.detail)
