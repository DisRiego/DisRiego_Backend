from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from app.users.models import Gender, Status, TypeDocument, User
from Crypto.Protocol.KDF import scrypt
import os

class UserService:
    """Clase para gestionar la creación, autenticación y actualización de usuarios"""

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_username(self, username: str):
        """Obtener un usuario por su nombre de usuario (email)"""
        try:
            user = self.db.query(User).filter(User.email == username).first()
            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado.")
            return user
        except Exception as e:
            raise HTTPException(status_code=500, detail={"success": False, "data": {
                "title" : f"Contacta con el administrador",
                "message" : str(e),
            }})

    def create_user(self, email: str, password: str, name: str, **kwargs):
        """Crear un nuevo usuario con todos los campos"""
        try:
            salt, hashed_password = self.hash_password(password)
            db_user = User(
                email=email,
                password=hashed_password,
                password_salt=salt,
                name=name,
                **kwargs
            )
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            return {"success": True, "data": "Usuario creado correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail={"success": False, "data": {
                "title" : f"Contacta con el administrador",
                "message" : str(e),
            }})

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

    async def update_user(self, user_id: int, **kwargs):
        """Actualizar los detalles de un usuario y generar una notificación automática"""
        try:
            db_user = self.db.query(User).filter(User.id == user_id).first()
            if not db_user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")
            
            # Guardar los campos que se van a actualizar para la notificación
            updated_fields = []
            
            for key, value in kwargs.items():
                if value is not None and hasattr(db_user, key):
                    old_value = getattr(db_user, key)
                    if old_value != value:  # Solo registrar si el valor cambió
                        updated_fields.append(key)
                        setattr(db_user, key, value)
            
            # Solo guardar cambios y generar notificación si hubo actualizaciones
            if updated_fields:
                self.db.commit()
                self.db.refresh(db_user)
                
                # Generar mensaje para la notificación
                if len(updated_fields) == 1:
                    message = f"Se ha actualizado el campo: {self._get_field_display_name(updated_fields[0])}"
                else:
                    field_names = [self._get_field_display_name(field) for field in updated_fields]
                    message = f"Se han actualizado los siguientes campos: {', '.join(field_names)}"
                
                # Crear notificación automática
                await self._create_profile_update_notification(user_id, message)
                
                return {"success": True, "data": "Usuario actualizado correctamente", "updated_fields": updated_fields}
            else:
                return {"success": True, "data": "No se realizaron cambios en el usuario"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail={"success": False, "data": {
                "title": "Error al actualizar el usuario",
                "message": str(e),
            }})

    def _get_field_display_name(self, field_name):
        """Obtener un nombre legible para los campos del usuario"""
        field_mapping = {
            "name": "nombre",
            "first_last_name": "apellido paterno",
            "second_last_name": "apellido materno",
            "address": "dirección",
            "profile_picture": "imagen de perfil",
            "phone": "número de teléfono",
            "email": "correo electrónico"
        }
        return field_mapping.get(field_name, field_name)

    async def _create_profile_update_notification(self, user_id: int, message: str):
        """Crear una notificación para actualización de perfil"""
        try:
            # Importar el servicio de propiedades para crear la notificación
            from app.property_routes.services import PropertyLotService
            
            # Crear una nueva instancia del servicio con la misma sesión de DB
            property_service = PropertyLotService(self.db)
            
            # Crear la notificación
            await property_service.create_notification(
                user_id=user_id,
                title="Actualización de información personal",
                message=message,
                notification_type="profile_update"
            )
        except Exception as e:
            # Solo registrar el error pero no fallar la operación principal
            print(f"Error al crear notificación de actualización de perfil: {str(e)}")

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
        """Obtener todos los usuarios con sus detalles"""
        try:
            # Filtramos los campos que queremos devolver utilizando `with_entities()`
            users = self.db.query(User).join(User.type_document).join(User.status_user).join(User.gender).with_entities(
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
            ).all()  #  obtener todos los usuarios
            
            if not users:
                return {
                    "success": False,
                    "data": {
                        "title": "Error al obtener los usuarios",
                        "message": "No se encontraron usuarios."
                    }
                }
            
            print([users])

            # Convertir los resultados a diccionarios
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
                    "date_issuance_document": user.date_issuance_document,  # fecha de expedición
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

                # Si no tiene roles asignados, se asigna una lista vacía
                user_roles = [{"id": role.id, "name": role.name} for role in user_obj.roles] if user_obj.roles else []

                # Agregar los roles al diccionario del usuario
                user_dict["roles"] = user_roles

                # Añadir el diccionario a la lista de usuarios
                users_list.append(user_dict)

            return jsonable_encoder({"success": True, "data": users_list})  # Usamos jsonable_encoder para convertir a formato JSON

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
