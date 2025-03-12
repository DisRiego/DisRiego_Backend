from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app.property_routes.services import PropertyLotService
from app.property_routes.schemas import PropertyCreate, PropertyResponse

router = APIRouter(prefix="/properties", tags=["Properties"])

@router.post("/", response_model=dict)
async def create_property(
    name: str = Form(...),  # Usamos Form para los campos de texto
    longitude: float = Form(...),
    latitude: float = Form(...),
    extension: float = Form(...),
    real_estate_registration_number: int = Form(...),
    description: str = Form(None),  # Descripción opcional
    location: str = Form(None), 
    freedom_tradition_certificate: UploadFile = File(...),  # Archivos obligatorios
    public_deed: UploadFile = File(...),
    db: Session = Depends(get_db)  # Dependencia de la base de datos
):
    try:
        # Validación personalizada para archivos faltantes
        if not freedom_tradition_certificate or not public_deed:
            missing_files = []
            if not freedom_tradition_certificate:
                missing_files.append("freedom_tradition_certificate")
            if not public_deed:
                missing_files.append("public_deed")

            # Respuesta personalizada si faltan archivos
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "data": {
                        "title": "Archivos requeridos faltantes",
                        "message": f"Faltan los siguientes archivos: {', '.join(missing_files)}"
                    }
                }
            )

        # Creamos una instancia del servicio para manejar la lógica
        property_service = PropertyLotService(db)

        # Llamamos al método para crear el predio
        result = await property_service.create_property(
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

        return result  # El resultado es devuelto como un diccionario

    except HTTPException as e:
        raise e  # Re-lanzamos la excepción si ya se manejó aquí

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
    
@router.get("/{property_id}/lots/")
def list_lots_properties(property_id: int, db: Session = Depends(get_db)):
    """Obtener todos los lotes de un predio"""
    try:
        property_service = PropertyLotService(db)
        lots = property_service.get_lots_property(property_id)
        return lots
        pass
    except HTTPException as e:
        raise e  # Re-raise HTTPException for known errors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los lotes de predios: {str(e)}")
