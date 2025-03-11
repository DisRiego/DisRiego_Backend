from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from pydantic import BaseModel
from app.roles.models import Role, user_role_table  # Asegúrate de que estos existan

class ChangeUserStatusRequest(BaseModel):
    """Modelo para cambiar el estado de un usuario"""
    user_id: int
    new_status: int

class User(Base):
    """Modelo de Usuario"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    password = Column(String)
    password_salt = Column(String)
    name = Column(String)
    email_status = Column(Boolean, nullable=True)
    document_number = Column(Integer, nullable=True)
    date_issuance_document = Column(DateTime, nullable=True)
    type_person_id = Column(Integer, nullable=True)
    birthday = Column(DateTime, nullable=True)
    gender_id = Column(Integer, nullable=True)
    first_last_name = Column(String, nullable=True)
    second_last_name = Column(String, nullable=True)
    address = Column(String, nullable=True)
    profile_picture = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    type_document_id = Column(Integer, ForeignKey('type_document.id'), nullable=True)  # Llave foránea a TypeDocument
    status_id = Column(Integer, ForeignKey('status_user.id'), nullable=True)  # Llave foránea a Status
    gender_id = Column(Integer, ForeignKey('gender.id'), nullable=True)  # Llave foránea a Gender

    # Relación con roles
    roles = relationship("Role", secondary=user_role_table, back_populates="users")
    type_document = relationship("TypeDocument", back_populates="users")
    status_user = relationship("Status", back_populates="users")  # Aquí está la relación corregida
    gender = relationship("Gender", back_populates="users")
    notifications = relationship("Notification", back_populates="user")
    __table_args__ = {'extend_existing': True}  # Evita redefinir la tabla

class RevokedToken(Base):
    """Modelo para almacenar tokens revocados (para cierre de sesión)"""
    __tablename__ = "revoked_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    def has_expired(self):
        return datetime.utcnow() > self.expires_at
    
class TypeDocument(Base):
    """Modelo para el Tipo de Documento"""
    __tablename__ = "type_document"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    # Relación con los usuarios (uno a muchos)
    users = relationship("User", back_populates="type_document")

    __table_args__ = {'extend_existing': True}  # Evita redefinir la tabla

class Gender(Base):
    """Modelo para el Tipo de Documento"""
    __tablename__ = "gender"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    # Relación con los usuarios (uno a muchos)
    users = relationship("User", back_populates="gender")

    __table_args__ = {'extend_existing': True}  # Evita redefinir la tabla

class Status(Base):
    """Modelo para los estados del usuario"""
    __tablename__ = "status_user"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)

    # Relación con los usuarios (uno a muchos)
    users = relationship("User", back_populates="status_user")  # Aquí cambiamos 'status_user' por 'status'

    __table_args__ = {'extend_existing': True}  # Evita redefinir la tabla

