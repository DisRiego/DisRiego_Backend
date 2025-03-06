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

@router.post("/update", response_model=dict)
def updater(
    update: schemas.UpdateUserRequest,  
    db: Session = Depends(get_db)
):
    update_user_service = services.UserService(db)
    return update_user_service.update_user(
        user_id=update.user_id,
        new_address=update.new_address,
        new_profile_picture=update.new_profile_picture,
        new_phone=update.new_phone
    )