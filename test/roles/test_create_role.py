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
    db = SessionLocal()
    created_role_ids = []
    created_permission_ids = []
    created_status_ids = []

    yield db, created_role_ids, created_permission_ids, created_status_ids

    if created_role_ids:
        db.execute(
            text("DELETE FROM rol_permission WHERE rol_id = ANY(:role_ids)"),
            {"role_ids": created_role_ids}
        )
        db.commit()
        db.execute(
            text("DELETE FROM rol WHERE id = ANY(:role_ids)"),
            {"role_ids": created_role_ids}
        )
        db.commit()

    if created_permission_ids:
        db.execute(
            text("DELETE FROM permission WHERE id = ANY(:permission_ids)"),
            {"permission_ids": created_permission_ids}
        )
        db.commit()

    if created_status_ids:
        db.execute(
            text("DELETE FROM vars WHERE id = ANY(:status_ids)"),
            {"status_ids": created_status_ids}
        )
        db.commit()

    db.rollback()
    db.close()

@pytest.fixture()
def role_service(db):
    return RoleService(db[0])

def test_create_role_success(role_service, db):
    db_session, created_role_ids, _, created_status_ids = db

    # 🔹 Verificar si el estado "Activo" ya existe
    status = db_session.query(Vars).filter_by(id=1).first()
    if not status:
        status = Vars(id=1, name="Activo", type="status")
        db_session.add(status)
        db_session.commit()
        db_session.refresh(status)
        created_status_ids.append(status.id)

    # ✅ Usar permiso existente en la base de datos, por ejemplo ID 2 ("Añadir rol")
    existing_permission = db_session.query(Permission).filter_by(id=2).first()
    assert existing_permission is not None, "Permiso con ID 2 no existe en la base de datos"

    # 🔹 Crear un nombre único para el rol
    role_name = f"Test_Role_{uuid.uuid4().hex[:8]}"
    role_data = RoleCreate(
        name=role_name,
        description="Role for testing",
        permissions=[existing_permission.id]
    )

    response = role_service.create_role(role_data)

    assert response is not None
    assert response.name == role_name
    assert response.description == "Role for testing"
    assert isinstance(response.id, int)

    created_role_ids.append(response.id)

    created_role = db_session.query(Role).filter_by(name=role_name).first()
    assert created_role is not None
    assert len(created_role.permissions) == 1

def test_create_duplicate_role(role_service, db):
    db_session, created_role_ids, _, created_status_ids = db

    status = db_session.query(Vars).filter_by(id=1).first()
    if not status:
        status = Vars(id=1, name="Activo", type="status")
        db_session.add(status)
        db_session.commit()
        db_session.refresh(status)
        created_status_ids.append(status.id)

    # ✅ Usar permiso existente en la base
    existing_permission = db_session.query(Permission).filter_by(id=2).first()
    assert existing_permission is not None, "Permiso con ID 2 no existe en la base de datos"

    role_name = f"Test_Role_{uuid.uuid4().hex[:8]}"
    role_data = RoleCreate(
        name=role_name,
        description="Role for testing",
        permissions=[existing_permission.id]
    )

    response = role_service.create_role(role_data)
    created_role_ids.append(response.id)

    with pytest.raises(HTTPException) as exc_info:
        role_service.create_role(role_data)

    assert exc_info.value.status_code == 400
    assert "El rol ya existe" in str(exc_info.value.detail)
