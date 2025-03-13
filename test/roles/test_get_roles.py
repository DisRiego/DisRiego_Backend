import pytest
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.roles.services import RoleService
from app.roles.models import Role, Vars
from sqlalchemy import text

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
def setup_roles(db: Session):
    """Crear roles de prueba en la base de datos"""
    # Crear un estado de prueba si no existe
    status = db.query(Vars).filter_by(name="Activo").first()
    if not status:
        status = Vars(name="Activo", type="default")  # Se asigna type para evitar error
        db.add(status)
        db.commit()
        db.refresh(status)

    # Crear roles de prueba
    role1 = Role(name="Admin", description="Rol de administrador", status=status.id)
    role2 = Role(name="User", description="Rol de usuario", status=status.id)

    db.add_all([role1, role2])
    db.commit()
    db.refresh(role1)
    db.refresh(role2)

    yield [role1, role2]  # Retorna los roles creados para usarlos en la prueba

    # 🔹 Primero elimina referencias en `user_rol`
    db.execute(text("DELETE FROM user_rol WHERE rol_id IN (SELECT id FROM rol)"))
    db.commit()

    # 🔹 Luego elimina referencias en `rol_permission`
    db.execute(text("DELETE FROM rol_permission WHERE rol_id IN (SELECT id FROM rol)"))
    db.commit()

    # 🔹 Ahora sí elimina los roles
    db.query(Role).delete()
    db.commit()

def test_get_roles(role_service, setup_roles):
    """✅ Prueba para obtener la lista de roles correctamente"""
    response = role_service.get_roles()

    assert response["success"] is True
    assert "data" in response
    assert len(response["data"]) >= 2  # Al menos los dos que agregamos en la prueba

    # Validar que los roles existen en la respuesta
    role_names = {role["role_name"] for role in response["data"]}
    assert "Admin" in role_names
    assert "User" in role_names
