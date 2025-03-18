from pydantic import BaseModel, Field, validator, model_validator
import re
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

class GenderEnum(str, Enum):
    MALE = "Hombre"
    FEMALE = "Mujer"
    OTHER = "Otro"

class AdminUserCreateRequest(BaseModel):
    """
    Esquema para la creación de usuarios por parte del administrador.
    Incluye todos los campos obligatorios del formulario.
    """
    name: str = Field(..., min_length=1, max_length=30, description="Nombres del usuario")
    first_last_name: str = Field(..., min_length=1, max_length=30, description="Primer apellido")
    second_last_name: str = Field(..., min_length=1, max_length=30, description="Segundo apellido")
    type_document_id: int = Field(..., description="ID del tipo de documento")
    document_number: str = Field(..., max_length=30, description="Número de documento")
    date_issuance_document: date = Field(..., description="Fecha de expedición del documento")
    birthday: date = Field(..., description="Fecha de nacimiento")
    gender_id: int = Field(..., description="ID del género (1=Hombre, 2=Mujer, 3=Otro)")
    roles: List[int] = Field(..., description="Lista de IDs de roles asignados al usuario")
    
    @validator('document_number')
    def validate_document_number(cls, v):
        """Validar que el número de documento contenga solo números"""
        if not v.isdigit():
            raise ValueError("El número de documento debe contener solo dígitos")
        return v
    
    @validator('birthday')
    def validate_birthday(cls, v):
        """Validar que la fecha de nacimiento no sea en el futuro"""
        if v > date.today():
            raise ValueError("La fecha de nacimiento no puede ser en el futuro")
        return v
    
    @validator('date_issuance_document')
    def validate_issuance_date(cls, v, values):
        """Validar que la fecha de expedición no sea en el futuro y posterior al nacimiento"""
        if v > date.today():
            raise ValueError("La fecha de expedición no puede ser en el futuro")
        if 'birthday' in values and v < values['birthday']:
            raise ValueError("La fecha de expedición no puede ser anterior a la fecha de nacimiento")
        return v

class AdminUserCreateResponse(BaseModel):
    """Respuesta para la creación de usuario por administrador"""
    success: bool
    message: str
    user_id: Optional[int] = None

# Modelo base para la solicitud de usuario
class UserBase(BaseModel):
    username: str
    password: str  # Incluye password en el modelo de solicitud

# Modelo de respuesta, que incluye el campo `id` (y otros campos que desees)
class UserResponse(UserBase):
    id: int
    email_status: Optional[bool] = None
    type_document_id: Optional[int] = None
    document_number: Optional[int] = None
    date_issuance_document: Optional[datetime] = None
    type_person_id: Optional[int] = None
    birthday: Optional[datetime] = None
    gender_id: Optional[int] = None
    status_id: Optional[int] = None
    name: Optional[str] = None
    first_last_name: Optional[str] = None
    second_last_name: Optional[str] = None
    address: Optional[str] = None
    profile_picture: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    country: Optional[str] = None
    department: Optional[str] = None
    municipality: Optional[int] = None

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

# Actualizado: Modelo para registro de usuario después del primer login
class FirstLoginProfileUpdate(BaseModel):
    user_id: int
    country: str = Field(..., description="Pais de residencia")
    department: str = Field(..., description="Departamento o provincia")
    municipality: int = Field(..., ge=1, le=37, description="Codigo del municipio (1-37)")
    address: str = Field(..., description="Direccion completa")
    phone: str = Field(..., description="Numero de telefono")
    profile_picture: Optional[str] = None

# Existente: Actualización general de usuario
class UpdateUserRequest(BaseModel):
    user_id: int
    new_address: Optional[str] = None
    new_profile_picture: Optional[str] = None
    new_phone: Optional[str] = None
    country: Optional[str] = None
    department: Optional[str] = None
    municipality: Optional[int] = Field(None, ge=1, le=37, description="Codigo del municipio (1-37)")

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
    country: Optional[str] = Field(None, description="País de residencia")
    department: Optional[str] = Field(None, description="Departamento o provincia")
    municipality: Optional[int] = Field(None, ge=1, le=37, description="Código del municipio (1-37)")
    address: Optional[str] = Field(None, description="Dirección completa")
    phone: Optional[str] = Field(None, description="Número de teléfono")
    profile_picture: Optional[str] = None

# Esquema simplificado para la edición de usuario
class UserEditRequest(BaseModel):
    """
    Esquema para la edición de información básica del usuario.
    Restringe los campos que se pueden editar a país, departamento, 
    municipio, dirección y teléfono.
    """
    country: Optional[str] = Field(None, description="País de residencia")
    department: Optional[str] = Field(None, description="Departamento o provincia")
    municipality: Optional[int] = Field(None, ge=1, le=37, description="Codigo del municipio (1-37)")
    address: Optional[str] = Field(None, description="Direccion completa")
    phone: Optional[str] = Field(None, description="Numero de telefono")
    profile_picture: Optional[str] = None


