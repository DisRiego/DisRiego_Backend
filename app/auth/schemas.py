from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# Modelo para el login de usuario
class UserLogin(BaseModel):
    email: str
    password: str

# Modelo de respuesta con el token
class Token(BaseModel):
    access_token: str
    token_type: str

# Esquema para la solicitud de restablecimiento de contraseña
class ResetPasswordRequest(BaseModel):
    email: str

# Esquema para el restablecimiento de contraseña con token
class UpdatePasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=12, description="Nueva contraseña")
    confirm_password: str = Field(..., min_length=12, description="Confirmación de la nueva contraseña")

# Respuesta de restablecimiento de contraseña
class ResetPasswordResponse(BaseModel):
    message: str
    token: Optional[str] = None

# Esquema para la solicitud de cambio de contraseña
class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=12, description="Contraseña actual")
    new_password: str = Field(..., min_length=12, description="Nueva contraseña con mínimo 12 caracteres, incluyendo mayúsculas, minúsculas y números")
    confirm_password: str = Field(..., min_length=12, description="Confirmación de la nueva contraseña")

# Respuesta de cambio de contraseña
class ChangePasswordResponse(BaseModel):
    message: str
