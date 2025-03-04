from pydantic import BaseModel, Field

# Modelo base para la solicitud de usuario
class UserBase(BaseModel):
    username: str
    password: str  # Incluye password en el modelo de solicitud

# Modelo de respuesta de usuario, que incluye el campo `id`
class UserResponse(UserBase):
    id: int

    class Config:
        orm_mode = True  # Esto permite que SQLAlchemy funcione con Pydantic

# Modelo de Token para autenticación
class Token(BaseModel):
    access_token: str
    token_type: str
