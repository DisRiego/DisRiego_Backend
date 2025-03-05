from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import AuthService
from app.password_change.schemas import ChangePasswordRequest
from app.password_change.services import PasswordChangeService

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.put("/change-password")
def update_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService().get_user)
):
    """Endpoint para permitir a los usuarios cambiar su contraseña"""
    password_service = PasswordChangeService(db)
    return password_service.change_password(
        user_id=current_user.id,
        old_password=request.old_password,
        new_password=request.new_password,
        confirm_password=request.confirm_password
    )
