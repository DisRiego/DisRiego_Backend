import pytest
from fastapi import HTTPException
from sqlalchemy import text
from app.database import SessionLocal
from app.roles.services import RoleService
from app.roles.schemas import RoleCreate
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


def test_edit_role_success(role_service, db):
    """✅ Prueba la edición exitosa de un rol"""
    db_session, created_role_ids, created_permission_ids = db

    # 🔹 Crear un permiso de prueba con nombre único
    permission_name = f"Edit_Permission_{uuid.uuid4().hex[:8]}"
    permission = Permission(name=permission_name, description="Permission for editing", category="General")
    db_session.add(permission)
    db_session.commit()
    db_session.refresh(permission)
    created_permission_ids.append(permission.id)

    # 🔹 Crear un rol de prueba con nombre único
    role_name = f"Edit_Role_{uuid.uuid4().hex[:8]}"
    role = Role(name=role_name, description="Role to edit", status=1)
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    created_role_ids.append(role.id)

    # 🔹 Editar el rol
    updated_role_data = RoleCreate(name=role.name, description="Updated description", permissions=[permission.id])
    response = role_service.edit_rol(role.id, updated_role_data)

    # ✅ Cambiar la forma de acceder a la descripción
    assert response["success"] is True
    assert response["message"] == "Rol editado correctamente"
    assert response["data"].description == "Updated description"  # Acceder directamente al atributo del objeto `Role`
    
    # 🔹 Verificar en la base de datos que el rol ha sido actualizado correctamente
    updated_role = db_session.query(Role).filter_by(id=role.id).first()
    assert updated_role is not None
    assert updated_role.description == "Updated description"


def test_edit_role_not_found(role_service):
    """❌ Prueba que no se pueda editar un rol inexistente"""
    updated_role_data = RoleCreate(name="Inexistente", description="No existe", permissions=[1])
    with pytest.raises(HTTPException) as excinfo:
        role_service.edit_rol(9999, updated_role_data)
    assert excinfo.value.status_code == 404
    assert "El rol no existe" in str(excinfo.value.detail)
