from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from app.users.models import User, PasswordReset  # Asegúrate de que el modelo User esté correctamente importado
from app.database import Base
from fastapi import HTTPException
import uuid
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    """Clase para gestionar la creación y obtención de usuarios"""

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_username(self, username: str):
        """Obtener un usuario por su nombre de usuario (email)"""
        try:
            user = self.db.query(User).filter(User.email == username).first()
            if not user:
                raise HTTPException(status_code=404, detail={
                    "success": False,
                    "data": "Usuario no encontrado."
                })
            return user
        except Exception as e:
            raise HTTPException(status_code=500, detail={
                "success": False,
                "data": f"Error al obtener el usuario: {str(e)}"
            })

    def create_user(
        self, 
        email: str, 
        password: str, 
        name: str, 
        email_status: Optional[bool] = None,
        type_document_id: Optional[int] = None,
        document_number: Optional[int] = None,
        date_issuance_document: Optional[datetime] = None,
        type_person_id: Optional[int] = None,
        birthday: Optional[datetime] = None,
        gender_id: Optional[int] = None,
        status_id: Optional[int] = None,
        first_last_name: Optional[str] = None,
        second_last_name: Optional[str] = None,
        address: Optional[str] = None,
        profile_picture: Optional[str] = None,
        phone: Optional[str] = None
    ):
        """Crear un nuevo usuario con todos los campos"""
        try:
            db_user = User(
                email=email,
                password=password,
                name=name,
                email_status=email_status,
                type_document_id=type_document_id,
                document_number=document_number,
                date_issuance_document=date_issuance_document,
                type_person_id=type_person_id,
                birthday=birthday,
                gender_id=gender_id,
                status_id=status_id,
                first_last_name=first_last_name,
                second_last_name=second_last_name,
                address=address,
                profile_picture=profile_picture,
                phone=phone
            )
            
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            return {
                "success": True,
                "data": "Usuario creado correctamente"
            }
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail={
                "success": False,
                "data": f"Error al crear el usuario: {str(e)}"
            })
    def generate_reset_token(self, email: str):
        """Generar un token para restablecer la contraseña"""
        token = str(uuid.uuid4())  # Genera un token único
        expiration_time = datetime.utcnow() + timedelta(hours=1)  # Token válido por 1 hora
        
        password_reset = PasswordReset(email=email, token=token, expiration=expiration_time)
        self.db.add(password_reset)
        self.db.commit()

        return token

    def update_password(self, token: str, new_password: str):
        """Restablecer la contraseña con el token y la nueva contraseña"""
        # Verificar si el token es válido
        password_reset = self.db.query(PasswordReset).filter(PasswordReset.token == token).first()
        if not password_reset:
            raise HTTPException(status_code=404, detail="Invalid or expired token")
        
        if password_reset.expiration < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Token expired")

        # Obtener al usuario
        user = self.db.query(User).filter(User.email == password_reset.email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Actualizar la contraseña
        hashed_password = pwd_context.hash(new_password)
        user.password = hashed_password
        self.db.commit()

        # Eliminar el token después de usarlo
        self.db.delete(password_reset)
        self.db.commit()

        return {"message": "Password successfully updated"}