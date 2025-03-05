from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os

# Contexto de encriptación de contraseñas (usando bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Clave secreta y configuración de JWT
SECRET_KEY = os.getenv("SECRET_KEY", "defaultsecretkey")  # Si no hay .env, usa un valor por defecto
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Expiración del token en minutos

# **Función para hashear contraseñas**
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# **Función para verificar contraseñas**
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# **Función para generar un token de acceso**
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# **Función para validar y decodificar un token JWT**
def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  # Devuelve el contenido del token si es válido
    except JWTError:
        return None  # Devuelve None si el token es inválido o ha expirado
