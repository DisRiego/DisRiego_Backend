from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base
from app.roles.models import Role, user_role_table  # Importamos los modelos de roles correctamente

class User(Base):
    """Modelo de Usuario"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    name = Column(String)

    # Relación con roles
    roles = relationship("Role", secondary=user_role_table, back_populates="users")

    __table_args__ = {'extend_existing': True}  # Evita redefinir la tabla


class Token(BaseModel):
    access_token: str
    token_type: str