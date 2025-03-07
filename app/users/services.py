from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.users.models import User
from Crypto.Protocol.KDF import scrypt
import os

class UserService:
    """Clase para gestionar la creación, autenticación y actualización de usuarios"""

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

    def create_user(self, email: str, password: str, name: str, **kwargs):
        """Crear un nuevo usuario con todos los campos"""
        try:
            salt, hashed_password = self.hash_password(password)
            db_user = User(
                email=email,
                password=hashed_password,
                password_salt=salt,
                name=name,
                **kwargs
            )
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            return {"success": True, "data": "Usuario creado correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al crear el usuario: {str(e)}")

    def hash_password(self, password: str) -> tuple:
        """Generar un hash de la contraseña con salt aleatorio"""
        try:
            salt = os.urandom(16)  # Usar un salt aleatorio
            key = scrypt(password.encode(), salt, key_len=32, N=2**14, r=8, p=1)
            return salt.hex(), key.hex()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al generar el hash de la contraseña: {str(e)}")

    def verify_password(self, stored_salt: str, stored_hash: str, password: str) -> bool:
        """Verificar la contraseña ingresada contra el hash almacenado"""
        try:
            salt = bytes.fromhex(stored_salt)  # Convertir el salt de vuelta a bytes
            key = scrypt(password.encode(), salt, key_len=32, N=2**14, r=8, p=1)  # Recalcular el hash
            return key.hex() == stored_hash  # Comparar el hash calculado con el almacenado
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al verificar la contraseña: {str(e)}")

    def update_user(self, user_id: int, **kwargs):
        """Actualizar los detalles de un usuario"""
        try:
            db_user = self.db.query(User).filter(User.id == user_id).first()
            if not db_user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")
            for key, value in kwargs.items():
                setattr(db_user, key, value)
            self.db.commit()
            self.db.refresh(db_user)
            return {"success": True, "data": "Usuario actualizado correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al actualizar el usuario: {str(e)}")
