import pytest
import random
from httpx import AsyncClient, ASGITransport
from app.database import SessionLocal
from app.main import app
from app.property_routes.models import Property, PropertyUser, Lot
from app.users.models import User
from app.firebase_config import FIREBASE_STORAGE_BUCKET
from sqlalchemy import text


VALID_DEED = "files/public_deed.pdf"
VALID_CERT = "files/freedom_certificate.pdf"
NEW_DEED = "files/new_deed.pdf"
NEW_CERT = "files/new_certificate.pdf"

@pytest.mark.asyncio
async def test_update_lot_files():
    db = SessionLocal()  # Crea la sesión manualmente

    try:
        # Crear usuario
        user = User(
            name="ArchivosLote",
            first_last_name="Cambio",
            second_last_name="Archivos",
            document_number=str(random.randint(100000000, 999999999)),
            type_document_id=1
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Crear predio
        property_ = Property(
            name="Predio archivos",
            longitude=-75.0,
            latitude=6.0,
            extension=500,
            real_estate_registration_number=random.randint(10000000, 99999999),
            public_deed="https://fakeurl.com/original_deed.pdf",
            freedom_tradition_certificate="https://fakeurl.com/original_cert.pdf",
            state=16
        )
        db.add(property_)
        db.commit()
        db.refresh(property_)

        # Relación con usuario
        db.add(PropertyUser(user_id=user.id, property_id=property_.id))
        db.commit()

        # Crear lote vía API
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            reg_number = random.randint(10000000, 99999999)

            with open(VALID_DEED, "rb") as deed, open(VALID_CERT, "rb") as cert:
                create_response = await client.post("/properties/lot/", files={
                    "public_deed": ("public_deed.pdf", deed, "application/pdf"),
                    "freedom_tradition_certificate": ("freedom_certificate.pdf", cert, "application/pdf")
                }, data={
                    "property_id": str(property_.id),
                    "name": "Lote con archivos",
                    "longitude": "-75.3",
                    "latitude": "6.3",
                    "extension": "250",
                    "real_estate_registration_number": str(reg_number)
                })

            assert create_response.status_code == 200
            assert create_response.json()["success"] is True

            # Obtener lote creado
            lot = db.query(Lot).filter(Lot.real_estate_registration_number == str(reg_number)).first()
            

            original_deed_url = lot.public_deed
            original_cert_url = lot.freedom_tradition_certificate

            # Actualizar archivos del lote
            with open(NEW_DEED, "rb") as new_deed, open(NEW_CERT, "rb") as new_cert:
                update_response = await client.put(f"/properties/lot/{lot.id}", files={
                    "public_deed": ("new_deed.pdf", new_deed, "application/pdf"),
                    "freedom_tradition_certificate": ("new_certificate.pdf", new_cert, "application/pdf")
                }, data={
                    "name": "Lote actualizado",
                    "longitude": "-75.4",
                    "latitude": "6.4",
                    "extension": "300",
                    "real_estate_registration_number": str(reg_number)
                })

            assert update_response.status_code == 200
            assert update_response.json()["success"] is True

            # Validar que las URLs hayan cambiado
            db.refresh(lot)
            assert lot.public_deed != original_deed_url
            assert lot.freedom_tradition_certificate != original_cert_url
            assert FIREBASE_STORAGE_BUCKET in lot.public_deed
            assert FIREBASE_STORAGE_BUCKET in lot.freedom_tradition_certificate

        # Limpieza

        db.delete(lot)  # Elimina el lote

        # Elimina relaciones del usuario con el predio
        db.query(PropertyUser).filter_by(user_id=user.id, property_id=property_.id).delete()

        # Elimina relación en tabla intermedia property_lot
        db.execute(
            text("DELETE FROM property_lot WHERE property_id = :property_id"),
            {"property_id": property_.id}
        )



        #Luego elimina predio y usuario
        db.delete(property_)
        db.delete(user)
        db.commit()

    finally:
        db.close()
