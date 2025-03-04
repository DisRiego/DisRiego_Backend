from fastapi import APIRouter, Depends
from app.services.restore_password import request_password_reset, generate_reset_token, reset_password
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/request-password-reset")
def request_reset_password(email: str, db: Session = Depends(get_db)):
    user = request_password_reset(db, email)
    token = generate_reset_token(user.email, db)
    return {"detail": "Password reset email sent"}, token

@router.post("/reset-password/{token}")
def reset_password_route(token: str, new_password: str, db: Session = Depends(get_db)):
    return reset_password(db, token, new_password)
