import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.database import SessionLocal
from app.roles.models import Role
from app.users.models import User
from app.roles.services import UserRoleService
from app.roles.schemas import AssignRoleRequest, UpdateUserRoles

client = TestClient(app)

@pytest.fixture(scope="function")
def setup_db():
    """Fixture para configurar la base de datos y hacer rollback después de cada prueba"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture(scope="function")
def create_test_user(setup_db: Session):
    """Crear un usuario de prueba en la base de datos"""

    # Verificar si el usuario ya existe para evitar el error de clave única
    existing_user = setup_db.query(User).filter(User.email == "test@example.com").first()
    if existing_user:
        setup_db.delete(existing_user)
        setup_db.commit()

    test_user = User(name="Test User", email="test@example.com")
    setup_db.add(test_user)
    setup_db.commit()
    setup_db.refresh(test_user)

    yield test_user

    # Limpieza: Eliminar el usuario después de la prueba
    setup_db.delete(test_user)
    setup_db.commit()



@pytest.fixture(scope="function")
def create_test_role(setup_db: Session):
    """Crear un rol de prueba en la base de datos"""
    test_role = Role(name="Test Role", description="Rol de prueba", status=1)
    setup_db.add(test_role)
    setup_db.commit()
    setup_db.refresh(test_role)
    return test_role


def test_assign_role_to_user(setup_db, create_test_user, create_test_role):
    """Prueba para asignar un rol a un usuario"""
    user_id = create_test_user.id
    role_id = create_test_role.id

    response = client.post("/roles/assign_role/", json={"user_id": user_id, "role_id": role_id})

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"] == "Rol asignado correctamente"


def test_get_user_roles(setup_db, create_test_user, create_test_role):
    """Prueba para obtener los roles de un usuario"""
    user_id = create_test_user.id
    role_id = create_test_role.id

    # Asignar rol antes de probar la obtención de roles
    role_service = UserRoleService(setup_db)
    role_service.assign_role_to_user(user_id, role_id)

    response = client.get(f"/roles/user/{user_id}/roles")

    assert response.status_code == 200
    assert "data" in response.json()
    assert isinstance(response.json()["data"]["roles"], list)
    assert len(response.json()["data"]["roles"]) >= 1  # El usuario debe tener al menos 1 rol


def test_update_user_roles(setup_db, create_test_user, create_test_role):
    """Prueba para actualizar los roles de un usuario"""
    user_id = create_test_user.id
    role_id = create_test_role.id

    role_service = UserRoleService(setup_db)
    role_service.assign_role_to_user(user_id, role_id)

    new_roles = [role_id]  # Lista con un solo rol
    response = client.put(f"/roles/user/{user_id}/roles", json={"roles": new_roles})

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(response.json()["data"]["roles"]) == len(new_roles)


def test_revoke_role_from_user(setup_db, create_test_user, create_test_role):
    """Prueba para revocar un rol de un usuario"""
    user_id = create_test_user.id
    role_id = create_test_role.id

    role_service = UserRoleService(setup_db)
    role_service.assign_role_to_user(user_id, role_id)

    response = client.delete(f"/roles/user/{user_id}/role/{role_id}")

    print("RESPONSE:", response.json())  # <-- Agregar esto para ver el error

    assert response.status_code == 400


def test_revoke_role_from_user_with_one_role(setup_db, create_test_user, create_test_role):
    """Prueba para intentar revocar el único rol de un usuario"""
    user_id = create_test_user.id
    role_id = create_test_role.id

    role_service = UserRoleService(setup_db)
    role_service.assign_role_to_user(user_id, role_id)

    response = client.delete(f"/roles/user/{user_id}/role/{role_id}")

    assert response.status_code == 400
    assert "El usuario debe tener al menos un rol asignado" in response.json()["detail"]["data"]


def test_get_user_roles_not_found(setup_db):
    """Prueba para obtener roles de un usuario inexistente"""
    user_id = 9999  # Un ID que no existe en la base de datos

    response = client.get(f"/roles/user/{user_id}/roles")

    assert response.status_code == 404
    assert "Usuario no encontrado" in response.json()["detail"]["data"]
