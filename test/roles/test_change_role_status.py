import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.database import SessionLocal
from app.roles.services import RoleService
from app.roles.models import Role, Vars
import uuid

@pytest.fixture(scope="function")
def db():
    """Fixture para manejar una sesión de base de datos en pruebas con rollback"""
    db = SessionLocal()

    # Listas para rastrear los roles y estados creados en la prueba
    created_role_ids = []
    created_status_ids = []

    yield db, created_role_ids, created_status_ids  # Proporciona la sesión y las listas de IDs creados

    # 🔹 Eliminar los roles creados en la prueba
    if created_role_ids:
        db.execute(
            text("DELETE FROM rol WHERE id = ANY(:role_ids)"),
            {"role_ids": created_role_ids}
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

def test_change_role_status_success(role_service, db):
    """✅ Prueba cambiar el estado de un rol correctamente"""
    db_session, created_role_ids, created_status_ids = db

    # 🔹 Crear un estado en la tabla `vars` con `type="status"`
    status = Vars(name="Estado Activo", type="status")
    db_session.add(status)
    db_session.commit()
    db_session.refresh(status)
    created_status_ids.append(status.id)  # Guardamos el ID del estado creado

    # 🔹 Crear un rol de prueba con un estado inicial
    role = Role(name=f"Status_Role_{uuid.uuid4().hex[:8]}", description="Role to test status", status=status.id)
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    created_role_ids.append(role.id)

    # 🔹 Crear otro estado para cambiarlo
    new_status = Vars(name="Estado Inactivo", type="status")  
    db_session.add(new_status)
    db_session.commit()
    db_session.refresh(new_status)
    created_status_ids.append(new_status.id)  # Guardamos el ID del nuevo estado creado

    # 🔹 Cambiar estado del rol
    response = role_service.change_role_status(role.id, new_status.id)

    assert response["success"] is True
    assert response["data"] == "Estado de rol actualizado correctamente."

    # 🔹 Verificar que el estado se actualizó en la base de datos
    updated_role = db_session.query(Role).filter_by(id=role.id).first()
    assert updated_role is not None
    assert updated_role.status == new_status.id  # Se asegura que el estado cambió

def test_change_role_status_not_found(role_service):
    """❌ Prueba cambiar el estado de un rol inexistente"""
    with pytest.raises(HTTPException) as excinfo:
        role_service.change_role_status(9999, 2)  # ID de rol inexistente
    assert excinfo.value.status_code == 404  
    assert "Rol no encontrado" in str(excinfo.value.detail)
