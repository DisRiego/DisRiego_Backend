from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.roles import schemas, services

router = APIRouter(prefix="/roles", tags=["Roles"])

@router.post("/", response_model=schemas.RoleResponse)
def create_role(role: schemas.RoleCreate, db: Session = Depends(get_db)):
    role_service = services.RoleService(db)
    return role_service.create_role(role)
    # return services.create_role(db, role)

@router.get("/", response_model=list[schemas.RoleResponse])
def list_roles(db: Session = Depends(get_db)):
    role_service = services.RoleService(db)
    return role_service.get_roles()
    # return services.get_roles(db)

@router.post("/permissions/", response_model=schemas.PermissionResponse)
def create_permission(permission: schemas.PermissionBase, db: Session = Depends(get_db)):
    permission_service = services.PermissionService(db)
    return permission_service.create_permission(permission)
    # return services.create_permission(db, permission)

@router.get("/permissions/", response_model=list[schemas.PermissionResponse])
def list_permissions(db: Session = Depends(get_db)):
    permission_service = services.PermissionService(db)
    return permission_service.get_permissions()
    # return services.get_permissions(db)

@router.put("/{role_id}/permissions", tags=["Roles"])
def update_permissions(
    role_id: int, 
    request: schemas.UpdateRolePermissions, 
    db: Session = Depends(get_db)
):
    """Actualizar los permisos de un rol."""
    role_service = services.RoleService(db)
    return role_service.update_role_permissions(role_id, request.permissions)
    # return services.update_role_permissions(db, role_id, request.permissions)

@router.post("/assign_role/")
def assign_role(
    request: schemas.AssignRoleRequest,
    db: Session = Depends(get_db)
):
    user_role_service = services.UserRoleService(db)
    return user_role_service.assign_role_to_user(request.user_id, request.role_id)
    # user = services.assign_role_to_user(db, request.user_id, request.role_id)

@router.get("/user/{user_id}/roles", tags=["Usuarios"])
def get_user_roles(user_id: int, db: Session = Depends(get_db)):
    """Obtener la información de un usuario y sus roles asignados"""
    user_role_service = services.UserRoleService(db)
    return user_role_service.get_user_with_roles(user_id)

@router.put("/user/{user_id}/roles", tags=["Usuarios"])
def update_user_roles(user_id: int, request: schemas.UpdateUserRoles, db: Session = Depends(get_db)):
    """Actualizar los roles de un usuario, asegurando que tenga al menos 1"""
    user_role_service = services.UserRoleService(db)
    return user_role_service.update_user_roles(user_id, request.roles)

@router.delete("/user/{user_id}/role/{role_id}", tags=["Usuarios"])
def revoke_role(user_id: int, role_id: int, db: Session = Depends(get_db)):
    """Revocar un rol de un usuario, asegurando que tenga al menos 1 rol"""
    user_role_service = services.UserRoleService(db)
    return user_role_service.revoke_role_from_user(user_id, role_id)

