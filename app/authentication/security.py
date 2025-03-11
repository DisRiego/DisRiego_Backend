# Añadir a un archivo de seguridad, por ejemplo, app/authentication/security.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from jose import JWTError, jwt
from app.auth import AuthService
from app.roles.services import RoleService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user_id(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Verificar el token JWT y devolver el ID del usuario actual
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        auth_service = AuthService()
        payload = jwt.decode(token, auth_service.secret_key, algorithms=[auth_service.algorithm])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    return user_id

async def verify_lot_management_permission(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """
    Verificar que el usuario tiene permisos para gestionar lotes
    """
    try:
        # Implementar la verificación de permisos según tu sistema
        role_service = RoleService(db)
        has_permission = role_service.user_has_permission(user_id, "manage_lots")
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para gestionar lotes"
            )
            
        return user_id
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al verificar permisos: {str(e)}"
        )