from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from app.users.models import User  
from app.database import Base
from fastapi import HTTPException
from jose import JWTError, jwt
import bcrypt

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

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
                password=hash_password(password),  # Guarda la contraseña hasheada
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

    def get_user_by_email(db: Session, email: str):
        return db.query(User).filter(User.email == email).first()

    def verify_password(plain_password, hashed_password):
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    def authenticate_user(db: Session, email: str, password: str):
        user = UserService.get_user_by_email(db, email)
        if not user or not UserService.verify_password(password, user.password):
            return None
        return user

    def create_access_token(data: dict, expires_delta: timedelta = None):
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
        
    def update_user(self, user_id, new_address:Optional[str] , new_profile_picture:Optional[str] , new_phone:Optional[str]):
        try:
            db_user = self.db.query(User).filter(User.id == user_id).first()
            if not db_user:
                raise HTTPException(status_code=404, detail={
                     "success": False,
                     "data": "Usuario no encontrando"
                })
                
            if new_address is not None:
                db_user.address = new_address
            if new_profile_picture is not None:
                db_user.profile_picture=new_profile_picture
            if new_phone is not None:
                db_user.phone = new_phone               
                
            self.db.commit()

            self.db.refresh(db_user)
            return{
                "success":True,
                "data": "Usuario Actualizado correctamente"
            }
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail={
                "success": False,
                "data": f"Error al actualizar el usuario: {str(e)}"
            })
