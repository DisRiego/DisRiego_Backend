from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException
from app.roles import models, schemas
from app.models import User

class PermissionService:
    """Clase para gestionar los permisos"""

    def __init__(self, db: Session):
        self.db = db

    def create_permission(self, permission: schemas.PermissionBase):
        """Crear un permiso con manejo de errores"""
        try:
            db_permission = self.db.query(models.Permission).filter(models.Permission.name == permission.name).first()
            if db_permission:
                raise HTTPException(status_code=400, detail={
                    "success": False,
                    "data": "El permiso ya existe asignado a ese nombre"
                })

            db_permission = models.Permission(
                name=permission.name, 
                description=permission.description, 
                category=permission.category
            )
            self.db.add(db_permission)
            self.db.commit()
            self.db.refresh(db_permission)
            return {
                "detail": {
                    "success": True,
                    "data": "El permiso se ha creado correctamente"
                }
            }
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=400, detail={"success": False, "data": "El permiso ya existe."})
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(status_code=500, detail={"success": False, "data": "Error interno al crear el permiso."})

    def get_permissions(self):
        """Obtener todos los permisos con manejo de errores"""
        try:
            return self.db.query(models.Permission).all()
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail={"success": False, "data": "Error al obtener los permisos."})


class RoleService:
    """Clase para gestionar los roles"""

    def __init__(self, db: Session):
        self.db = db

    def create_role(self, role_data: schemas.RoleCreate):
        """Crear un rol con manejo de errores"""
        try:
            db_role = self.db.query(models.Role).filter(models.Role.name == role_data.name).first()
            if db_role:
                raise HTTPException(status_code=400, detail={"success": False, "data": "El rol ya existe."})

            permissions = self.db.query(models.Permission).filter(models.Permission.id.in_(role_data.permissions)).all()
            found_permission_ids = {perm.id for perm in permissions}
            missing_permissions = set(role_data.permissions) - found_permission_ids

            if missing_permissions:
                raise HTTPException(status_code=400, detail={
                    "success": False,
                    "data": f"Los siguientes permisos no existen: {list(missing_permissions)}"
                })

            db_role = models.Role(name=role_data.name, description=role_data.description)
            db_role.permissions = permissions
            self.db.add(db_role)
            self.db.commit()
            self.db.refresh(db_role)

            return {"detail": {"success": True, "data": "El rol se ha creado correctamente"}}
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="El rol ya existe.")
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Error al crear el rol.")

    def get_roles(self):
        """Obtener todos los roles con manejo de errores"""
        try:
            roles = self.db.query(models.Role).all()
            for role in roles:
                if not hasattr(role, "permissions") or role.permissions is None:
                    role.permissions = []
            return roles
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail={"success": False, "data": "Error al obtener los roles."})

    def update_role_permissions(self, role_id: int, permission_ids: list[int]):
        """Actualizar permisos de un rol"""
        try:
            role = self.db.query(models.Role).filter(models.Role.id == role_id).first()
            if not role:
                raise HTTPException(status_code=404, detail={"success": False, "data": "Rol no encontrado."})

            permissions = self.db.query(models.Permission).filter(models.Permission.id.in_(permission_ids)).all()
            found_permission_ids = {perm.id for perm in permissions}
            missing_permissions = set(permission_ids) - found_permission_ids

            if missing_permissions:
                raise HTTPException(status_code=400, detail={
                    "success": False,
                    "data": f"Los siguientes permisos no existen: {list(missing_permissions)}"
                })

            role.permissions = permissions
            self.db.commit()
            self.db.refresh(role)

            return {
                "success": True,
                "message": "Permisos actualizados correctamente",
                "data": {
                    "role_id": role.id,
                    "permissions": [{"id": p.id, "name": p.name} for p in role.permissions]
                }
            }
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(status_code=500, detail={"success": False, "data": "Error al actualizar permisos."})


