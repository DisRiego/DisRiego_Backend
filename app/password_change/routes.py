from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import AuthService
from .schemas import ChangePasswordRequest
from .services import change_password
from app.auth import AuthService

router = APIRouter(prefix="/password", tags=["password"])

@router.put("/change")
def update_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthService().get_user)
):
    return change_password(db, current_user.id, request.old_password, request.new_password, request.confirm_password)
