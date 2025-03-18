import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.roles.services import RoleService
from app.roles.models import Role, Permission
import uuid

@pytest.fixture(scope="function")
def db():
    """Fixture para manejar una sesión de base de datos en pruebas con rollback"""
    db = SessionLocal()

    # Listas para rastrear los roles y permisos creados en la prueba
    created_role_ids = []
    created_permission_ids = []

    yield db, created_role_ids, created_permission_ids  # Proporciona la sesión y las listas de IDs creados

    # 🔹 Eliminar referencias en `rol_permission` antes de borrar los roles
    if created_role_ids:
        db.execute(
            text("DELETE FROM rol_permission WHERE rol_id = ANY(:role_ids)"),
            {"role_ids": created_role_ids}
        )
        db.commit()

    # 🔹 Eliminar los roles creados en la prueba
    if created_role_ids:
        db.query(Role).filter(Role.id.in_(created_role_ids)).delete(synchronize_session=False)
        db.commit()

    # 🔹 Eliminar los permisos creados en la prueba
    if created_permission_ids:
        db.query(Permission).filter(Permission.id.in_(created_permission_ids)).delete(synchronize_session=False)
        db.commit()

    db.rollback()  # Revierte otros cambios de la prueba
    db.close()


@pytest.fixture()
def role_service(db):
    """Instancia del servicio de roles para pruebas"""
    return RoleService(db[0])  # Pasamos solo la sesión de la base de datos


def test_get_roles(role_service, db):
    """✅ Prueba para obtener la lista de roles correctamente"""
    db_session, created_role_ids, created_permission_ids = db

    # 🔹 Crear un permiso de prueba
    permission_name = f"Test_Permission_{uuid.uuid4().hex[:8]}"  # Nombre único
    permission = Permission(name=permission_name, description="Permission for testing", category="General")
    db_session.add(permission)
    db_session.commit()
    db_session.refresh(permission)

    # Guardamos el ID del permiso creado
    created_permission_ids.append(permission.id)

    # 🔹 Crear un rol de prueba
    role_name = f"Test_Role_{uuid.uuid4().hex[:8]}"  # Nombre único
    role = Role(name=role_name, description="Role for testing", status=1)
    role.permissions.append(permission)  # Asignar el permiso al rol
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)

    # Guardamos el ID del rol creado
    created_role_ids.append(role.id)

    # 🔹 Ejecutar la función `get_roles()`
    response = role_service.get_roles()

    assert response["success"] is True
    assert "data" in response

    # 🔹 Buscar el rol creado en la respuesta de la API
    roles_data = response["data"]
    created_role_data = next((r for r in roles_data if r["role_name"] == role_name), None)

    assert created_role_data is not None, "El rol de prueba no se encontró en la respuesta de la API"
    assert created_role_data["role_description"] == "Role for testing"
    assert created_role_data["status_name"] is not None  # Se asegura que el status se devuelve correctamente

    # 🔹 Verificar los permisos del rol en la API
    permission_data = created_role_data["permissions"]
    assert len(permission_data) == 1
    assert permission_data[0]["name"] == permission_name
