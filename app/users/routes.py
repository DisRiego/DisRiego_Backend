from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.users import schemas
from app.users.models import ChangeUserStatusRequest
from app.users.services import UserService
from app.users.schemas import UpdateUserRequest, UserResponse, UserCreateRequest , ChangePasswordRequest

router = APIRouter(prefix="/users", tags=["Users"])

# @router.get("/", response_model=list[UserResponse])
# def list_users(db: Session = Depends(get_db)):
#     """
#     Obtener todos los usuarios.
#     :param db: Dependencia de la base de datos
#     :return: Lista de usuarios
#     """
#     try:
#         user_service = UserService(db)
#         users = user_service.get_users()
#         return users
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error al obtener los usuarios: {str(e)}")


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


@router.post("/create-user/")
def create_user(request: UserCreateRequest , db: Session = Depends(get_db)):
    try:
        user_service = UserService(db)
        return user_service.create_user(request)
    except Exception as e:
        raise HTTPException(status_code=500 , detail=f"Error al crear el usuario: {e}")
    
@router.post("/{user_id}/change-password", response_model=dict)
def change_password(user_id: int, request: ChangePasswordRequest, db: Session = Depends(get_db)):
    """
    Actualiza la contraseña del usuario verificando la contraseña actual.
    """
    try:
        user_service = UserService(db)
        return user_service.change_user_password(user_id, request)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al cambiar la contraseña: {str(e)}")