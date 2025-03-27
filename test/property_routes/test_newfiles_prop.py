import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import status
from app.main import app
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.users.models import User
from app.property_routes.models import Property, PropertyUser
import os
import random

FILE_DIR = "files"
VALID_DEED = os.path.join(FILE_DIR, "public_deed.pdf")
VALID_CERT = os.path.join(FILE_DIR, "freedom_certificate.pdf")
NEW_DEED = os.path.join(FILE_DIR, "new_deed.pdf")
NEW_CERT = os.path.join(FILE_DIR, "new_certificate.pdf")


@pytest.fixture()
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def test_user(db: Session):
    document_number = "223344556"
    user = db.query(User).filter_by(document_number=document_number).first()
    created = False

    if not user:
        user = User(
            name="Test",
            first_last_name="Updater",
            second_last_name="Property",
            document_number=document_number,
            type_document_id=1,
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
async def test_update_property_with_new_files(db, test_user):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg_number = random.randint(11111111, 99999999)

        # Crear el predio primero
        with open(VALID_DEED, "rb") as deed, open(VALID_CERT, "rb") as cert:
            create_response = await client.post("/properties/", files={
                "public_deed": ("original.pdf", deed, "application/pdf"),
                "freedom_tradition_certificate": ("original_cert.pdf", cert, "application/pdf")
            }, data={
                "user_id": str(test_user.id),
                "name": "Predio para editar archivos",
                "longitude": "-75.1",
                "latitude": "6.1",
                "extension": "1000",
                "real_estate_registration_number": str(reg_number)
            })

            assert create_response.status_code == 200
            assert create_response.json()["success"] is True

        # Buscar el predio creado
        property_obj = db.query(Property).filter_by(real_estate_registration_number=reg_number).first()
        assert property_obj is not None

        # Actualizar con nuevos archivos
        with open(NEW_DEED, "rb") as new_deed, open(NEW_CERT, "rb") as new_cert:
            update_response = await client.put(f"/properties/{property_obj.id}", files={
                "public_deed": ("new_deed.pdf", new_deed, "application/pdf"),
                "freedom_tradition_certificate": ("new_cert.pdf", new_cert, "application/pdf")
            }, data={
                "user_id": str(test_user.id),
                "name": "Predio Editado Archivos",
                "longitude": "-75.2",
                "latitude": "6.2",
                "extension": "1200",
                "real_estate_registration_number": str(reg_number)
            })

            print("📄 Update response:", update_response.json())
            assert update_response.status_code == 200
            assert update_response.json()["success"] is True
            assert "editado satisfactoriamente" in update_response.json()["data"]["message"].lower()

        # Limpiar
        db.query(PropertyUser).filter_by(property_id=property_obj.id).delete()
        db.delete(property_obj)
        db.commit()