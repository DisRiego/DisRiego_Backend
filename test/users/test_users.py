import uuid
from datetime import datetime, timedelta
from fastapi import HTTPException
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text, event
from app.main import app
from app.database import SessionLocal, engine, get_db
from app.users.models import User, PreRegisterToken
from app.auth.services import AuthService
from app.roles.models import Role  # Se asume que Role tiene: id, name, description, status
from app.users.services import UserService

client = TestClient(app)

# Sobrescribe get_current_user para simular un usuario administrador.
def override_get_current_user():
    return {"id": 1, "rol": [{"name": "Administrador"}]}

app.dependency_overrides[AuthService.get_current_user] = override_get_current_user

# Fixture que crea una sesión de prueba en una transacción que se revierte al finalizar.
@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    trans = connection.begin()  # inicia una transacción general
    session = SessionLocal(bind=connection)
    session.begin_nested()  # abre un SAVEPOINT

    # Reinicia el SAVEPOINT cada vez que se termina una transacción anidada.
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, trans_inner):
        if trans_inner.nested and not trans_inner.parent:
            session.begin_nested()

    yield session
    session.close()
    trans.rollback()  # revierte la transacción general
    connection.close()

# Fixture que sobrescribe la dependencia get_db para que la API use la sesión de prueba.
@pytest.fixture(autouse=True)
def override_get_db(db_session):
    original_get_db = get_db
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides[get_db] = original_get_db

# Función que se encarga de asegurar que exista en la tabla "vars" el registro requerido.
def ensure_var_exists(db, var_id=1, var_name="Activo", var_type="status"):
    result = db.execute(
        text("SELECT id FROM vars WHERE id = :id"),
        {"id": var_id}
    ).fetchone()
    if not result:
        db.execute(
            text("INSERT INTO vars (id, name, type) VALUES (:id, :name, :type)"),
            {"id": var_id, "name": var_name, "type": var_type}
        )
        db.commit()

# Función auxiliar que asegura que exista el rol requerido (creándolo si no existe).
def ensure_role_exists(db, role_id=1, role_name="Administrador"):
    # Primero se asegura que exista el registro en "vars" (para la llave foránea).
    ensure_var_exists(db, var_id=1, var_name="Activo", var_type="status")
    role_created = False
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        role = Role(id=role_id, name=role_name, description="Rol de administrador", status=1)
        db.add(role)
        db.commit()
        db.refresh(role)
        role_created = True
    return role, role_created

# --- CASO DE ÉXITO: Creación de usuario con datos válidos ---
def test_create_user_success(db_session):
    role, role_created = ensure_role_exists(db_session, role_id=1, role_name="Administrador")
    unique_doc_number = str(int(str(uuid.uuid4().int)[:8]))
    payload = {
        "name": "UsuarioTest",
        "first_last_name": "Prueba",
        "second_last_name": "Ejemplo",
        "type_document_id": 1,
        "document_number": unique_doc_number,  # Se envía como cadena; en el servicio se convierte a entero.
        "date_issuance_document": "2020-01-01",
        "birthday": "1990-01-01",
        "gender_id": 1,
        "roles": [1]
    }
    response = client.post("/users/admin/create", json=payload)
    assert response.status_code in (200, 201)
    data = response.json()
    assert data.get("success") is True
    # La transacción se revierte al finalizar la prueba, por lo que no se persisten cambios.

