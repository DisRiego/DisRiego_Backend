from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.users import schemas, services
from datetime import datetime
from jose import jwt, JWTError
from app.users.schemas import ChangePasswordRequest
from app.auth import AuthService
from app.users.services import PasswordChangeService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=list[schemas.UserResponse])
def list_users(db: Session = Depends(get_db)):
    user_service = services.UserService(db)
    
    return []  

@router.post("/login", response_model=schemas.Token)
def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user_service = services.UserService(db)
    user = user_service.authenticate_user(user_credentials.email, user_credentials.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = user_service.create_access_token(data={"sub": str(user.email)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/update", response_model=dict)
def updater(update: schemas.UpdateUserRequest, db: Session = Depends(get_db)):
    update_user_service = services.UserService(db)
    return update_user_service.update_user(
        user_id=update.user_id,
        new_address=update.new_address,
        new_profile_picture=update.new_profile_picture,
        new_phone=update.new_phone
    )


@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    auth_service = services.AuthService()
    try:
        
        payload = jwt.decode(token, auth_service.secret_key, algorithms=["HS256"])
        expires_at = datetime.utcfromtimestamp(payload.get("exp"))
        
        auth_service.revoke_token(db, token, expires_at)
        return {"message": "Cierre de sesión exitoso"}
    except JWTError:
        raise HTTPException(status_code=400, detail="Token inválido")

@router.put("/change", response_model=dict)
@router.put("/change", response_model=dict)
def update_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(lambda: AuthService().get_user),  
    db: Session = Depends(get_db) 
):
    password_service = PasswordChangeService(db, current_user["id"], request.old_password, request.new_password, request.confirm_password)
    response = password_service.change_password()

    if isinstance(response, dict):
        return response  
    else:
        return {"error": "No se pudo actualizar la contraseña"}

