from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app.property_routes.services import PropertyLotService

router = APIRouter(prefix="/properties", tags=["Properties"])

@router.post("/", response_model=dict)
async def create_property(
    name: str = Form(...),  # Asegúrate de usar Form para campos de texto
    longitude: float = Form(...),
    latitude: float = Form(...),
    extension: float = Form(...),
    real_estate_registration_number: int = Form(...),
    description: str = Form(None),  # Descripción opcional
    location: str = Form(None), 
    freedom_tradition_certificate: UploadFile = File(...),  # Asegúrate de que los archivos sean obligatorios
    public_deed: UploadFile = File(...),
    db: Session = Depends(get_db)  # Dependencia de la base de datos
):
    try:
        # Creamos una instancia del servicio para manejar la lógica
        property_service = PropertyLotService(db)

        # Llamamos al método para crear el predio
        return await property_service.create_property(
            name=name,
            longitude=longitude,
            latitude=latitude,
            extension=extension,
            real_estate_registration_number=real_estate_registration_number,
            public_deed=public_deed,
            freedom_tradition_certificate=freedom_tradition_certificate,
            description=description,
            location=location,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear el predio: {str(e)}")

@router.post("/lot/create", response_model=dict)
def create_lot(name: str, area: float, property_id: int, db: Session = Depends(get_db)):
    service = PropertyLotService(db)
    return service.create_lot(name, area, property_id)

@router.post("/link", response_model=dict)
def link_property_lot(property_id: int, lot_id: int, db: Session = Depends(get_db)):
    service = PropertyLotService(db)
    return service.link_property_lot(property_id, lot_id)

@router.post("/inhabilitate/{property_id}", response_model=dict)
def property_inhabilitate(property_id: int, db: Session = Depends(get_db)):
    service = PropertyLotService(db)
    return service.property_inhabilitate(property_id)

@router.get("/")
def list_properties(db: Session = Depends(get_db)):
    """Obtener todos los predios"""
    try:
        property_service = PropertyLotService(db)
        properties = property_service.get_all_properties()
        return properties
    except HTTPException as e:
        raise e  # Re-raise HTTPException for known errors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los predios: {str(e)}")
