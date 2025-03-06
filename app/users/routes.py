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
    user = services.authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = services.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}