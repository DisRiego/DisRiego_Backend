import pytest
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import SessionLocal
from app.roles.services import RoleService, PermissionService
from app.roles.models import Role, Permission
from app.roles.schemas import UpdateRolePermissions


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


@pytest.fixture()
def permission_service(db: Session):
    """Instancia del servicio de permisos para pruebas"""
    return PermissionService(db)


@pytest.fixture()
def setup_role_with_permissions(db: Session):
    """Crear un rol y permisos de prueba en la base de datos"""

    # Crear permisos de prueba
    perm1 = Permission(name="permiso_lectura", description="Leer datos", category="general")
    perm2 = Permission(name="permiso_escritura", description="Escribir datos", category="general")

    db.add_all([perm1, perm2])
    db.commit()
    db.refresh(perm1)
    db.refresh(perm2)

    # Crear rol de prueba
    role = Role(name="Tester", description="Rol de prueba", status=1)
    db.add(role)
    db.commit()
    db.refresh(role)

    yield role, [perm1, perm2]  # Retorna el rol y los permisos creados

    # 🔹 Limpieza: Eliminar referencias en la tabla intermedia antes de borrar los roles y permisos
    db.execute(text("DELETE FROM rol_permission WHERE rol_id = :role_id"), {"role_id": role.id})
    db.commit()

    db.delete(role)
    db.delete(perm1)
    db.delete(perm2)
    db.commit()


def test_modify_permissions(role_service, setup_role_with_permissions):
    """✅ Prueba para modificar los permisos de un rol"""
    
    role, permissions = setup_role_with_permissions
    permission_ids = [permissions[0].id, permissions[1].id]  # IDs de permisos

    request_data = UpdateRolePermissions(permissions=permission_ids)
    
    response = role_service.update_role_permissions(role.id, request_data.permissions)

    assert response["success"] is True
    assert "data" in response
    assert "permissions" in response["data"]

    updated_permission_ids = {perm["id"] for perm in response["data"]["permissions"]}
    assert set(permission_ids) == updated_permission_ids, "Los permisos asignados no coinciden con los esperados."
