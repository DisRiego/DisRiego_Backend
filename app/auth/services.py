
from fastapi import HTTPException
from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.users.models import User, RevokedToken
from sqlalchemy.orm import Session , joinedload
from app.roles.models import Role, Permission
from Crypto.Protocol.KDF import scrypt
import os

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class AuthService:
    """Clase para la gestión de autenticación"""

    def __init__(self, db: Session):
        self.db = db

    def create_access_token(self, data: dict, expires_delta: timedelta = None) -> str:
        """
        Crear un token de acceso JWT con una fecha de expiración
        :param data: Información que se incluirá en el payload del JWT
        :param expires_delta: Tiempo de expiración del token
        :return: JWT firmado
        """
        try:
            to_encode = data.copy()
            expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
            to_encode.update({"exp": expire})
            encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
            return encoded_jwt
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al crear el token: {str(e)}")

    # def authenticate_user(self, email: str, password: str) -> User:
    #     """
    #     Autenticar al usuario comparando la contraseña ingresada con la almacenada
    #     :param email: Correo del usuario
    #     :param password: Contraseña proporcionada por el usuario
    #     :return: Usuario autenticado
    #     """
    #     try:
    #         user_service = UserService(self.db)
    #         user = user_service.get_user_by_username(email)
    #         if not user:
    #             raise HTTPException(status_code=404, detail="Usuario no encontrado")

    #         # Verificar la contraseña usando la función verify_password
    #         if not self.verify_password(user.password_salt, user.password, password):
    #             raise HTTPException(status_code=401, detail="Credenciales inválidas")

    #         return user
    #     except Exception as e:
    #         raise HTTPException(status_code=500, detail=f"Error al autenticar al usuario: {str(e)}")

    def revoke_token(self, db: Session, token: str, expires_at: datetime):
        """
        Revocar un token y guardarlo en la base de datos
        :param db: Sesión de la base de datos
        :param token: El token a revocar
        :param expires_at: Fecha de expiración del token
        :return: Mensaje de éxito
        """
        try:
            revoked = RevokedToken(token=token, expires_at=expires_at)
            db.add(revoked)
            db.commit()
            return {"success": True, "data": "Token revocado correctamente"}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al revocar el token: {str(e)}")

    def verify_password(self, stored_salt: str, stored_hash: str, password: str) -> bool:
        """
        Verificar si la contraseña proporcionada coincide con el hash almacenado
        :param stored_salt: El salt almacenado en la base de datos
        :param stored_hash: El hash de la contraseña almacenado en la base de datos
        :param password: La contraseña proporcionada por el usuario
        :return: True si la contraseña es válida, False en caso contrario
        """
        try:
            calculated_hash = self.hash_password(password, stored_salt)
            return calculated_hash == stored_hash
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al verificar la contraseña: {str(e)}")

    def hash_password(self, password: str, salt: str) -> str:
        """
        Generar el hash de la contraseña con salt utilizando el algoritmo scrypt
        :param password: Contraseña proporcionada por el usuario
        :param salt: El salt para el hash
        :return: El hash generado de la contraseña
        """
        try:
            salt_bytes = bytes.fromhex(salt)
            key = scrypt(password.encode(), salt=salt_bytes, key_len=32, N=2**14, r=8, p=1)
            return key.hex()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al generar el hash de la contraseña: {str(e)}")
    
    def get_user_by_username(self, username: str):
        try:
            user = (
                self.db.query(User)
                .options(joinedload(User.roles).joinedload(Role.permissions))
                .filter(User.email == username)
                .first()
            )
            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado.")
            return user
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al obtener el usuario: {str(e)}")

    def hash_password(self, password: str) -> tuple:
        try:
            salt = os.urandom(16)
            key = scrypt(password.encode(), salt, key_len=32, N=2**14, r=8, p=1)
            return salt.hex(), key.hex()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al generar el hash de la contraseña: {str(e)}")

    def verify_password(self, stored_salt: str, stored_hash: str, password: str) -> bool:
        try:
            bytes.fromhex(stored_salt)
        except ValueError:
            raise HTTPException(status_code=400, detail="El salt almacenado no es una cadena hexadecimal válida.")
        
        try:
            salt = bytes.fromhex(stored_salt)
            key = scrypt(password.encode(), salt, key_len=32, N=2**14, r=8, p=1)
            return key.hex() == stored_hash
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al verificar la contraseña: {str(e)}")

    def authenticate_user(self, email: str, password: str):
        try:
            user = self.get_user_by_username(email)
            if not user or not self.verify_password(user.password_salt, user.password, password):
                raise HTTPException(status_code=401, detail="Credenciales inválidas")
            return user
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Error al autenticar al usuario: {str(e)}")

    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        try:
            to_encode = data.copy()
            expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
            to_encode.update({"exp": expire})
            encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
            return encoded_jwt
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al crear el token: {str(e)}")

