from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database import Base

# Tabla intermedia para la relación User - Role (Muchos a Muchos)
user_role_table = Table(
    "user_rol",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("rol_id", Integer, ForeignKey("rol.id"), primary_key=True),
    extend_existing=True
)

# Tabla intermedia para la relación Role - Permission (Muchos a Muchos)
role_permission_table = Table(
    "rol_permission",
    Base.metadata,
    Column("rol_id", Integer, ForeignKey("rol.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permission.id"), primary_key=True),
    extend_existing=True
)

class Role(Base):
    """Modelo para los roles"""
    __tablename__ = "rol"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, index=True)

    permissions = relationship("Permission", secondary=role_permission_table, back_populates="roles")
    users = relationship("User", secondary=user_role_table, back_populates="roles")

    __table_args__ = {'extend_existing': True}

class Permission(Base):
    """Modelo para los permisos"""
    __tablename__ = "permission"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, index=True)
    category = Column(String, index=True)

    roles = relationship("Role", secondary=role_permission_table, back_populates="permissions")

    __table_args__ = {'extend_existing': True}
