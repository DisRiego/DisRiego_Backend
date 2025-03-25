from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app.property_routes.services import PropertyLotService
from app.property_routes.schemas import PropertyCreate, PropertyResponse
from datetime import datetime


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

        return result  

    except HTTPException as e:
        raise e  

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear el predio: {str(e)}")

@router.post("/user-search/", response_model=dict)
async def search_user_by_document(
    document_type: int = Form(...),
    document_number: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Busca un usuario por tipo y número de documento.
    Retorna: user_id, name, first_lastname y second_lastname.
    """
    try:
        property_service = PropertyLotService(db)
        return property_service.search_user_by_document(
            document_type=document_type,
            document_number=document_number
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la búsqueda: {str(e)}")


@router.post("/lot/", response_model=dict)
async def create_lot(
    property_id: int = Form(...),
    name: str = Form(...),  
    longitude: float = Form(...),
    latitude: float = Form(...),
    extension: float = Form(...),
    real_estate_registration_number: int = Form(...),
    freedom_tradition_certificate: UploadFile = File(...),  
    public_deed: UploadFile = File(...),
    db: Session = Depends(get_db)  
):
    try:
       
        property_service = PropertyLotService(db)
        result = await property_service.create_lot(
            property_id=property_id,
            name=name,
            longitude=longitude,
            latitude=latitude,
            extension=extension,
            real_estate_registration_number=real_estate_registration_number,
            public_deed=public_deed,
            freedom_tradition_certificate=freedom_tradition_certificate,

        )

        return result  

    except HTTPException as e:
        raise e  

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear el predio: {str(e)}")

@router.get("/{property_id}", response_model=dict)
def get_property(property_id: int, db: Session = Depends(get_db)):
    """
    Obtener la información de un predio específico por su ID.
    """
    try:
        property_service = PropertyLotService(db)
        return property_service.get_property_by_id(property_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el predio: {str(e)}")
    
@router.put("/{property_id}/state", response_model=dict)
def update_property_state(
    property_id: int,
    new_state: bool = Form(...),
    db: Session = Depends(get_db)
):
    """
    Cambia el estado del predio.
    new_state: true (activar → state = 16) o false (desactivar → state = 17).
    Si se intenta desactivar y hay lotes asociados activos (state == 18), se rechaza.
    """
    try:
        property_service = PropertyLotService(db)
        updated_property = property_service.update_property_state(property_id, new_state)
        return {
            "success": True,
            "data": {
                "property_id": updated_property.id,
                "state": updated_property.state
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar el estado del predio: {str(e)}")


@router.put("/lot/{lot_id}/state", response_model=dict)
def update_lot_state(
    lot_id: int,
    new_state: bool = Form(...),
    db: Session = Depends(get_db)
):
    """
    Cambia el estado del lote.
    new_state: true (activar → state = 18) o false (desactivar → state = 19).
    Al activar, se valida que el predio asociado esté activo (state == 16).
    """
    try:
        property_service = PropertyLotService(db)
        updated_lot = property_service.update_lot_state(lot_id, new_state)
        return {
            "success": True,
            "data": {
                "lot_id": updated_lot.id,
                "state": updated_lot.state
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar el estado del lote: {str(e)}")



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
        raise e  
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
        raise e  
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




@router.put("/lot/{lot_id}/edit-fields", response_model=dict)
async def update_lot_fields(
    lot_id: int,
    payment_interval: int = Form(...),
    type_crop_id: int = Form(...),
    planting_date: str = Form(...),  # Recibido como 'YYYY-MM-DD'
    estimated_harvest_date: str = Form(...),  # Recibido como 'YYYY-MM-DD'
    db: Session = Depends(get_db)
):
    """
    Endpoint para editar los campos:
    - payment_interval
    - type_crop_id
    - planting_date
    - estimated_harvest_date

    El campo 'state' permanece inalterable.
    """
    try:
        planting_date_obj = datetime.strptime(planting_date, "%Y-%m-%d").date()
        estimated_harvest_date_obj = datetime.strptime(estimated_harvest_date, "%Y-%m-%d").date()
    except Exception as e:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD.")

    property_service = PropertyLotService(db)
    return await property_service.edit_lot_fields(
        lot_id=lot_id,
        payment_interval=payment_interval,
        type_crop_id=type_crop_id,
        planting_date=planting_date_obj,
        estimated_harvest_date=estimated_harvest_date_obj
    )