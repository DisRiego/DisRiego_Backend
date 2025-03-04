# services/restore_password.py
from sqlalchemy.orm import Session
from app import crud
from app.models import User, PasswordReset
from fastapi_mail import FastMail, MessageSchema
from fastapi import HTTPException
import uuid
import datetime
from datetime import timedelta
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Función para recibir la solicitud y validar el correo
def request_password_reset(db: Session, email: str):
    user = crud.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=404, detail="Email not registered")
    return user

# Función para generar un token único para el restablecimiento
def generate_reset_token(user_email: str, db: Session):
    token = str(uuid.uuid4())  # Genera un token único
    #expiration_time = datetime.datetime() + timedelta(hours=1)  # Expiración del token
    # Guardar el token en la base de datos
    #password_reset = PasswordReset(email=user_email, token=token, expiration=expiration_time)
    #db.add(password_reset)
    #db.commit()
    return token



# Función para verificar si el token es válido y no ha expirado
def verify_reset_token(db: Session, token: str):
    password_reset = db.query(PasswordReset).filter(PasswordReset.token == token).first()
    if not password_reset:
        raise HTTPException(status_code=404, detail="Invalid token")
    
    if password_reset.expiration < datetime.datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expired")
    
    return password_reset

# Función para restablecer la contraseña
def reset_password(db: Session, token: str, new_password: str):
    password_reset = verify_reset_token(db, token)
    hashed_password = pwd_context.hash(new_password)  # Encriptar la nueva contraseña
    user = db.query(User).filter(User.email == password_reset.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.password = hashed_password  # Actualizar la contraseña
    db.commit()

    # Eliminar el token de la base de datos para evitar su reutilización
    db.delete(password_reset)
    db.commit()

    return {"detail": "Password successfully updated"}
