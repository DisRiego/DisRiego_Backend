from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.users import schemas, services

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=list[schemas.UserResponse])
def list_users(db: Session = Depends(get_db)):
    role_service = services.UserService(db)
    return role_service.get_roles()
   

@router.post("/login", response_model=schemas.Token)
def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user_service = services.UserService(db)
    # user_service.generate_salt_and_hash(user_credentials.password)
    user = user_service.authenticate_user(user_credentials.email, user_credentials.password)

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = user_service.create_access_token(data={"sub": str(user.email)})
    return {"access_token": access_token, "token_type": "bearer"}

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
