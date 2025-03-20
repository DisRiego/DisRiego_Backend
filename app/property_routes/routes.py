from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app.property_routes.services import PropertyLotService
from app.property_routes.schemas import PropertyCreate, PropertyResponse

router = APIRouter(prefix="/properties", tags=["Properties"])

@router.post("/", response_model=dict)
async def create_property(
    user_id: int = Form(...),
    name: str = Form(...),  # Usamos Form para los campos de texto
    longitude: float = Form(...),
    latitude: float = Form(...),
    extension: float = Form(...),
    real_estate_registration_number: int = Form(...),
    freedom_tradition_certificate: UploadFile = File(...),  # Archivos obligatorios
    public_deed: UploadFile = File(...),
    db: Session = Depends(get_db)  # Dependencia de la base de datos
):
    try:
        # Creamos una instancia del servicio para manejar la lógica
        property_service = PropertyLotService(db)
        result = await property_service.create_property(
            user_id=user_id,
            name=name,
            longitude=longitude,
            latitude=latitude,
            extension=extension,
            real_estate_registration_number=real_estate_registration_number,
            public_deed=public_deed,
            freedom_tradition_certificate=freedom_tradition_certificate
        )

        return result  # El resultado es devuelto como un diccionario

    except HTTPException as e:
        raise e  # Re-lanzamos la excepción si ya se manejó aquí

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear el predio: {str(e)}")


@router.post("/lot/", response_model=dict)
async def create_lot(
    property_id: int = Form(...),
    name: str = Form(...),  # Usamos Form para los campos de texto
    longitude: float = Form(...),
    latitude: float = Form(...),
    extension: float = Form(...),
    real_estate_registration_number: int = Form(...),
    freedom_tradition_certificate: UploadFile = File(...),  # Archivos obligatorios
    public_deed: UploadFile = File(...),
    db: Session = Depends(get_db)  # Dependencia de la base de datos
):
    try:
        # Creamos una instancia del servicio para manejar la lógica
        property_service = PropertyLotService(db)
        result = await property_service.create_lot(
            property_id=property_id,
            name=name,
            longitude=longitude,
            latitude=latitude,
            extension=extension,
            real_estate_registration_number=real_estate_registration_number,
            public_deed=public_deed,
            freedom_tradition_certificate=freedom_tradition_certificate
        )

        return result  # El resultado es devuelto como un diccionario

    except HTTPException as e:
        raise e  # Re-lanzamos la excepción si ya se manejó aquí

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear el predio: {str(e)}")

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
    except HTTPException as e:
        raise e  # Re-raise HTTPException for known errors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los lotes de predios: {str(e)}")
    
@router.get("/user/{user_id}")
def list_lots_properties(user_id: int, db: Session = Depends(get_db)):
    """Obtener todos los predios de un usuario"""
    try:
        property_service = PropertyLotService(db)
        properties = property_service.get_properties_for_user(user_id)
        return properties
    except HTTPException as e:
        raise e  # Re-raise HTTPException for known errors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los lotes de predios: {str(e)}")
    
@router.put("/lot/{lot_id}", response_model=dict)
async def update_lot(lot_id: int,
    name: str = Form(...),
    longitude: float = Form(...),
    latitude: float = Form(...),
    extension: float = Form(...),
    real_estate_registration_number: int = Form(...),
    public_deed: UploadFile = File(None), freedom_tradition_certificate: UploadFile = File(None), db: Session = Depends(get_db)):
    property_service = PropertyLotService(db)
    return await property_service.edit_lot(
        lot_id=lot_id,
        name=name,
        longitude = longitude,
        latitude = latitude,
        extension = extension,
        real_estate_registration_number = real_estate_registration_number,
        public_deed=public_deed,
        freedom_tradition_certificate=freedom_tradition_certificate
    )

@router.put("/{property_id}", response_model=dict)
async def update_lot(property_id: int,
    user_id: int = Form(...),
    name: str = Form(...),
    longitude: float = Form(...),
    latitude: float = Form(...),
    extension: float = Form(...),
    real_estate_registration_number: int = Form(...),
    public_deed: UploadFile = File(None), freedom_tradition_certificate: UploadFile = File(None), db: Session = Depends(get_db)):
    property_service = PropertyLotService(db)
    return await property_service.edit_property(
        property_id=property_id,
        user_id=user_id,
        name=name,
        longitude = longitude,
        latitude = latitude,
        extension = extension,
        real_estate_registration_number = real_estate_registration_number,
        public_deed=public_deed,
        freedom_tradition_certificate=freedom_tradition_certificate
    )
