import pytest
from sqlalchemy import text
from app.database import SessionLocal
from app.roles.services import PermissionService
from app.roles.models import Permission
import uuid

@pytest.fixture(scope="function")
def db():
    """Fixture para manejar una sesión de base de datos en pruebas con rollback"""
    db = SessionLocal()

    # Lista para rastrear los permisos creados en la prueba
    created_permission_ids = []

    yield db, created_permission_ids  # Proporciona la sesión y la lista de IDs creados

    # 🔹 Eliminar los permisos creados en la prueba
    if created_permission_ids:
        db.execute(
            text("DELETE FROM permission WHERE id = ANY(:permission_ids)"),
            {"permission_ids": created_permission_ids}
        )
        db.commit()

    db.rollback()  # Revierte otros cambios de la prueba
    db.close()

@pytest.fixture()
def permission_service(db):
    """Instancia del servicio de permisos para pruebas"""
    return PermissionService(db[0])  # Pasamos solo la sesión de la base de datos

def test_get_permissions(permission_service, db):
    """✅ Prueba para listar todos los permisos"""
    db_session, created_permission_ids = db

    # 🔹 Crear permisos de prueba
    permission1 = Permission(
        name=f"Permiso_Test_1_{uuid.uuid4().hex[:8]}", 
        description="Permiso de prueba 1", 
        category="General"
    )
    permission2 = Permission(
        name=f"Permiso_Test_2_{uuid.uuid4().hex[:8]}", 
        description="Permiso de prueba 2", 
        category="Administración"
    )
    db_session.add(permission1)
    db_session.add(permission2)
    db_session.commit()
    db_session.refresh(permission1)
    db_session.refresh(permission2)

    # Guardamos los IDs para eliminarlos después
    created_permission_ids.append(permission1.id)
    created_permission_ids.append(permission2.id)

    # 🔹 Ejecutar la función `get_permissions()`
    response = permission_service.get_permissions()

    # 🔹 Verificar que se recibieron permisos correctamente
    assert isinstance(response, list)
    assert len(response) >= 2  # Al menos los 2 creados
    permission_names = {perm.name for perm in response}

    assert permission1.name in permission_names
    assert permission2.name in permission_names
