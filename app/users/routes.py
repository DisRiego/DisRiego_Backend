from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.users import schemas
from app.users.models import ChangeUserStatusRequest
from app.users.services import UserService
from app.users.schemas import UpdateUserRequest, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/update", response_model=dict)
async def update_user(update: UpdateUserRequest, db: Session = Depends(get_db)):
   
    try:
        user_service = UserService(db)
        result = await user_service.update_user(
            user_id=update.user_id,
            address=update.new_address,
            profile_picture=update.new_profile_picture,
            phone=update.new_phone
        )
        return result
    except HTTPException as e:
        raise e  # Re-raise HTTPException for known errors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar el usuario: {str(e)}")

@router.get("/{user_id}")
def list_user(user_id: int, db: Session = Depends(get_db)):
    """obtener informacion de un usuario"""
    try:
        user_service = UserService(db)
        return user_service.list_user(user_id)
    except HTTPException as e:
        raise e  # Re-raise HTTPException for known errors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar el usuario: {str(e)}")
    
@router.get("/")
def list_users(db: Session = Depends(get_db)):
    try:
        user_service = UserService(db)
        return user_service.list_users()  # Llamar al método para obtener todos los usuarios
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar los usuarios: {str(e)}")
    
@router.get("/type-document/", tags=['type-document'])
def list_types_document(db: Session = Depends(get_db)):
    try:
        user_service = UserService(db)
        return user_service.get_type_documents()
    except HTTPException as e:
        raise e  # Re-raise HTTPException for known errors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar los tipos de documentos: {str(e)}")
    
@router.post("/change-user-status/")
def change_user_status(request: ChangeUserStatusRequest, db: Session = Depends(get_db)):
    """Cambiar el estado de un usuario"""
    try:
        user_service = UserService(db)
        return user_service.change_user_status(request.user_id, request.new_status)
    except HTTPException as e:
        raise e  # Re-raise HTTPException for known errors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el cambio de estado del usuario: {str(e)}")
