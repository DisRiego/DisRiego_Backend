from typing import List
import uuid
import os
from datetime import datetime, timedelta, date
from fastapi import HTTPException, Depends, status, UploadFile
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session, joinedload
from app.users.models import Gender, Status, TypeDocument, User, PasswordReset
from Crypto.Protocol.KDF import scrypt
from app.users.schemas import UserCreateRequest, ChangePasswordRequest, UserUpdateInfo, AdminUserCreateResponse
from app.roles.models import Role 
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
                                        department: str, municipality: int, 
                                        address: str, phone: str, 
                                        profile_picture: str = None) -> dict:
        """
        Completa el registro del usuario despues de su primer login
        
        Args:
            user_id: ID del usuario
            country: Pais de residencia
            department: Departamento o provincia
            municipality: Codigo de municipio (1-37)
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
                
            # Validar que el municipio esté en el rango correcto
            if municipality < 1 or municipality > 37:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Error en registro",
                            "message": "El codigo de municipio debe estar entre 1 y 37"
                        }
                    }
                )
                
            # Actualizar los datos del usuario
            user.country = country
            user.department = department
            user.municipality = municipality
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
                    "has_profile_data": user.country is not None and user.department is not None and user.municipality is not None
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
                    TypeDocument.name.label("type_document_name"),
                    User.status_id,
                    Status.name.label("status_name"),
                    Status.description.label("status_description"),
                    User.gender_id,
                    Gender.name.label("gender_name"),
                    # Nuevos campos
                    User.country,
                    User.department,
                    User.municipality,
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
                    "status_name": user.status_name,
                    "status_description": user.status_description,
                    "type_document": user.type_document_id,
                    "type_document_name": user.type_document_name,
                    "gender": user.gender_id,
                    "gender_name": user.gender_name,
                    # Nuevos campos
                    "country": user.country,
                    "department": user.department,
                    "municipality": user.municipality,
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
                "municipality": user.municipality,
                "first_login_complete": user.first_login_complete
            }
            
            return jsonable_encoder({"success": True, "data": [user_dict]})
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al obtener la información del usuario: {str(e)}"
            )
        

async def update_basic_profile(self, user_id: int, country: str = None, 
                             department: str = None, municipality: int = None,
                             address: str = None, phone: str = None,
                             profile_picture: str = None) -> dict:
        """
        Actualiza solo la informacion basica del perfil de un usuario.
        
        Args:
            user_id: ID del usuario
            country: Pais (opcional)
            department: Departamento (opcional)
            municipality: Codigo de municipio (opcional)
            address: Direccion (opcional)
            phone: Teléfono (opcional)
            profile_picture: Ruta a la imagen de perfil (opcional)
            
        Returns:
            Diccionario con el resultado de la operacion
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
                            "title": "Error en actualizacion",
                            "message": "Usuario no encontrado"
                        }
                    }
                )
                
            # Actualizar solo los campos proporcionados
            if country is not None:
                user.country = country
                
            if department is not None:
                user.department = department
                
            if municipality is not None:
                # Validar el rango del municipio
                if municipality < 1 or municipality > 37:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "success": False,
                            "data": {
                                "title": "Error en actualizacion",
                                "message": "El codigo de municipio debe estar entre 1 y 37"
                            }
                        }
                    )
                user.municipality = municipality
                
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
                        "message": "Informacion del perfil actualizada correctamente"
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
                        type_document_id: int, document_number: str, 
                        date_issuance_document: date, birthday: date, 
                        gender_id: int, roles: List[int]) -> AdminUserCreateResponse:
    """
    Crea un nuevo usuario en el sistema con los datos proporcionados por un administrador.
    
    Args:
        name: Nombres del usuario
        first_last_name: Primer apellido
        second_last_name: Segundo apellido
        type_document_id: ID del tipo de documento
        document_number: Número de documento
        date_issuance_document: Fecha de expedición del documento
        birthday: Fecha de nacimiento
        gender_id: ID del género
        roles: Lista de IDs de roles asignados al usuario
        
    Returns:
        Respuesta con estado de éxito y mensaje
    """
    try:
        # Validar que el tipo de documento exista
        type_document = self.db.query(TypeDocument).filter(TypeDocument.id == type_document_id).first()
        if not type_document:
            return AdminUserCreateResponse(
                success=False,
                message=f"El tipo de documento con ID {type_document_id} no existe"
            )
            
        # Validar que el género exista
        gender = self.db.query(Gender).filter(Gender.id == gender_id).first()
        if not gender:
            return AdminUserCreateResponse(
                success=False,
                message=f"El género con ID {gender_id} no existe"
            )
            
        # Verificar si ya existe un usuario con ese número de documento
        existing_user = self.db.query(User).filter(User.document_number == document_number).first()
        if existing_user:
            return AdminUserCreateResponse(
                success=False,
                message=f"Ya existe un usuario con el número de documento {document_number}"
            )
            
        # Validar los roles
        db_roles = self.db.query(Role).filter(Role.id.in_(roles)).all()
        if len(db_roles) != len(roles):
            return AdminUserCreateResponse(
                success=False,
                message="Uno o más roles seleccionados no existen"
            )
            
        # Generar una contraseña aleatoria segura (12 caracteres)
        password = self._generate_random_password()
        
        # Generar hash y salt para la contraseña
        salt, hash_password = self.hash_password(password)
        
        # Generar un email temporal basado en el nombre y número de documento
        # Por ejemplo: juan.perez.12345678@temp.disriego.com
        email_username = f"{name.lower().replace(' ', '.')}.{first_last_name.lower()}.{document_number}"
        email = f"{email_username}@temp.disriego.com"
        
        # Crear el nuevo usuario
        new_user = User(
            name=name,
            first_last_name=first_last_name,
            second_last_name=second_last_name,
            type_document_id=type_document_id,
            document_number=document_number,
            date_issuance_document=date_issuance_document,
            birthday=birthday,
            gender_id=gender_id,
            email=email,
            password=hash_password,
            password_salt=salt,
            status_id=1  # Asumiendo que 1 es el estado "Activo"
        )
        
        # Asignar roles
        new_user.roles = db_roles
        
        # Guardar en la base de datos
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        
        # Intentar enviar email con credenciales (en un entorno real)
        try:
            self._send_credentials_email(email, password, name)
        except Exception as e:
            # Log el error pero continuamos porque el usuario ya fue creado
            print(f"Error al enviar email: {str(e)}")
            
        return AdminUserCreateResponse(
            success=True,
            message=f"Usuario creado correctamente. Email temporal: {email}, Contraseña: {password}",
            user_id=new_user.id
        )
            
    except Exception as e:
        self.db.rollback()
        raise Exception(f"Error al crear usuario: {str(e)}")



    
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