class UserRoleService:
    """Clase para gestionar la asignación de roles a usuarios"""

    def __init__(self, db: Session):
        self.db = db

    def assign_role_to_user(self, user_id: int, role_id: int):
        """Asignar un rol a un usuario con validaciones"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail={"success": False, "data": "Usuario no encontrado."})

            role = self.db.query(models.Role).filter(models.Role.id == role_id).first()
            if not role:
                raise HTTPException(status_code=404, detail={"success": False, "data": "Rol no encontrado."})

            if role in user.roles:
                raise HTTPException(status_code=400, detail={"success": False, "data": "El usuario ya tiene este rol asignado."})

            user.roles.append(role)
            self.db.commit()
            self.db.refresh(user)
            return {"success": True, "data": "Rol asignado correctamente"}
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(status_code=500, detail={"success": False, "data": "Error al asignar el rol al usuario."})
    
    def revoke_role_from_user(self, user_id: int, role_id: int):
      """Revocar un rol de un usuario, asegurando que al menos tenga 1 rol asignado"""
      try:
          user = self.db.query(User).filter(User.id == user_id).first()
          if not user:
              raise HTTPException(status_code=404, detail={"success": False, "data": "Usuario no encontrado."})

          role = self.db.query(models.Role).filter(models.Role.id == role_id).first()
          if not role:
              raise HTTPException(status_code=404, detail={"success": False, "data": "Rol no encontrado."})

          if role not in user.roles:
              raise HTTPException(status_code=400, detail={"success": False, "data": "El usuario no tiene este rol asignado."})

          if len(user.roles) == 1:
              raise HTTPException(status_code=400, detail={"success": False, "data": "El usuario debe tener al menos un rol asignado."})

          user.roles.remove(role)
          self.db.commit()
          self.db.refresh(user)

          return {"success": True, "data": "Rol revocado correctamente"}
      except SQLAlchemyError:
          self.db.rollback()
          raise HTTPException(status_code=500, detail={"success": False, "data": "Error al revocar el rol del usuario."})
      
    def update_user_roles(self, user_id: int, new_role_ids: list[int]):
      """Actualizar los roles de un usuario asegurando que al menos tenga 1 rol"""
      try:
          user = self.db.query(User).filter(User.id == user_id).first()
          if not user:
              raise HTTPException(status_code=404, detail={"success": False, "data": "Usuario no encontrado."})

          # Obtener los roles existentes en la BD
          roles = self.db.query(models.Role).filter(models.Role.id.in_(new_role_ids)).all()

          # Validar que existen todos los roles enviados
          found_role_ids = {role.id for role in roles}
          missing_roles = set(new_role_ids) - found_role_ids

          if missing_roles:
              raise HTTPException(status_code=400, detail={
                  "success": False,
                  "data": f"Los siguientes roles no existen: {list(missing_roles)}"
              })

          # Validar que el usuario tenga al menos 1 rol
          if len(roles) < 1:
              raise HTTPException(status_code=400, detail={
                  "success": False,
                  "data": "El usuario debe tener al menos un rol asignado."
              })

          # Asignar los nuevos roles
          user.roles = roles
          self.db.commit()
          self.db.refresh(user)

          return {
              "success": True,
              "message": "Roles actualizados correctamente",
              "data": {
                  "user_id": user.id,
                  "roles": [{"id": r.id, "name": r.name} for r in user.roles]
              }
          }
      except SQLAlchemyError:
          self.db.rollback()
          raise HTTPException(status_code=500, detail={"success": False, "data": "Error al actualizar los roles del usuario."})

    def get_user_with_roles(self, user_id: int):
      """Obtener la información de un usuario y sus roles asignados"""
      try:
          user = self.db.query(User).filter(User.id == user_id).first()
          if not user:
              raise HTTPException(status_code=404, detail={"success": False, "data": "Usuario no encontrado."})

          # Obtener roles del usuario
          user_roles = [{"id": role.id, "name": role.name} for role in user.roles]

          return {
              "success": True,
              "data": {
                  "id": user.id,
                  "email": user.email,
                  "name": user.name,
                  "roles": user_roles
              }
          }
      except SQLAlchemyError:
          raise HTTPException(status_code=500, detail={"success": False, "data": "Error al obtener la información del usuario."})
