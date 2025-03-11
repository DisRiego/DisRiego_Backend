from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.authentication.services import AuthService
from app.users.schemas import UserLogin, Token
from app.authentication.schemas import ResetPasswordRequest
from app.users.services import UserService
from datetime import datetime
from jose import jwt, JWTError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login/", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Ruta para iniciar sesión de un usuario, generando un token de acceso
    :param user_credentials: Credenciales del usuario para el login
    :param db: Dependencia de la base de datos
    :return: Token de acceso
    """
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = auth_service.create_access_token(data={"sub": str(user.email)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Ruta para cerrar sesión y revocar el token
    :param token: Token de autenticación del usuario
    :param db: Dependencia de la base de datos
    :return: Mensaje confirmando el cierre de sesión
    """
    auth_service = AuthService(db)
    try:
        # Verificar y decodificar el token JWT
        payload = jwt.decode(token, 'asdasdasd', algorithms=["HS256"])
        expires_at = datetime.utcfromtimestamp(payload.get("exp"))
        
        # Revocar el token
        auth_service.revoke_token(db, token, expires_at)
        return {"message": "Cierre de sesión exitoso"}
    except JWTError:
        raise HTTPException(status_code=400, detail="Token inválido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al revocar el token: {str(e)}")

@router.post("/reset-password", response_model=Token)
def reset_password(reset_request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Ruta para solicitar un restablecimiento de contraseña mediante un token
    :param reset_request: Datos necesarios para restablecer la contraseña
    :param db: Dependencia de la base de datos
    :return: Token para restablecer la contraseña
    """
    try:
        user_service = UserService(db)
        user = user_service.get_user_by_username(reset_request.email)
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        token = user_service.generate_reset_token(reset_request.email)
        return {"message": "Password reset successfully", "token": token}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al restablecer la contraseña: {str(e)}")
