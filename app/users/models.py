from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from app.roles.models import Role, user_role_table  # Asegúrate de que estos existan

class User(Base):
    """Modelo de Usuario"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    password = Column(String)
    password_salt = Column(String)
    name = Column(String)
    email_status = Column(Boolean, nullable=True)
    type_document_id = Column(Integer, nullable=True)
    document_number = Column(Integer, nullable=True)
    date_issuance_document = Column(DateTime, nullable=True)
    type_person_id = Column(Integer, nullable=True)
    birthday = Column(DateTime, nullable=True)
    gender_id = Column(Integer, nullable=True)
    status_id = Column(Integer, nullable=True)
    first_last_name = Column(String, nullable=True)
    second_last_name = Column(String, nullable=True)
    address = Column(String, nullable=True)
    profile_picture = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    # Relación con roles
    roles = relationship("Role", secondary=user_role_table, back_populates="users")

    __table_args__ = {'extend_existing': True}  # Evita redefinir la tabla

class RevokedToken(Base):
    """Modelo para almacenar tokens revocados (para cierre de sesión)"""
    __tablename__ = "revoked_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    def has_expired(self):
        return datetime.utcnow() > self.expires_at
