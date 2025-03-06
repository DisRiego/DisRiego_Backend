from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from app.roles.models import Role, user_role_table  # Importamos correctamente los modelos de roles

class User(Base):
    """Modelo de Usuario"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    password_salt = Column(String)
    name = Column(String)
    email_status = Column(Boolean, nullable=True)  # Boolean para el estado del email
    type_document_id = Column(Integer, nullable=True)  # Integer para tipo de documento
    document_number = Column(Integer, nullable=True)  # Integer para número de documento
    date_issuance_document = Column(DateTime, nullable=True)  # Timestamp para fecha de emisión del documento
    type_person_id = Column(Integer, nullable=True)  # Integer para tipo de persona
    birthday = Column(DateTime, nullable=True)  # Timestamp para fecha de cumpleaños
    gender_id = Column(Integer, nullable=True)  # Integer para género
    status_id = Column(Integer, nullable=True)  # Integer para estado
    first_last_name = Column(String, nullable=True)
    second_last_name = Column(String, nullable=True)
    address = Column(String, nullable=True)
    profile_picture = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    # Relación con roles
    roles = relationship("Role", secondary=user_role_table, back_populates="users")

    __table_args__ = {'extend_existing': True}  # Evita redefinir la tabla
