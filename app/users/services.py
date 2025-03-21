import uuid
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta, date
from typing import List, Optional
from fastapi import HTTPException, Depends, status, UploadFile
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from app.users.models import Gender, Status, TypeDocument, User, PasswordReset, PreRegisterToken, ActivationToken
from app.users.schemas import UserCreateRequest, ChangePasswordRequest, UserUpdateInfo, AdminUserCreateResponse, PreRegisterResponse, ActivateAccountResponse
from app.roles.models import Role
from Crypto.Protocol.KDF import scrypt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from app.auth.services import SECRET_KEY, ALGORITHM
from jose import jwt, JWTError
from fastapi.responses import JSONResponse

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """Clase para gestionar la creación y obtención de usuarios"""

    def __init__(self, db: Session):
        self.db = db

    async def save_profile_picture(self, file: UploadFile) -> str:
        """
        Guarda una imagen de perfil en el servidor con un nombre único
        
        Args:
            file: El archivo de imagen subido
            
        Returns:
            La ruta donde se guardo la imagen
        """
        try:
            # Crear directorio si no existe
            directory = "uploads/profile_pictures/"
            if not os.path.exists(directory):
                os.makedirs(directory)
                
            # Generar nombre unico
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(directory, unique_filename)
            
            # Guardar el archivo
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())
                
            return file_path
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al guardar la imagen de perfil: {str(e)}"
            )
            
    async def complete_first_login_registration(self, user_id: int, country: str, 
                                        department: str, city: int, 
                                        address: str, phone: str, 
                                        profile_picture: str = None) -> dict:
        """
        Completa el registro del usuario despues de su primer login
        
        Args:
            user_id: ID del usuario
            country: Pais de residencia
            department: Departamento o provincia
            city: Codigo de municipio (1-37)
            address: Direccion completa
            phone: Numero de teléfono
            profile_picture: Ruta a la imagen de perfil (opcional)
            
        Returns:
            Diccionario con el resultado de la operación
        """
        try:
            # Validar que el usuario existe
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "data": {
                            "title": "Error en registro",
                            "message": "Usuario no encontrado"
                        }
                    }
                )
                

                
            # Actualizar los datos del usuario
            user.country = country
            user.department = department
            user.city = city
            user.address = address
            user.phone = phone
            
            if profile_picture:
                user.profile_picture = profile_picture
                
            # Marcar como completo el registro del primer login
            user.first_login_complete = True
            
            # Guardar cambios
            self.db.commit()
            self.db.refresh(user)
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {
                        "title": "Registro completo",
                        "message": "Datos de perfil guardados correctamente"
                    }
                }
            )
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error al completar el registro: {str(e)}"
            )

    def check_profile_completion(self, user_id: int) -> dict:
        """
        Verifica si el usuario ya ha completado su perfil después del primer login
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Diccionario con el estado de completitud del perfil
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    "success": False,
                    "data": {
                        "title": "Error",
                        "message": "Usuario no encontrado"
                    }
                }
                
            return {
                "success": True,
                "data": {
                    "first_login_complete": user.first_login_complete,
                    "has_profile_data": user.country is not None and user.department is not None and user.city is not None
                }
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al verificar el estado del perfil: {str(e)}"
            )

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

            return {"success": True, "title":"Éxito", "data": "Usuario creado correctamente"}

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
                    User.document_number,  # Campo corregido
                    User.date_issuance_document,
                    User.type_document_id,
                    User.birthday,
                    TypeDocument.name.label("type_document_name"),
                    User.status_id,
                    Status.name.label("status_name"),
                    Status.description.label("status_description"),
                    User.gender_id,
                    Gender.name.label("gender_name"),
                    # Nuevos campos
                    User.country,
                    User.department,
                    User.city,
                    User.first_login_complete
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
                    "document_number": user.document_number,
                    "status": user.status_id,
                    "birthday": user.birthday,
                    "status_name": user.status_name,
                    "status_description": user.status_description,
                    "type_document": user.type_document_id,
                    "type_document_name": user.type_document_name,
                    "gender": user.gender_id,
                    "gender_name": user.gender_name,
                    # Nuevos campos
                    "country": user.country,
                    "department": user.department,
                    "city": user.city,
                    "first_login_complete": user.first_login_complete
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
    async def validate_for_pre_register(self, document_type_id: int, document_number: str, 
                                        date_issuance_document: datetime) -> PreRegisterResponse:
        try:
            # Convertir documento a int para la búsqueda
            doc_number_int = int(document_number)
            
            # Buscar usuario con el documento y tipo correspondiente
            user = self.db.query(User).filter(
                User.document_number == doc_number_int,
                User.type_document_id == document_type_id
            ).first()
            
            if not user:
                return PreRegisterResponse(
                    success=False,
                    message="No existe un usuario con estos datos en el sistema."
                )
                
            # Verificar que la fecha de expedición coincide
            if user.date_issuance_document.date() != date_issuance_document:
                return PreRegisterResponse(
                    success=False,
                    message="La fecha de expedición no coincide con nuestros registros."
                )
                
            # Verificar que el usuario no haya completado su pre-registro
            if user.status_id == 1:
                return PreRegisterResponse(
                    success=False,
                    message="Este usuario ya ha realizado su pre-registro. Por favor inicie sesión o use la opción de recuperar contraseña."
                )
                
            # Verificar que el usuario ya esté activo (status_id == 1 significa activo)
            if user.status_id == 1:
                return PreRegisterResponse(
                    success=False,
                    message="Esta cuenta ya está activa. Por favor inicie sesión o use la opción de recuperar contraseña."
                )
                
            # Verificar si el usuario ya tiene un email registrado
            if user.email:
                return PreRegisterResponse(
                    success=False,
                    message="Este usuario ya tiene un correo electrónico registrado. Por favor inicie sesión o use la opción de recuperar contraseña."
                )
                
            # Generar token para completar pre-registro
            token = str(uuid.uuid4())
            expiration = datetime.utcnow() + timedelta(hours=24)  # Token válido por 24 horas
            
            # Guardar el token en la base de datos
            pre_register_token = PreRegisterToken(
                token=token,
                user_id=user.id,
                expires_at=expiration,
                used=False
            )
            
            self.db.add(pre_register_token)
            self.db.commit()
            
            # Retornar respuesta exitosa con token
            return PreRegisterResponse(
                success=True,
                message="Validación exitosa. Complete su registro con email y contraseña.",
                token=token
            )
            
        except ValueError as e:
            self.db.rollback()
            raise ValueError(f"Error en la validación: {str(e)}")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error de base de datos: {str(e)}")
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error inesperado: {str(e)}")

    async def complete_pre_register(self, token: str, email: str, password: str) -> PreRegisterResponse:
        try:
            # Verificar que el token es válido y no ha sido usado
            pre_register_token = self.db.query(PreRegisterToken).filter(
                PreRegisterToken.token == token,
                PreRegisterToken.used == False,
                PreRegisterToken.expires_at > datetime.utcnow()
            ).first()
            
            if not pre_register_token:
                return PreRegisterResponse(
                    success=False,
                    message="Token inválido o expirado. Por favor, reinicie el proceso."
                )
                    
            # Obtener el usuario asociado al token
            user = self.db.query(User).filter(User.id == pre_register_token.user_id).first()
            if not user:
                return PreRegisterResponse(
                    success=False,
                    message="Usuario no encontrado. Por favor, contacte al administrador."
                )
                    
            # Verificar que el email no esté en uso por otro usuario
            existing_email = self.db.query(User).filter(
                User.email == email,
                User.id != user.id
            ).first()
                
            if existing_email:
                # No se marca el token como usado para permitir reintentar
                return PreRegisterResponse(
                    success=False,
                    message="Este correo electrónico ya está registrado. Por favor utilice otro."
                )
                    
            # Generar hash y salt para la nueva contraseña
            salt, hash_password = self.hash_password(password)
                
            # Actualizar los datos del usuario
            user.email = email
            user.password = hash_password
            user.password_salt = salt
            user.status_id = 1  # Marca al usuario como activo

            # Marcar el token de pre-registro como usado
            pre_register_token.used = True
                
            # Generar token de activación
            activation_token = str(uuid.uuid4())
            expiration = datetime.utcnow() + timedelta(days=7)  # Token válido por 7 días
                
            # Guardar el token de activación
            new_activation_token = ActivationToken(
                token=activation_token,
                user_id=user.id,
                expires_at=expiration,
                used=False
            )
                
            self.db.add(new_activation_token)
            self.db.commit()
                
            # Enviar correo de activación (si falla, solo se loguea el error)
            activation_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/activate-account/{activation_token}"
            try:
                await self._send_activation_email(email, user.name, activation_url)
            except Exception as e:
                print(f"Error al enviar correo de activación: {str(e)}")
                
            # Retornar respuesta exitosa
            return PreRegisterResponse(
                success=True,
                message="Pre-registro completado con éxito. Se ha enviado un correo de activación a su dirección de email.",
                token=token
            )
                
        except ValueError as e:
            self.db.rollback()
            raise ValueError(f"Error en el pre-registro: {str(e)}")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error de base de datos: {str(e)}")
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error inesperado: {str(e)}")

    async def activate_account(self, activation_token: str) -> ActivateAccountResponse:
        try:
            # Verificar que el token es válido y no ha sido usado
            token = self.db.query(ActivationToken).filter(
                ActivationToken.token == activation_token,
                ActivationToken.used == False,
                ActivationToken.expires_at > datetime.utcnow()
            ).first()
            
            if not token:
                return ActivateAccountResponse(
                    success=False,
                    message="Token de activación inválido o expirado. Por favor, solicite uno nuevo."
                )
                
            # Obtener el usuario asociado al token
            user = self.db.query(User).filter(User.id == token.user_id).first()
            
            if not user:
                return ActivateAccountResponse(
                    success=False,
                    message="Usuario no encontrado. Por favor, contacte al administrador."
                )
                
            # Activar la cuenta: se marca el token como usado y se actualiza el status_id a 1 (Activo)
            token.used = True
            if user.status_id is None or user.status_id == 2:  # Asumiendo que 2 es "Inactivo"
                user.status_id = 1  # Asumiendo que 1 es "Activo"
            
            self.db.commit()
            
            return ActivateAccountResponse(
                success=True,
                message="¡Su cuenta ha sido activada con éxito! Ahora puede iniciar sesión en el sistema."
            )
        
        except ValueError as e:
            self.db.rollback()
            raise ValueError(f"Error en la activación: {str(e)}")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error de base de datos: {str(e)}")
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error inesperado: {str(e)}")
    

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

        
    def list_user(self, user_id: int):
            """
            Obtiene la información completa de un usuario, incluyendo relaciones:
            type_document, status_user, gender y roles.
            """
            try:
                user = (
                    self.db.query(User)
                    .options(
                        joinedload(User.type_document),
                        joinedload(User.status_user),
                        joinedload(User.gender),
                        joinedload(User.roles)
                    )
                    .filter(User.id == user_id)
                    .first()
                )
                if not user:
                    return {
                        "success": False,
                        "data": {
                            "title": "Error al obtener el usuario",
                            "message": "Usuario no encontrado."
                        }
                    }
                
                user_dict = {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "first_last_name": user.first_last_name,
                    "second_last_name": user.second_last_name,
                    "address": user.address,
                    "profile_picture": user.profile_picture,
                    "phone": user.phone,
                    "document_number": user.document_number,
                    "date_issuance_document": user.date_issuance_document,
                    "type_document_id": user.type_document_id,
                    "status_id": user.status_id,
                    "gender_id": user.gender_id,
                    # Si las relaciones están cargadas, se obtienen sus nombres
                    "type_document_name": user.type_document.name if user.type_document else None,
                    "status_name": user.status_user.name if user.status_user else None,
                    "status_description": user.status_user.description if user.status_user else None,
                    "gender_name": user.gender.name if user.gender else None,
                    "roles": [{"id": role.id, "name": role.name} for role in user.roles],
                    # Nuevos campos
                    "country": user.country,
                    "department": user.department,
                    "city": user.city,
                    "first_login_complete": user.first_login_complete
                }
                
                return jsonable_encoder({"success": True, "data": [user_dict]})
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error al obtener la información del usuario: {str(e)}"
                )
            

    async def update_basic_profile(
        self,
        user_id: int,
        country: Optional[int] = None,
        department: Optional[int] = None,
        city: Optional[int] = None,
        address: Optional[str] = None,
        phone: Optional[str] = None,
        profile_picture: Optional[str] = None
    ) -> dict:
        """
        Actualiza solo la información básica del perfil de un usuario.

        Args:
            user_id: ID del usuario
            country: País (opcional)
            department: Departamento (opcional)
            city: Código de municipio (opcional)
            address: Dirección (opcional)
            phone: Teléfono (opcional)
            profile_picture: Ruta a la imagen de perfil (opcional)

        Returns:
            Diccionario con el resultado de la operación
        """
        try:
            # Verificar que el usuario existe
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "data": {
                            "title": "Error en actualización",
                            "message": "Usuario no encontrado"
                        }
                    }
                )

            # Actualizar solo los campos proporcionados
            if country is not None:
                user.country = country
            if department is not None:
                user.department = department
            if city is not None:
                # Se asume que ya se validó el rango en el router
                user.city = city
            if address is not None:
                user.address = address
            if phone is not None:
                user.phone = phone
            if profile_picture is not None:
                user.profile_picture = profile_picture

       


            # Guardar los cambios
            self.db.commit()
            self.db.refresh(user)


            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {
                        "title": "Perfil actualizado",
                        "message": "Información del perfil actualizada correctamente"
                    }
                }
            )
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error al actualizar el perfil: {str(e)}"
            )
            
    def create_user_by_admin(self, name: str, first_last_name: str, second_last_name: str, 
                                type_document_id: int, document_number: str, date_issuance_document: datetime,
                                birthday: datetime, gender_id: int, roles: List[int]):
            try:
                db_user = User(
                    name=name,
                    first_last_name=first_last_name,
                    second_last_name=second_last_name,
                    type_document_id=type_document_id,
                    document_number=document_number,
                    date_issuance_document=date_issuance_document,
                    birthday=birthday,
                    gender_id=gender_id,
                    status_id=4  # Se asigna el status "Activo" al crear el usuario
                )
                
                if roles:
                    roles_obj = self.db.query(Role).filter(Role.id.in_(roles)).all()
                    db_user.roles = roles_obj

                self.db.add(db_user)
                self.db.commit()
                self.db.refresh(db_user)
                
                return {"success": True, "message": "Usuario creado correctamente", "user_id": db_user.id}

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


        
    def get_genders(self):
        """Obtiene todos los géneros disponibles en el sistema"""
        try:
            genders = self.db.query(Gender).all()
            return {
                "success": True,
                "data": jsonable_encoder(genders)
            }
        except Exception as e:
            raise Exception(f"Error al obtener géneros: {str(e)}")