from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.users.services import UserService
from app.users.schemas import UpdateUserRequest, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db)):
    """
    Obtener todos los usuarios.
    :param db: Dependencia de la base de datos
    :return: Lista de usuarios
    """
    try:
        user_service = UserService(db)
        users = user_service.get_users()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los usuarios: {str(e)}")

@router.post("/update", response_model=dict)
def update_user(update: UpdateUserRequest, db: Session = Depends(get_db)):
    """
    Actualizar los detalles de un usuario.
    :param update: Datos del usuario a actualizar
    :param db: Dependencia de la base de datos
    :return: Mensaje de éxito o error
    """
    try:
        user_service = UserService(db)
        result = user_service.update_user(
            update.user_id,
            update.new_address,
            update.new_profile_picture,
            update.new_phone
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return {"success": True, "message": "Usuario actualizado correctamente"}
    except HTTPException as e:
        raise e  # Re-raise HTTPException for known errors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar el usuario: {str(e)}")
