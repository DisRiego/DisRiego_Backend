from pydantic import BaseModel
from typing import List, Any

# Respuesta simplificada con éxito y datos
class SimpleResponse(BaseModel):
    success: bool
    data: Any  # Aquí se puede incluir el mensaje de éxito o los datos relevantes

class PermissionBase(BaseModel):
    name: str
    description: str
    category: str

class PermissionResponse(PermissionBase):
    id: int
    class Config:
        orm_mode = True

class RoleBase(BaseModel):
    name: str
    description: str

class RoleCreate(RoleBase):
    permissions: List[int] = []

class RoleResponse(RoleBase):
    id: int
    permissions: List[PermissionResponse] = []
    class Config:
        orm_mode = True

class AssignRoleRequest(BaseModel):
    user_id: int
    role_id: int

class UpdateRolePermissions(BaseModel):
    permissions: List[int]  # Lista de IDs de permisos a asignar

class UpdateUserRoles(BaseModel):
    roles: List[int]  # Lista de IDs de los roles que el usuario debe tener
