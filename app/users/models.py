from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from pydantic import BaseModel
from app.roles.models import Role, user_role_table

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
    # Nuevos campos para registro de usuario
    country = Column(Integer, nullable=True)
    department = Column(Integer, nullable=True)
    municipality = Column(Integer, nullable=True)
    first_login_complete = Column(Boolean, default=False)  # Indica si el usuario completo su primer registro
    type_document_id = Column(Integer, ForeignKey('type_document.id'), nullable=True)  
    status_id = Column(Integer, ForeignKey('status_user.id'), nullable=True)  
    gender_id = Column(Integer, ForeignKey('gender.id'), nullable=True)  

    # Relación con roles
    roles = relationship("Role", secondary=user_role_table, back_populates="users")
    type_document = relationship("TypeDocument", back_populates="users")
    status_user = relationship("Status", back_populates="users")  
    gender = relationship("Gender", back_populates="users")

    __table_args__ = {'extend_existing': True}  

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

    __table_args__ = {'extend_existing': True}  

class Gender(Base):
    """Modelo para género"""
    __tablename__ = "gender"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    
    # Relación con los usuarios (uno a muchos)
    users = relationship("User", back_populates="gender")

    __table_args__ = {'extend_existing': True}
    
    def __repr__(self):
        return f"<Gender(id={self.id}, name={self.name})>"

# Agregar estos datos a la base de datos si no existen
def ensure_default_genders(db):
    """
    Asegura que existen los géneros predeterminados en la base de datos.
    Esta función debe llamarse al inicio de la aplicación.
    """
    default_genders = [
        {"id": 1, "name": "Hombre"},
        {"id": 2, "name": "Mujer"},
        {"id": 3, "name": "Otro"}
    ]
    
    for gender_data in default_genders:
        gender = db.query(Gender).filter(Gender.id == gender_data["id"]).first()
        if not gender:
            gender = Gender(**gender_data)
            db.add(gender)
    
    db.commit()

class Status(Base):
    """Modelo para los estados del usuario"""
    __tablename__ = "status_user"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)

    # Relación con los usuarios (uno a muchos)
    users = relationship("User", back_populates="status_user")  

    __table_args__ = {'extend_existing': True}  # Evita redefinir la tabla

class PasswordReset(Base):
    __tablename__ = "password_resets"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    token = Column(String, unique=True, index=True)
    expiration = Column(DateTime, default=datetime.utcnow)

