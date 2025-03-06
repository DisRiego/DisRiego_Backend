import os
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta



from app.users.models import User, RevokedToken , PasswordReset  # Ahora importamos también RevokedToken
from app.database import Base
from fastapi import HTTPException

from app.users.models import User, PasswordReset,RevokedToken  # Asegúrate de que el modelo User esté correctamente importado
from app.database import Base
from fastapi import HTTPException
import uuid
from passlib.context import CryptContext

from jose import JWTError, jwt
from Crypto.Protocol.KDF import scrypt
import uuid
# Constantes para autenticación
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    """Clase para gestionar la creación, autenticación y actualización de usuarios"""

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_username(self, username: str):
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
            raise HTTPException(status_code=500, detail=f"Error al autenticar al usuario: {str(e)}")

    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        try:
            to_encode = data.copy()
            expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
            to_encode.update({"exp": expire})
            encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
            return encoded_jwt
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al crear el token: {str(e)}")

    def update_user(self, user_id: int, new_address: Optional[str] = None, new_profile_picture: Optional[str] = None, new_phone: Optional[str] = None):
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
        
        # Buscar la solicitud de restablecimiento de contraseña usando el token
        password_reset = self.db.query(PasswordReset).filter(PasswordReset.token == token).first()
        if not password_reset:
            raise HTTPException(status_code=404, detail="Invalid or expired token")
        
        # Verificar que el token no haya expirado
        if password_reset.expiration < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Token expired")
        
        # Buscar el usuario asociado al email en la solicitud de reset
        user = self.db.query(User).filter(User.email == password_reset.email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Generar un nuevo salt y hash para la nueva contraseña utilizando scrypt
        salt, hashed_password = self.hash_password(new_password)
        
        # Actualizar ambos campos: la contraseña y el salt
        user.password = hashed_password
        user.password_salt = salt
        
        # Confirmar los cambios en la base de datos
        self.db.commit()
        
        # Eliminar la solicitud de restablecimiento para que el token no se pueda reutilizar
        self.db.delete(password_reset)
        self.db.commit()

        return {"message": "Password successfully updated"}


            #raise HTTPException(status_code=500, detail=f"Error al actualizar el usuario: {str(e)}")

        raise HTTPException(status_code=500, detail=f"Error al actualizar el usuario: {str(e)}")



# Clase para gestionar la autenticación y cierre de sesión (revocación de tokens)

class AuthService:
    def __init__(self):
        self.secret_key = SECRET_KEY

    def revoke_token(self, db: Session, token: str, expires_at: datetime):
        """Revocar un token (guardar en la base de datos como revocado)"""
        try:
            revoked = RevokedToken(token=token, expires_at=expires_at)
            db.add(revoked)
            db.commit()
            return {"success": True, "data": "Token revocado"}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al revocar el token: {str(e)}")