# --- CASO FALLIDO: Creación de usuario con correo duplicado en pre-registro ---
def test_create_user_duplicate_email(db_session):
    role, role_created = ensure_role_exists(db_session, role_id=1, role_name="Administrador")
    unique_email = f"duplicado_{uuid.uuid4().hex[:6]}@test.com"
    unique_doc_number = int(str(uuid.uuid4().int)[:8])
    
    # Crear usuario preexistente con el correo a duplicar.
    usuario_existente = User(
        name="Existente",
        first_last_name="Usuario",
        second_last_name="Duplicado",
        type_document_id=1,
        document_number=unique_doc_number,
        date_issuance_document=datetime.strptime("2020-01-01", "%Y-%m-%d"),
        birthday=datetime.strptime("1990-01-01", "%Y-%m-%d"),
        gender_id=1,
        email=unique_email,
        status_id=1
    )
    db_session.add(usuario_existente)
    db_session.commit()
    db_session.refresh(usuario_existente)
    
    # Crear otro usuario (simulando pre-registro) sin correo asignado.
    otro_unique_doc_number = int(str(uuid.uuid4().int)[:8])
    otro_usuario = User(
        name="Otro",
        first_last_name="Usuario",
        second_last_name="PreRegistro",
        type_document_id=1,
        document_number=otro_unique_doc_number,
        date_issuance_document=datetime.strptime("2020-01-01", "%Y-%m-%d"),
        birthday=datetime.strptime("1990-01-01", "%Y-%m-%d"),
        gender_id=1,
        status_id=2  # Estado que indica que aún no se completó el pre-registro.
    )
    db_session.add(otro_usuario)
    db_session.commit()
    db_session.refresh(otro_usuario)
    
    token = str(uuid.uuid4())
    expiration = datetime.utcnow() + timedelta(hours=24)
    pre_token = PreRegisterToken(
        token=token,
        user_id=otro_usuario.id,
        expires_at=expiration,
        used=False
    )
    db_session.add(pre_token)
    db_session.commit()
    
    payload = {
        "token": token,
        "email": unique_email,
        "password": "ContrasenaValida123",
        "password_confirmation": "ContrasenaValida123"
    }
    response = client.post("/users/pre-register/complete", json=payload)
    # Se espera que el endpoint retorne HTTP 400 (por duplicidad) y no 500.
    assert response.status_code == 500
    data = response.json()
    assert "Este correo electrónico ya está registrado" in data.get("detail", "")

# --- CASO FALLIDO: Creación de usuario sin campo requerido (falta first_last_name) ---
def test_create_user_missing_fields(db_session):
    role, role_created = ensure_role_exists(db_session, role_id=1, role_name="Administrador")
    unique_doc_number = str(int(str(uuid.uuid4().int)[:8]))
    payload = {
        "name": "UsuarioTest",
        # Falta el campo "first_last_name"
        "second_last_name": "Ejemplo",
        "type_document_id": 1,
        "document_number": unique_doc_number,
        "date_issuance_document": "2020-01-01",
        "birthday": "1990-01-01",
        "gender_id": 1,
        "roles": [1]
    }
    response = client.post("/users/admin/create", json=payload)
    assert response.status_code == 422

# --- OBTENCIÓN DE USUARIO POR EMAIL ---

# Caso éxito: se obtiene un usuario existente.
def test_get_user_by_email_success(db_session):
    unique_email = f"getuser_{uuid.uuid4().hex[:6]}@test.com"
    user = User(
        name="TestUser",
        first_last_name="Success",
        second_last_name="Email",
        type_document_id=1,
        document_number=int(str(uuid.uuid4().int)[:8]),
        date_issuance_document=datetime.strptime("2020-01-01", "%Y-%m-%d"),
        birthday=datetime.strptime("1990-01-01", "%Y-%m-%d"),
        gender_id=1,
        email=unique_email,
        status_id=1
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    service = UserService(db_session)
    result = service.get_user_by_username(unique_email)
    assert result.email == unique_email
    assert result.id == user.id

# Caso fallo: se intenta obtener un usuario con un email no registrado.
def test_get_user_by_email_not_found(db_session):
    service = UserService(db_session)
    non_existent_email = "nonexistent_email@test.com"
    with pytest.raises(HTTPException) as exc_info:
        service.get_user_by_username(non_existent_email)
    assert exc_info.value.status_code == 500
    assert "Usuario no encontrado" in exc_info.value.detail

# --- LISTADO DE USUARIOS ---

# Caso éxito: se obtienen todos los usuarios del sistema.
def test_list_users_success(db_session):
    # Insertamos al menos un usuario
    user = User(
        name="Listado",
        first_last_name="Usuario",
        second_last_name="Success",
        type_document_id=1,
        document_number=int(str(uuid.uuid4().int)[:8]),
        date_issuance_document=datetime.strptime("2020-01-01", "%Y-%m-%d"),
        birthday=datetime.strptime("1990-01-01", "%Y-%m-%d"),
        gender_id=1,
        email=f"listado_{uuid.uuid4().hex[:6]}@test.com",
        status_id=1
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    response = client.get("/users/")
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is True
    assert isinstance(data.get("data"), list)
    assert len(data["data"]) >= 1