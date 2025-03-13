from pydantic import BaseModel, Field , model_validator , validator
import re
from typing import Optional , List
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
        from_attributes = True  

# Modelo de token para la autenticación
class Token(BaseModel):
    access_token: str
    token_type: str

# Modelo para el login de usuario
class UserLogin(BaseModel):
    email: str
    password: str

class UpdateUserRequest(BaseModel):
    user_id: int
    new_address: Optional[str] = None
    new_profile_picture: Optional[str] = None
    new_phone: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=12, description="Contraseña actual del usuario")
    new_password: str = Field(
        ...,
        min_length=12,
        description="Nueva contraseña con mínimo 12 caracteres, incluyendo mayúsculas, minúsculas y números"
    )
    confirm_password: str = Field(..., min_length=12, description="Confirmación de la nueva contraseña")

    @validator('new_password')
    def validate_new_password(cls, value):
        if len(value) < 12:
            raise ValueError("La contraseña debe tener al menos 12 caracteres")
        if not re.search(r'[0-9]', value):
            raise ValueError("La contraseña debe incluir al menos un número")
        if not re.search(r'[A-Z]', value):
            raise ValueError("La contraseña debe incluir al menos una letra mayúscula")
        if not re.search(r'[a-z]', value):
            raise ValueError("La contraseña debe incluir al menos una letra minúscula")
        return value

    @model_validator(mode="after")
    def check_passwords_match(cls, values):
        if values.new_password != values.confirm_password:
            raise ValueError("La nueva contraseña y la confirmación no coinciden")
        return values

class UserCreateRequest(BaseModel):
    first_name: str
    first_last_name: str
    second_last_name: Optional[str] = None
    document_type: int
    document_number: int
    date_issuance_document: datetime
    role_id: Optional[List[int]] = None

class UserUpdateInfo(BaseModel):
    name: str
    first_last_name: str
    second_last_name: str
    type_document_id: int
    document_number: int
    date_issuance_document: datetime
    email: str

