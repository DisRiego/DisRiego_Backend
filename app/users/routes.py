from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.users import schemas, services

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=list[schemas.UserResponse])
def list_users(db: Session = Depends(get_db)):
    role_service = services.User(db)
    return role_service.get_roles()
    # return services.get_roles(db)
    
# Ruta para solicitar el restablecimiento de la contraseña
@router.post("/request-reset-password", response_model=schemas.ResetPasswordResponse)
def request_reset_password(
    reset_password_request: schemas.ResetPasswordRequest, 
    db: Session = Depends(get_db)
):
    user_service = services.UserService(db)
    user_service.get_user_by_username(reset_password_request.email)  # Validamos que el email exista
    token = user_service.generate_reset_token(reset_password_request.email)
    return schemas.ResetPasswordResponse(message="Reset link generated", token=token)

# Ruta para actualizar la contraseña
@router.post("/reset-password/{token}", response_model=schemas.ResetPasswordResponse)
def reset_password(
    token: str, 
    update_password_request: schemas.UpdatePasswordRequest, 
    db: Session = Depends(get_db)
):
    user_service = services.UserService(db)
    user_service.update_password(token, update_password_request.new_password)
    return schemas.ResetPasswordResponse(message="Password successfully updated", token=token)