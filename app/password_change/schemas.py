from pydantic import BaseModel, Field

# Modelo para solicitud de cambio de contraseña
class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=12, description="Contraseña actual del usuario")
    new_password: str = Field(..., min_length=12, description="Nueva contraseña con mínimo 12 caracteres, incluyendo mayúsculas, minúsculas y números")
    confirm_password: str = Field(..., min_length=12, description="Confirmación de la nueva contraseña")
