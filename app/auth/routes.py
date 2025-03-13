from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session , joinedload
from datetime import datetime
from jose import jwt, JWTError
from app.database import get_db
from app.auth.services import AuthService, SECRET_KEY
from app.auth.schemas import ResetPasswordRequest, ResetPasswordResponse, UpdatePasswordRequest
from app.users.schemas import UserLogin, Token
from app.users.services import UserService
from app.roles.models import Role, Permission 
from app.users.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login/", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Inicia sesión y genera un token de acceso con la siguiente información:
    - id, name, email, status_date
    - rol: una lista de roles, cada uno con sus permisos (si existen, de lo contrario una lista vacía)
    """
    auth_service = AuthService(db)
    
    
    user = auth_service.authenticate_user(user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    
    user = (
        db.query(User)
        .options(joinedload(User.roles).joinedload(Role.permissions))
        .filter(User.email == user.email)
        .first()
    )
    
   
    roles = []
    for role in user.roles:
        role_data = {"id": role.id, "name": role.name}
        permisos = [{"id": perm.id, "name": perm.name} for perm in role.permissions]
        role_data["permisos"] = permisos  # Si no hay permisos, será una lista vacía
        roles.append(role_data)
    
   
    token_data = {
        "sub": user.email,   
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "status_date": str(datetime.utcnow()),
        "rol": roles
    }
    
    access_token = auth_service.create_access_token(data=token_data)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Cierra la sesión revocando el token.
    """
    auth_service = AuthService(db)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        expires_at = datetime.utcfromtimestamp(payload.get("exp"))
        auth_service.revoke_token(db, token, expires_at)
        return {"message": "Cierre de sesión exitoso"}
    except JWTError:
        raise HTTPException(status_code=400, detail="Token inválido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al revocar el token: {str(e)}")

@router.post("/request-reset-password", response_model=ResetPasswordResponse)
def request_reset_password(reset_request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Solicita el restablecimiento de contraseña: valida el email, inhabilita tokens previos 
    y genera un token nuevo.
    """
    user_service = UserService(db)
    # Valida que el usuario exista (de lo contrario se lanza error)
    user_service.get_user_by_username(reset_request.email)
    token = user_service.generate_reset_token(reset_request.email)
    return ResetPasswordResponse(message="Enlace de restablecimiento generado", token=token)

@router.post("/reset-password/{token}", response_model=ResetPasswordResponse)
def update_password(token: str, update_request: UpdatePasswordRequest, db: Session = Depends(get_db)):
    """
    Actualiza la contraseña utilizando el token de restablecimiento.
    """
    user_service = UserService(db)
    user_service.update_password(token, update_request.new_password)
    return ResetPasswordResponse(message="Contraseña actualizada correctamente", token=token)
