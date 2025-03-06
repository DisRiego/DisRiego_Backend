from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.auth_service import AuthService  # Importa el servicio de autenticación
from datetime import datetime
from jose import jwt, JWTError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
router = APIRouter(prefix="/auth", tags=["Auth"])

auth_service = AuthService()

@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Cierra sesión invalidando el token"""
    try:
        payload = jwt.decode(token, auth_service.secret_key, algorithms=["HS256"])
        expires_at = datetime.utcfromtimestamp(payload.get("exp"))

        # Guardar token revocado en la base de datos
        auth_service.revoke_token(db, token, expires_at)

        return {"message": "Cierre de sesión exitoso"}
    except JWTError:
        raise HTTPException(status_code=400, detail="Token inválido")
