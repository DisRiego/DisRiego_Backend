import uuid
from datetime import datetime, timedelta
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from app.users.models import Gender, Status, TypeDocument, User, PasswordReset
from Crypto.Protocol.KDF import scrypt
from app.users.schemas import UserCreateRequest , ChangePasswordRequest
from app.roles.models import Role 
import os
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """Clase para gestionar la creación y obtención de usuarios"""

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_username(self, username: str):
        try:
            user = self.db.query(User).filter(User.email == username).first()
            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")
            return user
        except Exception as e:
            raise HTTPException(status_code=500, detail={"success": False, "data": {
                "title" : f"Contacta con el administrador",
                "message" : str(e),
            }})

    def create_user(self, user_data: UserCreateRequest):
        try:
            db_user = User(
                name=user_data.first_name,
                first_last_name=user_data.first_last_name,
                second_last_name=user_data.second_last_name,
                type_document_id=user_data.document_type,
                document_number=user_data.document_number,
                date_issuance_document=user_data.date_issuance_document
                
            )
            
            if user_data.role_id:
                
                roles = self.db.query(Role).filter(Role.id.in_(user_data.role_id)).all()
                db_user.roles = roles

            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)

            return {"success": True, "title":"Éxito","data": "Usuario creado correctamente"}

        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "data": {
                        "title": "Error al crear usuario",
                        "message": str(e),
                    },
                },
            )



    def hash_password(self, password: str) -> tuple:
        """Generar un hash de la contraseña con salt aleatorio"""
        try:
            salt = os.urandom(16)  # Usar un salt aleatorio
            key = scrypt(password.encode(), salt, key_len=32, N=2**14, r=8, p=1)
            return salt.hex(), key.hex()
        except Exception as e:
            raise HTTPException(status_code=500, detail={"success": False, "data": {
                "title" : f"Contacta con el administrador",
                "message" : str(e),
            }})

    def verify_password(self, stored_salt: str, stored_hash: str, password: str) -> bool:
        """Verificar la contraseña ingresada contra el hash almacenado"""
        try:
            salt = bytes.fromhex(stored_salt)  # Convertir el salt de vuelta a bytes
            key = scrypt(password.encode(), salt, key_len=32, N=2**14, r=8, p=1)  # Recalcular el hash
            return key.hex() == stored_hash  # Comparar el hash calculado con el almacenado
        except Exception as e:
            raise HTTPException(status_code=500, detail={"success": False, "data": {
                "title" : f"Contacta con el administrador",
                "message" : str(e),
            }})

    def update_user(self, user_id: int, **kwargs):
        """Actualizar los detalles de un usuario"""
        try:
            db_user = self.db.query(User).filter(User.id == user_id).first()
            if not db_user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")
            for key, value in kwargs.items():
                setattr(db_user, key, value)
            self.db.commit()
            self.db.refresh(db_user)
            return {"success": True, "data": "Usuario actualizado correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail={"success": False, "data": {
                "title" : f"Contacta con el administrador",
                "message" : str(e),
            }})

    def list_user(self, user_id: int):
        """obtener los detalles de un usuario"""
        try:
            # Filtramos los campos que queremos devolver utilizando `with_entities()`
            user = self.db.query(User).join(User.type_document).join(User.status_user).join(User.gender).with_entities(
                User.id,
                User.email,
                User.name,
                User.first_last_name,
                User.second_last_name,
                User.address,
                User.profile_picture,
                User.phone,
                User.date_issuance_document,
                User.type_document_id,
                TypeDocument.name.label("type_document_name"),  # Acceso al campo de la relación TypeDocument
                User.status_id,
                Status.name.label("status_name"),  # Cambié 'status_user' por 'status'
                Status.description.label("status_description"),
                User.gender_id,
                Gender.name.label("gender_name"),
            ).filter(User.id == user_id).first()
            if not user:
                return {
                    "success": False,
                    "data": {
                        "title" : f"Error al obtener el usuario",
                        "message" : "Usuario no encontrado.",
                        }
                    }
            # Convertir el resultado a un diccionario antes de devolverlo
            user_dict = {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "first_last_name": user.first_last_name,
                "second_last_name": user.second_last_name,
                "address": user.address,
                "profile_picture": user.profile_picture,
                "phone": user.phone,
                "date_issuance_document" : user.date_issuance_document, # fecha de expedicion
                "status": user.status_id,
                "status_name": user.status_name,
                "status_description": user.status_description,
                "type_document": user.type_document_id,
                "type_document_name": user.type_document_name,
                "gender": user.gender_id,
                "gender_name": user.gender_name,
            }

            # consulta los roles del usuario
            user = self.db.query(User).filter(User.id == user_id).first()

            # Obtener roles del usuario
            user_roles = [{"id": role.id, "name": role.name} for role in user.roles]

            # Para agregar los roles al diccionario
            user_dict["roles"] = user_roles
            
            return jsonable_encoder({"success": True, "data": [user_dict]})  # Usamos jsonable_encoder

        except Exception as e:
            raise HTTPException(status_code=500, detail={"success": False, "data": {
                "title" : f"Contacta con el administrador",
                "message" : str(e),
            }})
        
    def list_users(self):
    
        try:
            
            users = (
                self.db.query(
                    User.id,
                    User.email,
                    User.name,
                    User.first_last_name,
                    User.second_last_name,
                    User.address,
                    User.profile_picture,
                    User.phone,
                    User.date_issuance_document,
                    User.type_document_id,
                    TypeDocument.name.label("type_document_name"),
                    User.status_id,
                    Status.name.label("status_name"),
                    Status.description.label("status_description"),
                    User.gender_id,
                    Gender.name.label("gender_name"),
                )
                .outerjoin(User.type_document)
                .outerjoin(User.status_user)
                .outerjoin(User.gender)
                .all()
            )

            if not users:
                return {
                    "success": False,
                    "data": {
                        "title": "Error al obtener los usuarios",
                        "message": "No se encontraron usuarios."
                    }
                }

            users_list = []
            for user in users:
                user_dict = {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "first_last_name": user.first_last_name,
                    "second_last_name": user.second_last_name,
                    "address": user.address,
                    "profile_picture": user.profile_picture,
                    "phone": user.phone,
                    "date_issuance_document": user.date_issuance_document,
                    "status": user.status_id,
                    "status_name": user.status_name,
                    "status_description": user.status_description,
                    "type_document": user.type_document_id,
                    "type_document_name": user.type_document_name,
                    "gender": user.gender_id,
                    "gender_name": user.gender_name,
                }

                # Consultamos los roles del usuario, incluso si no tiene roles asignados
                user_obj = self.db.query(User).filter(User.id == user.id).first()
                user_roles = [{"id": role.id, "name": role.name} for role in user_obj.roles] if user_obj.roles else []
                user_dict["roles"] = user_roles

                users_list.append(user_dict)

            return jsonable_encoder({"success": True, "data": users_list})
        except Exception as e:
            raise HTTPException(status_code=500, detail={
                "success": False,
                "data": {
                    "title": "Error de servidor",
                    "message": str(e),
                }
            })



    def change_user_status(self, user_id: int, new_status: int):
        """Cambiar el estado de un usuario"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado.")
            
            # Verifica si el estado proporcionado existe en la tabla StatusUser
            status = self.db.query(Status).filter(Status.id == new_status).first()
            if not status:
                raise HTTPException(status_code=400, detail="Estado no válido.")

            # Cambiar el estado del usuario
            user.status_id = new_status
            self.db.commit()
            self.db.refresh(user)

            return {"success": True, "data": "Estado de usuario actualizado correctamente."}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al actualizar el estado del usuario: {str(e)}")

    def get_type_documents(self):
        """Obtener todos los tipos de documentos"""
        try:
            # Consultar todos los tipos de documentos
            type_documents = self.db.query(TypeDocument).all()

            # Verificar si la consulta devuelve resultados
            if not type_documents:
                raise HTTPException(status_code=404, detail="No se encontraron tipos de documentos.")

            # Convertir los resultados a un formato serializable por JSON
            type_documents_data = jsonable_encoder(type_documents)

            return {
                "success": True,
                "data": type_documents_data
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail={
                "success": False,
                "data": {
                    "title": "Error de servidor",
                    "message": str(e)
                }
            })
        

    def generate_reset_token(self, email: str) -> str:
        """
        Genera un token único para restablecer la contraseña y lo guarda en la BD.
        Si existen tokens previos para el mismo email, se eliminan para inhabilitarlos.
        """
        # Eliminar tokens previos para el mismo email
        previous_tokens = self.db.query(PasswordReset).filter(PasswordReset.email == email).all()
        for token_obj in previous_tokens:
            self.db.delete(token_obj)
        self.db.commit()

        token = str(uuid.uuid4())
        expiration_time = datetime.utcnow() + timedelta(hours=1)  # Token válido por 1 hora
        password_reset = PasswordReset(email=email, token=token, expiration=expiration_time)
        self.db.add(password_reset)
        self.db.commit()
        return token

    def update_password(self, token: str, new_password: str):
        """
        Actualiza la contraseña del usuario utilizando el token de restablecimiento.
        """
        password_reset = self.db.query(PasswordReset).filter(PasswordReset.token == token).first()
        if not password_reset:
            raise HTTPException(status_code=404, detail="Token inválido o expirado")

        if password_reset.expiration < datetime.utcnow():
            raise HTTPException(status_code=400, detail="El token ha expirado")

        user = self.db.query(User).filter(User.email == password_reset.email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Genera un nuevo salt y hash para la nueva contraseña
        new_salt, new_hash = self.hash_password(new_password)
        user.password = new_hash
        user.password_salt = new_salt
        self.db.commit()

        # Eliminar el token usado
        self.db.delete(password_reset)
        self.db.commit()

        return {"message": "Contraseña actualizada correctamente"}

    
    def change_user_password(self, user_id: int, password_data: ChangePasswordRequest):
        """Actualiza la contraseña de un usuario verificando la contraseña actual."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")
            
            # Si no hay un salt configurado
            if user.password_salt is None:
                raise HTTPException(
                    status_code=400, 
                    detail="El usuario no tiene una contraseña configurada. Por favor, utilice la opción de recuperación de contraseña."
                )
            
            # Verifica que la contraseña actual proporcionada coincida con la almacenada usando el método verify_password
            if not self.verify_password(user.password_salt, user.password, password_data.old_password):
                raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")
            
            # Genera un nuevo salt y hash usando el método hash_password
            new_salt, new_hash = self.hash_password(password_data.new_password)
            user.password = new_hash
            user.password_salt = new_salt
            self.db.commit()
            return {"success": True, "data": "Contraseña actualizada correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail={"success": False, "data": {
                "title": "Error al actualizar la contraseña",
                "message": str(e)
            }})

    