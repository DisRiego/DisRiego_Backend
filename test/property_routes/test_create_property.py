import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import status
from app.main import app
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.users.models import User
from app.property_routes.models import Property, PropertyUser
from app.roles.models import Vars
import os
import random

FILE_DIR = "files"
VALID_DEED = os.path.join(FILE_DIR, "public_deed.pdf")
VALID_CERT = os.path.join(FILE_DIR, "freedom_certificate.pdf")
INVALID_FILE = os.path.join(FILE_DIR, "invalid.txt")

@pytest.fixture()
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="session", autouse=True)
def ensure_state_exists():
    db = SessionLocal()
    try:
        state_id = 16
        if not db.query(Vars).filter_by(id=state_id).first():
            db.add(Vars(id=state_id, name="Activo", type="estado_predio"))
            db.commit()
    finally:
        db.close()

@pytest.fixture()
def test_user(db: Session):
    """Crea un usuario si no existe y lo elimina después si fue creado"""
    document_number = "123456789"
    user = db.query(User).filter_by(document_number=document_number).first()
    created = False

    if not user:
        user = User(
            name="Test",
            first_last_name="User",
            second_last_name="Example",
            document_number=document_number,
            type_document_id=1
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        created = True

    yield user

    if created:
        db.delete(user)
        db.commit()

@pytest.mark.asyncio
async def test_create_property_success(db, test_user):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg_number = random.randint(10000000, 99999999)

        with open(VALID_DEED, "rb") as deed, open(VALID_CERT, "rb") as cert:
            response = await client.post("/properties/", files={
                "public_deed": ("public_deed.pdf", deed, "application/pdf"),
                "freedom_tradition_certificate": ("freedom_certificate.pdf", cert, "application/pdf")
            }, data={
                "user_id": str(test_user.id),
                "name": "Predio Exitoso",
                "longitude": "-75.0",
                "latitude": "6.0",
                "extension": "500",
                "real_estate_registration_number": str(reg_number)
            })

            print("❗ DEBUG Response status code:", response.status_code)
            print("❗ DEBUG Response JSON:", response.json())

            assert response.status_code == 200
            assert response.json()["success"] is True

        # 🔁 Limpiar el predio solo si fue creado
        created_property = db.query(Property).filter_by(real_estate_registration_number=reg_number).first()
        if created_property:
            # Eliminar relación en tabla intermedia
            db.query(PropertyUser).filter_by(property_id=created_property.id).delete()
            db.delete(created_property)
            db.commit()


@pytest.mark.asyncio
async def test_create_property_missing_fields(test_user):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/properties/", data={"user_id": test_user.id})
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_property_user_not_exist():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with open(VALID_DEED, "rb") as deed, open(VALID_CERT, "rb") as cert:
            response = await client.post("/properties/", files={
                "public_deed": ("public_deed.pdf", deed, "application/pdf"),
                "freedom_tradition_certificate": ("freedom_certificate.pdf", cert, "application/pdf")
            }, data={
                "user_id": 999999,
                "name": "Predio Fantasma",
                "longitude": "-75.0",
                "latitude": "6.0",
                "extension": "500",
                "real_estate_registration_number": 87654321
            })
            assert response.status_code == 400
            assert "usuario a relacionar no existe" in response.text


@pytest.mark.asyncio
async def test_create_property_duplicate_registration(test_user):
    transport = ASGITransport(app=app)
    reg_number = 11223344
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with open(VALID_DEED, "rb") as deed, open(VALID_CERT, "rb") as cert:
            await client.post("/properties/", files={
                "public_deed": ("public_deed.pdf", deed, "application/pdf"),
                "freedom_tradition_certificate": ("freedom_certificate.pdf", cert, "application/pdf")
            }, data={
                "user_id": test_user.id,
                "name": "Predio Original",
                "longitude": "-75.0",
                "latitude": "6.0",
                "extension": "500",
                "real_estate_registration_number": reg_number
            })

        with open(VALID_DEED, "rb") as deed, open(VALID_CERT, "rb") as cert:
            response = await client.post("/properties/", files={
                "public_deed": ("public_deed.pdf", deed, "application/pdf"),
                "freedom_tradition_certificate": ("freedom_certificate.pdf", cert, "application/pdf")
            }, data={
                "user_id": test_user.id,
                "name": "Predio Duplicado",
                "longitude": "-75.1",
                "latitude": "6.1",
                "extension": "600",
                "real_estate_registration_number": reg_number
            })
            assert response.status_code == 400
            assert "registro de predio ya existe" in response.text


@pytest.mark.asyncio
async def test_create_property_invalid_files(test_user):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with open(INVALID_FILE, "rb") as deed, open(INVALID_FILE, "rb") as cert:
            response = await client.post("/properties/", files={
                "public_deed": ("invalid.txt", deed, "text/plain"),
                "freedom_tradition_certificate": ("invalid.txt", cert, "text/plain")
            }, data={
                "user_id": test_user.id,
                "name": "Predio Archivo Invalido",
                "longitude": "-70.0",
                "latitude": "5.0",
                "extension": "100",
                "real_estate_registration_number": 99887766
            })
            assert response.status_code in (400, 500)


@pytest.mark.asyncio
async def test_create_property_missing_optional_files(test_user):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/properties/", data={
            "user_id": test_user.id,
            "name": "Predio Sin Archivos",
            "longitude": "-75.0",
            "latitude": "6.0",
            "extension": "500",
            "real_estate_registration_number": 44556677
        })
        assert response.status_code in (200, 400, 422)


@pytest.mark.asyncio
async def test_create_property_out_of_range(test_user):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with open(VALID_DEED, "rb") as deed, open(VALID_CERT, "rb") as cert:
            response = await client.post("/properties/", files={
                "public_deed": ("public_deed.pdf", deed, "application/pdf"),
                "freedom_tradition_certificate": ("freedom_certificate.pdf", cert, "application/pdf")
            }, data={
                "user_id": test_user.id,
                "name": "Predio Fuera Rango",
                "longitude": "-200",
                "latitude": "95",
                "extension": "-100",
                "real_estate_registration_number": -10
            })
            assert response.status_code in (400, 422)
