from pydantic import BaseModel

# Modelo base para la solicitud de usuario
class UserBase(BaseModel):
    username: str
    password: str  # Incluye password en el modelo de solicitud

# Modelo de respuesta, que incluye el campo `id` (y otros campos que desees)
class UserResponse(UserBase):
    id: int

    class Config:
        orm_mode = True  # Esto permite que SQLAlchemy funcione con Pydantic


class Token(BaseModel):
    access_token: str
    token_type: str
