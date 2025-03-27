import pytest
from sqlalchemy import text
from app.database import SessionLocal
from app.roles.services import RoleService
from app.roles.models import Role, Permission, Vars
import uuid

@pytest.fixture(scope="function")
def db():
    """Fixture para manejar una sesión de base de datos en pruebas con rollback"""
    db = SessionLocal()

    # Listas para rastrear los roles, permisos y estados creados en la prueba
    created_role_ids = []
    created_permission_ids = []
    created_status_ids = []

    yield db, created_role_ids, created_permission_ids, created_status_ids  # Proporciona la sesión y las listas de IDs creados

    # 🔹 Eliminar referencias en `rol_permission` antes de borrar los roles
    if created_role_ids:
        db.execute(
            text("DELETE FROM rol_permission WHERE rol_id = ANY(:role_ids)"),
            {"role_ids": created_role_ids}
        )
        db.commit()

    # 🔹 Eliminar los roles creados en la prueba
    if created_role_ids:
        db.execute(
            text("DELETE FROM rol WHERE id = ANY(:role_ids)"),
            {"role_ids": created_role_ids}
        )
        db.commit()

    # 🔹 Eliminar los permisos creados en la prueba
    if created_permission_ids:
        db.execute(
            text("DELETE FROM permission WHERE id = ANY(:permission_ids)"),
            {"permission_ids": created_permission_ids}
        )
        db.commit()

    # 🔹 Eliminar los estados creados en la prueba
    if created_status_ids:
        db.execute(
            text("DELETE FROM vars WHERE id = ANY(:status_ids)"),
            {"status_ids": created_status_ids}
        )
        db.commit()

    db.rollback()  # Revierte otros cambios de la prueba
    db.close()

@pytest.fixture()
def role_service(db):
    """Instancia del servicio de roles para pruebas"""
    return RoleService(db[0])  # Pasamos solo la sesión de la base de datos


def test_get_specific_role(role_service, db):
    """✅ Prueba para obtener un rol específico"""
    db_session, created_role_ids, created_permission_ids, created_status_ids = db

    # 🔹 Crear un estado en la tabla `vars` con un tipo válido
    status = Vars(name="Estado de Prueba", type="status")  # ✅ Se añade 'type'
    db_session.add(status)
    db_session.commit()
    db_session.refresh(status)
    created_status_ids.append(status.id)

    # 🔹 Crear un permiso de prueba
    permission = Permission(name=f"Permiso_{uuid.uuid4().hex[:8]}", description="Permiso de prueba", category="General")
    db_session.add(permission)
    db_session.commit()
    db_session.refresh(permission)
    created_permission_ids.append(permission.id)

    # 🔹 Crear un rol con ese permiso y estado
    role_name = f"Rol_Test_{uuid.uuid4().hex[:8]}"
    role = Role(name=role_name, description="Rol de prueba", status=status.id)
    role.permissions.append(permission)
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    created_role_ids.append(role.id)

    # 🔹 Obtener el rol por ID
    response = role_service.get_rol(role.id)

    assert response["success"] is True
    assert "data" in response
    assert len(response["data"]) > 0

    role_data = response["data"][0]
    assert role_data["id"] == role.id
    assert role_data["name"] == role_name
    assert role_data["description"] == "Rol de prueba"
    assert role_data["status"] == status.id
    assert len(role_data["permissions"]) == 1
    assert role_data["permissions"][0]["id"] == permission.id
    assert role_data["permissions"][0]["name"] == permission.name
