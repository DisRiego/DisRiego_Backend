import pytest
from sqlalchemy import text
from app.database import SessionLocal
from app.roles.services import UserRoleService
from app.roles.models import Role, Permission
from app.users.models import User
import uuid

@pytest.fixture(scope="function")
def db():
    """Fixture para manejar una sesión de base de datos en pruebas con rollback"""
    db = SessionLocal()

    # Listas para rastrear los datos creados en la prueba
    created_user_ids = []
    created_role_ids = []
    created_permission_ids = []

    yield db, created_user_ids, created_role_ids, created_permission_ids  # Proporciona la sesión y listas de IDs creados   

    # 🔹 Eliminar las relaciones entre roles y permisos antes de eliminar los roles
    if created_role_ids:
        db.execute(
            text("DELETE FROM rol_permission WHERE rol_id = ANY(:role_ids)"),
            {"role_ids": created_role_ids}
        )
        db.commit()

    # 🔹 Eliminar las relaciones entre usuarios y roles antes de eliminar los roles
    if created_role_ids:
        db.execute(
            text("DELETE FROM user_rol WHERE rol_id = ANY(:role_ids)"),
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

    # 🔹 Eliminar los usuarios creados en la prueba
    if created_user_ids:
        db.execute(
            text("DELETE FROM users WHERE id = ANY(:user_ids)"),
            {"user_ids": created_user_ids}
        )
        db.commit()

    db.rollback()  # Revierte otros cambios de la prueba
    db.close()

@pytest.fixture()
def user_role_service(db):
    """Instancia del servicio de usuarios y roles para pruebas"""
    return UserRoleService(db[0])  # Pasamos solo la sesión de la base de datos

def test_get_user_roles(user_role_service, db):
    """✅ Prueba para obtener los roles de un usuario"""
    db_session, created_user_ids, created_role_ids, created_permission_ids = db

    # 🔹 Crear un usuario de prueba
    user = User(name=f"TestUser_{uuid.uuid4().hex[:8]}", email=f"user_{uuid.uuid4().hex[:8]}@example.com")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    created_user_ids.append(user.id)

    # 🔹 Crear permisos de prueba
    permission = Permission(
        name=f"Permission_{uuid.uuid4().hex[:8]}", 
        description="Permission for testing", 
        category="General"
    )
    db_session.add(permission)
    db_session.commit()
    db_session.refresh(permission)
    created_permission_ids.append(permission.id)

    # 🔹 Crear un rol de prueba y asignarle el permiso
    role = Role(
        name=f"Role_{uuid.uuid4().hex[:8]}", 
        description="Test Role", 
        status=1
    )
    role.permissions.append(permission)
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    created_role_ids.append(role.id)

    # 🔹 Asignar el rol al usuario
    user.roles.append(role)
    db_session.commit()
    db_session.refresh(user)

    # 🔹 Obtener los roles del usuario
    response = user_role_service.get_user_with_roles(user.id)

    # 🔹 Validaciones
    assert response["success"] is True
    assert response["data"]["id"] == user.id
    assert len(response["data"]["roles"]) == 1  # Debe tener exactamente un rol
    assert response["data"]["roles"][0]["id"] == role.id
    assert response["data"]["roles"][0]["name"] == role.name
