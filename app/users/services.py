import os
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from app.users.models import User  
from app.database import Base
from fastapi import HTTPException
from jose import JWTError, jwt
from passlib.context import CryptContext
from Crypto.Protocol.KDF import scrypt

# Constantes de configuración para la autenticación y hash de contraseñas
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Contexto para la creación de hashes de contraseñas
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
                raise HTTPException(status_code=404, detail="Usuario no encontrado.")
            return user
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al obtener el usuario: {str(e)}")

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
            salt, hashed_password = self.hash_password(password)

            db_user = User(
                email=email,
                password=hashed_password,
                password_salt=salt,
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
            return {"success": True, "data": "Usuario creado correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al crear el usuario: {str(e)}")

    def hash_password(self, password: str) -> str:
        """Generar un hash de la contraseña con salt aleatorio"""
        try:
            salt = os.urandom(16)  # Usar un salt aleatorio
            key = scrypt(password.encode(), salt, key_len=32, N=2**14, r=8, p=1)
            return salt.hex(), key.hex()  # Devolvemos tanto el salt como el hash
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al generar el hash de la contraseña: {str(e)}")

    def verify_password(self, stored_salt: str, stored_hash: str, password: str) -> bool:
        """Verificar la contraseña ingresada contra el hash almacenado"""
        try:
            # Validar que el salt sea una cadena hexadecimal válida
            bytes.fromhex(stored_salt)  # Intentar convertir el salt
        except ValueError:
            raise HTTPException(status_code=400, detail="El salt almacenado no es una cadena hexadecimal válida.")
        
        try:
            salt = bytes.fromhex(stored_salt)  # Convertir el salt de vuelta a bytes
            key = scrypt(password.encode(), salt, key_len=32, N=2**14, r=8, p=1)  # Recalcular el hash
            return key.hex() == stored_hash  # Comparar el hash calculado con el almacenado
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al verificar la contraseña: {str(e)}")

    def authenticate_user(self, email: str, password: str):
        """Autenticar al usuario comparando la contraseña ingresada con la almacenada"""
        try:
            user = self.get_user_by_username(email)
            if not user or not self.verify_password(user.password_salt, user.password, password):
                raise HTTPException(status_code=401, detail="Credenciales inválidas")
            return user
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al autenticar al usuario: {str(e)}")

    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        """Crear un token de acceso JWT"""
        try:
            to_encode = data.copy()
            expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
            to_encode.update({"exp": expire})
            encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
            return encoded_jwt
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al crear el token: {str(e)}")

    def update_user(self, user_id: int, new_address: Optional[str] = None, new_profile_picture: Optional[str] = None, new_phone: Optional[str] = None):
        """Actualizar la información de un usuario"""
        try:
            db_user = self.db.query(User).filter(User.id == user_id).first()
            if not db_user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")
                
            if new_address is not None:
                db_user.address = new_address
            if new_profile_picture is not None:
                db_user.profile_picture = new_profile_picture
            if new_phone is not None:
                db_user.phone = new_phone

            self.db.commit()
            self.db.refresh(db_user)
            return {"success": True, "data": "Usuario actualizado correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al actualizar el usuario: {str(e)}")
    
    # def generate_salt_and_hash(self, password: str):
    #     """Generar un salt y un hash para una contraseña"""
    #     # Generar un salt aleatorio
    #     salt = os.urandom(16)  # 16 bytes de salt aleatorio
        
    #     # Generar el hash de la contraseña utilizando scrypt
    #     key = scrypt(password.encode(), salt, key_len=32, N=2**14, r=8, p=1)
        
    #     # Imprimir el salt (en formato hexadecimal) y el hash generado
    #     print("Salt:", salt.hex())  # Imprimir salt en formato hexadecimal
    #     print("Hash:", key.hex())  # Imprimir hash en formato hexadecimal
