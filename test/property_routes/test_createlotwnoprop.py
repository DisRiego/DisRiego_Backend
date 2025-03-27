import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
import os
import random

FILE_DIR = "files"
VALID_DEED = os.path.join(FILE_DIR, "public_deed.pdf")
VALID_CERT = os.path.join(FILE_DIR, "freedom_certificate.pdf")

@pytest.mark.asyncio
async def test_create_lot_in_nonexistent_property():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # ⚠️ Usamos un ID de predio que seguramente no existe (muy alto)
        fake_property_id = 999999  

        reg_number = random.randint(10000000, 99999999)

        with open(VALID_DEED, "rb") as deed, open(VALID_CERT, "rb") as cert:
            response = await client.post("/properties/lot/", files={
                "public_deed": ("public_deed.pdf", deed, "application/pdf"),
                "freedom_tradition_certificate": ("freedom_certificate.pdf", cert, "application/pdf")
            }, data={
                "property_id": str(fake_property_id),
                "name": "Lote fantasma",
                "longitude": "-75.1",
                "latitude": "6.1",
                "extension": "50",
                "real_estate_registration_number": str(reg_number)
            })

        print("❌ Status:", response.status_code)
        print("❌ JSON:", response.json())

        assert response.status_code == 400
        assert response.json()["success"] is False
        assert "predio no existe" in response.json()["data"]["message"].lower()
