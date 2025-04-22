import pytest
from sqlalchemy import text
from app.database import SessionLocal
from app.roles.services import UserRoleService
from app.roles.models import Role, Permission, Vars
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
    created_status_ids = []

    # 🔹 Verificar si el estado 1 existe en `vars`, si no, crearlo
    status = db.query(Vars).filter_by(id=1).first()
    if not status:
        status = Vars(id=1, name="Activo", type="status")
        db.add(status)
        db.commit()
        db.refresh(status)
        created_status_ids.append(status.id)  # Guardar para eliminarlo al final

    yield db, created_user_ids, created_role_ids, created_permission_ids, created_status_ids  # Proporciona la sesión

    # 🔹 Eliminar relaciones antes de eliminar roles
    if created_role_ids:
        db.execute(
            text("DELETE FROM rol_permission WHERE rol_id = ANY(:role_ids)"),
            {"role_ids": created_role_ids}
        )
        db.execute(
            text("DELETE FROM user_rol WHERE rol_id = ANY(:role_ids)"),
            {"role_ids": created_role_ids}
        )
        db.commit()

    # 🔹 Eliminar los roles creados
    if created_role_ids:
        db.execute(
            text("DELETE FROM rol WHERE id = ANY(:role_ids)"),
            {"role_ids": created_role_ids}
        )
        db.commit()

    # 🔹 Eliminar los permisos creados
    if created_permission_ids:
        db.execute(
            text("DELETE FROM permission WHERE id = ANY(:permission_ids)"),
            {"permission_ids": created_permission_ids}
        )
        db.commit()

    # 🔹 Eliminar el estado creado en la prueba
    if created_status_ids:
        db.execute(
            text("DELETE FROM vars WHERE id = ANY(:status_ids)"),
            {"status_ids": created_status_ids}
        )
        db.commit()

    db.rollback()  # Revierte otros cambios de la prueba
    db.close()

@pytest.fixture()
def user_role_service(db):
    """Instancia del servicio de roles para pruebas"""
    return UserRoleService(db[0])  # Pasamos solo la sesión de la base de datos

def test_get_user_roles(user_role_service, db):
    """✅ Prueba para obtener los roles de un usuario"""
    db_session, created_user_ids, created_role_ids, created_permission_ids, created_status_ids = db

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
        status=1  # Aseguramos que el estado 1 existe
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

    assert response["success"] is True
    assert "data" in response

    # 🔹 Verificar que los datos sean correctos
    user_data = response["data"]
    assert user_data["id"] == user.id
    assert user_data["email"] == user.email
    assert user_data["name"] == user.name
    assert len(user_data["roles"]) == 1
    assert user_data["roles"][0]["id"] == role.id
    assert user_data["roles"][0]["name"] == role.name
