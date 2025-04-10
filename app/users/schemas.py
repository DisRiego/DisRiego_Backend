from pydantic import BaseModel, Field, validator, model_validator, EmailStr
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
        if not v.isdigit():
            raise ValueError("El número de documento debe contener solo dígitos")
        return v
    
    @validator('birthday')
    def validate_birthday(cls, v):
        if v > date.today():
            raise ValueError("La fecha de nacimiento no puede ser en el futuro")
        return v
    
    @validator('date_issuance_document')
    def validate_issuance_date(cls, v, values):
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
    password: str

# Modelo de respuesta que incluye el campo `id` y demás datos
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
    city: Optional[int] = None

    class Config:
        from_attributes = True  

# Modelo de token para autenticación
class Token(BaseModel):
    access_token: str
    token_type: str

# Modelo para el login de usuario
class UserLogin(BaseModel):
    email: str
    password: str

# Modelo para registro de usuario después del primer login
class FirstLoginProfileUpdate(BaseModel):
    user_id: int
    country: str = Field(..., description="País de residencia")
    department: str = Field(..., description="Departamento o provincia")
    city: int = Field(..., description="Código del municipio (1-37)")
    address: str = Field(..., description="Dirección completa")
    phone: str = Field(..., description="Número de teléfono")
    profile_picture: Optional[str] = None

# Actualización general de usuario (para autogestión)
class UpdateUserRequest(BaseModel):
    user_id: int
    new_address: Optional[str] = None
    new_profile_picture: Optional[str] = None
    new_phone: Optional[str] = None
    country: Optional[str] = None
    department: Optional[str] = None
    city: Optional[int] = Field(None, ge=1, le=37, description="Código del municipio (1-37)")

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
    city: Optional[int] = Field(None, description="Código del municipio ")
    address: Optional[str] = Field(None, description="Dirección completa")
    phone: Optional[str] = Field(None, description="Número de teléfono")
    profile_picture: Optional[str] = None

# Esquema para edición de perfil básico (usuario normal)
class UserEditRequest(BaseModel):
    """
    Esquema para la edición de información básica del usuario.
    Permite modificar solo país, departamento, municipio, dirección y teléfono.
    """
    country: Optional[str] = Field(None, description="País de residencia")
    department: Optional[str] = Field(None, description="Departamento o provincia")
    city: Optional[int] = Field(None, description="Código del municipio ")
    address: Optional[str] = Field(None, description="Dirección completa")
    phone: Optional[str] = Field(None, description="Número de teléfono")


class PreRegisterValidationRequest(BaseModel):
    """Solicitud para validar documento antes del pre-registro"""
    document_type_id: int = Field(..., description="ID del tipo de documento (1=CC, 2=TI, 3=CE)")
    document_number: str = Field(..., min_length=5, max_length=30, description="Número de documento")
    date_issuance_document: date = Field(..., description="Fecha de expedición del documento")

    @validator('document_number')
    def validate_document_number(cls, v):
        if not v.isdigit():
            raise ValueError("El número de documento debe contener solo dígitos")
        return v

class PreRegisterCompleteRequest(BaseModel):
    """Solicitud para completar el pre-registro con email y contraseña"""
    token: str = Field(..., description="Token de validación")
    email: EmailStr = Field(..., description="Correo electrónico")
    password: str = Field(..., min_length=12, max_length=128, description="Contraseña")
    password_confirmation: str = Field(..., min_length=12, max_length=128, description="Confirmación de contraseña")
    
    @validator('password')
    def validate_password_strength(cls, v):
        if not re.search(r'[a-z]', v):
            raise ValueError("La contraseña debe contener al menos una letra minúscula")
        if not re.search(r'[A-Z]', v):
            raise ValueError("La contraseña debe contener al menos una letra mayúscula")
        if not re.search(r'[0-9]', v):
            raise ValueError("La contraseña debe contener al menos un número")
        return v
    
    @validator('password_confirmation')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError("Las contraseñas no coinciden")
        return v

class PreRegisterResponse(BaseModel):
    """Respuesta para el proceso de pre-registro"""
    success: bool
    message: str
    token: Optional[str] = None

class ActivateAccountRequest(BaseModel):
    """Solicitud para activar la cuenta mediante el enlace enviado por email"""
    activation_token: str

class ActivateAccountResponse(BaseModel):
    """Respuesta para la activación de cuenta"""
    success: bool
    message: str

class AdminUserUpdateRequest(BaseModel):
    """
    Esquema para actualizar la información del usuario por parte del administrador.
    Campos actualizables:
      - Nombre, primer apellido, segundo apellido,
      - Tipo de documento, número de documento, fecha de expedición,
      - Fecha de nacimiento, género y roles asignados.
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
        if not v.isdigit():
            raise ValueError("El número de documento debe contener solo dígitos")
        return v

    @validator('birthday')
    def validate_birthday(cls, v):
        if v > date.today():
            raise ValueError("La fecha de nacimiento no puede ser en el futuro")
        return v

    @validator('date_issuance_document')
    def validate_issuance_date(cls, v, values):
        if v > date.today():
            raise ValueError("La fecha de expedición no puede ser en el futuro")
        if 'birthday' in values and v < values['birthday']:
            raise ValueError("La fecha de expedición no puede ser anterior a la fecha de nacimiento")
        return v

class NotificationBase(BaseModel):
    """Base schema for notification data"""
    title: str
    message: str
    type: str

class NotificationCreate(NotificationBase):
    """Schema for creating a new notification"""
    user_id: int

class NotificationUpdate(BaseModel):
    """Schema for updating a notification"""
    read: Optional[bool] = None

class NotificationResponse(NotificationBase):
    """Schema for notification response"""
    id: int
    user_id: int
    read: Optional[bool] = None
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class NotificationList(BaseModel):
    """Schema for a list of notifications"""
    success: bool
    data: List[NotificationResponse]
    unread_count: int

class MarkReadRequest(BaseModel):
    """Schema for marking notifications as read"""
    notification_ids: Optional[List[int]] = None
    mark_all: bool = False