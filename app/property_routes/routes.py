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
    user_id: int = Form(None),  # Usuario opcional que está creando o al que se asigna el predio
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

        property_service = PropertyLotService(db)
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
            user_id=user_id
        )
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear el predio: {str(e)}")


@router.post("/lot/create", response_model=dict)
async def create_lot(name: str, area: float, property_id: int, user_id: int = None,  db: Session = Depends(get_db)):
    try:
        service = PropertyLotService(db)
        return await service.create_lot(name, area, property_id, user_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear el lote: {str(e)}")

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
    except HTTPException as e:
        raise e  # Re-raise HTTPException for known errors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los lotes de predios: {str(e)}")

# Endpoints para notificaciones
@router.post("/notifications/", response_model=dict)
async def create_notification(
    user_id: int,
    title: str,
    message: str,
    notification_type: str,
    db: Session = Depends(get_db)
):
    """Crear una nueva notificación para un usuario"""
    try:
        property_service = PropertyLotService(db)
        result = await property_service.create_notification(user_id, title, message, notification_type)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear la notificación: {str(e)}")

@router.get("/notifications/{user_id}")
def get_notifications(user_id: int, db: Session = Depends(get_db)):
    """Obtener todas las notificaciones de un usuario"""
    try:
        property_service = PropertyLotService(db)
        notifications = property_service.get_user_notifications(user_id)
        return notifications
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener las notificaciones: {str(e)}")

@router.put("/notifications/{notification_id}/read")
def mark_notification_as_read(notification_id: int, db: Session = Depends(get_db)):
    """Marcar una notificación como leída"""
    try:
        property_service = PropertyLotService(db)
        result = property_service.mark_notification_as_read(notification_id)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al marcar la notificación como leída: {str(e)}")

@router.put("/notifications/user/{user_id}/read-all")
def mark_all_notifications_as_read(user_id: int, db: Session = Depends(get_db)):
    """Marcar todas las notificaciones de un usuario como leídas"""
    try:
        property_service = PropertyLotService(db)
        result = property_service.mark_all_notifications_as_read(user_id)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al marcar todas las notificaciones como leídas: {str(e)}")
