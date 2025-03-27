import pytest
from fastapi import HTTPException
from sqlalchemy import text
from app.database import SessionLocal
from app.roles.services import RoleService
from app.roles.schemas import RoleCreate
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

    yield db, created_role_ids, created_permission_ids, created_status_ids  # Proporciona la sesión y listas de IDs creados

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


def test_create_role_success(role_service, db):
    """✅ Prueba de creación exitosa de un rol con al menos un permiso"""
    db_session, created_role_ids, created_permission_ids, created_status_ids = db

    # 🔹 Verificar si el estado 1 existe en la tabla `vars`, si no, crearlo
    status = db_session.query(Vars).filter_by(id=1).first()
    if not status:
        status = Vars(id=1, name="Activo", type="status")
        db_session.add(status)
        db_session.commit()
        db_session.refresh(status)
        created_status_ids.append(status.id)  # Guardar para eliminarlo al final

    # 🔹 Crear un nombre único para el permiso
    permission_name = f"Test_Permission_{uuid.uuid4().hex[:8]}"  

    # 🔹 Crear un permiso en la base de datos
    permission = Permission(name=permission_name, description="Permission for testing", category="General")
    db_session.add(permission)
    db_session.commit()
    db_session.refresh(permission)

    # Guardamos el ID del permiso creado
    created_permission_ids.append(permission.id)

    # 🔹 Crear un nombre único para el rol
    role_name = f"Test_Role_{uuid.uuid4().hex[:8]}"  

    # 🔹 Crear un rol con al menos un permiso
    role_data = RoleCreate(name=role_name, description="Role for testing", permissions=[permission.id])

    response = role_service.create_role(role_data)

    assert response is not None
    assert response.name == role_name
    assert response.description == "Role for testing"
    assert isinstance(response.id, int)  

    # Guardamos el ID del rol creado para eliminarlo al final
    created_role_ids.append(response.id)

    # Verificar que el rol se creó en la BD
    created_role = db_session.query(Role).filter_by(name=role_name).first()
    assert created_role is not None
    assert len(created_role.permissions) == 1  # Debe tener al menos un permiso asignado


def test_create_duplicate_role(role_service, db):
    """❌ Prueba de intento de crear un rol con un nombre duplicado"""
    db_session, created_role_ids, created_permission_ids, created_status_ids = db

    # 🔹 Verificar si el estado 1 existe en la tabla `vars`, si no, crearlo
    status = db_session.query(Vars).filter_by(id=1).first()
    if not status:
        status = Vars(id=1, name="Activo", type="status")
        db_session.add(status)
        db_session.commit()
        db_session.refresh(status)
        created_status_ids.append(status.id)  

    # 🔹 Crear un nombre único para el permiso
    permission_name = f"Test_Permission_{uuid.uuid4().hex[:8]}"  

    # 🔹 Crear un permiso en la base de datos
    permission = Permission(name=permission_name, description="Permission for testing", category="General")
    db_session.add(permission)
    db_session.commit()
    db_session.refresh(permission)

    # Guardamos el ID del permiso creado
    created_permission_ids.append(permission.id)

    # 🔹 Crear un nombre único para el rol
    role_name = f"Test_Role_{uuid.uuid4().hex[:8]}"  

    # 🔹 Crear el rol por primera vez con al menos un permiso
    role_data = RoleCreate(name=role_name, description="Role for testing", permissions=[permission.id])
    response = role_service.create_role(role_data)
    created_role_ids.append(response.id)  

    # Intentar crearlo de nuevo y verificar que lanza un error 400
    with pytest.raises(HTTPException) as exc_info:
        role_service.create_role(role_data)

    assert exc_info.value.status_code == 400
    assert "El rol ya existe" in str(exc_info.value.detail)
