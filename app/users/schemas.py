from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Modelo base para la solicitud de usuario
class UserBase(BaseModel):
    username: str
    password: str  # Incluye password en el modelo de solicitud

# Modelo de respuesta, que incluye el campo `id` (y otros campos que desees)
class UserResponse(UserBase):
    id: int
    email_status: Optional[bool] = None  # Boolean para el estado del email
    type_document_id: Optional[int] = None
    document_number: Optional[int] = None
    date_issuance_document: Optional[datetime] = None  # Timestamp para fecha de emisión del documento
    type_person_id: Optional[int] = None
    birthday: Optional[datetime] = None  # Timestamp para fecha de cumpleaños
    gender_id: Optional[int] = None
    status_id: Optional[int] = None
    name: Optional[str] = None
    first_last_name: Optional[str] = None
    second_last_name: Optional[str] = None
    address: Optional[str] = None
    profile_picture: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

    class Config:
        orm_mode = True  # Esto permite que SQLAlchemy funcione con Pydantic

# Modelo de token para la autenticación
class Token(BaseModel):
    access_token: str
    token_type: str

# Esquema para el restablecimiento de contraseña
class ResetPasswordRequest(BaseModel):
    email: str  # El email es lo único necesario para solicitar el restablecimiento

class ResetPasswordResponse(BaseModel):
    message: str
    token: str

class UpdatePasswordRequest(BaseModel):
    token: str
    new_password: str