import os
from fastapi import HTTPException, UploadFile, File, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.property_routes.models import Property, Lot, PropertyLot, Notification, PropertyUser
from sqlalchemy.orm import Session
from app.property_routes.schemas import PropertyCreate, PropertyResponse
from app.users.models import User
from app.roles.models import Role, user_role_table
from datetime import datetime
from sqlalchemy import and_

class PropertyLotService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_properties(self):
        """Obtener todos los predios"""
        try:
            # Realizar la consulta para obtener todos los predios
            properties = self.db.query(Property).all()
            if not properties:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": jsonable_encoder([])
                    }
                )
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": jsonable_encoder(properties)
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Predios",
                        "message": f"Error al obtener los predios, Contacta al administrador"
                    }
                }
            )

    async def create_property(self, name: str, longitude: float, latitude: float, extension: float, 
                        real_estate_registration_number: int, description: str = None, location: str = None,
                        public_deed: UploadFile = File(...), freedom_tradition_certificate: UploadFile = File(...),
                        user_id: int = None):
        """Crear un nuevo predio en la base de datos con la carga de archivos y generar notificación"""
        # Validación de unicidad de registro de predio
        existing_property = self.db.query(Property).filter(Property.real_estate_registration_number == real_estate_registration_number).first()
        if existing_property:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "data": {
                        "title": "Creacion de predios",
                        "message": f"El registro de predio ya existe en el sistema"
                    }
                }
            )

        if not name or longitude is None or latitude is None or extension is None or not real_estate_registration_number:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "data": {
                        "title": "Creacion de predios",
                        "message": f"Faltan campos requeridos."
                    }
                }
            )
        
        # Validar que los archivos hayan sido enviados
        if not public_deed or not freedom_tradition_certificate:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "data": {
                        "title": "Creacion de predios",
                        "message": f"Faltan los archivos requeridos para el predio."
                    }
                }
            )

        try:
            # Guardar los archivos
            public_deed_path = await self.save_file(public_deed)
            freedom_tradition_certificate_path = await self.save_file(freedom_tradition_certificate)

            # Crear el objeto Property
            property = Property(
                name=name,
                longitude=longitude,
                latitude=latitude,
                extension=extension,
                real_estate_registration_number=real_estate_registration_number,
                public_deed=public_deed_path,
                freedom_tradition_certificate=freedom_tradition_certificate_path,
            )

            self.db.add(property)
            self.db.commit()
            self.db.refresh(property)

            # Si se proporcionó un user_id, asociar el usuario al predio
            if user_id:
                property_user = PropertyUser(property_id=property.id, user_id=user_id)
                self.db.add(property_user)
                self.db.commit()
                
                # Notificar al usuario que se le ha asignado un nuevo predio
                await self.create_notification(
                    user_id=user_id,
                    title="Nuevo predio registrado",
                    message=f"Se ha registrado un nuevo predio '{name}' asignado a tu cuenta.",
                    notification_type="property_creation"
                )
            
            # Notificar a los administradores sobre la creación del nuevo predio
            # Primero, obtener todos los usuarios con rol de administrador
            admin_users = self.db.query(User).join(user_role_table).join(Role).filter(Role.name == "Administrador").all()
            
            for admin in admin_users:
                await self.create_notification(
                    user_id=admin.id,
                    title="Nuevo predio en el sistema",
                    message=f"Se ha registrado un nuevo predio '{name}' con número de registro {real_estate_registration_number}.",
                    notification_type="property_creation"
                )

            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {
                        "title": "Creacion de predios",
                        "message": f"Se ha creado el predio satisfactoriamente"
                    }
                }
            )

        except Exception as e:
            self.db.rollback()  # Revertir cambios si ocurre algún error
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Creacion de predios",
                        "message": f"Error al crear el predio, Contacta al administrador"
                    }
                }
            )

    async def save_file(self, file: UploadFile) -> str:
        """Guardar un archivo en el servidor"""
        try:
            # Guardamos los archivos en un directorio específico
            directory = "files/"
            if not os.path.exists(directory):
                os.makedirs(directory)  # Crear el directorio 'files' si no existe

            # Guardar el archivo en el directorio específico
            file_path = os.path.join(directory, file.filename)

            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())
            return file_path
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al guardar el archivo: {str(e)}")

    async def create_lot(self, name: str, area: float, property_id: int, user_id: int = None):
        """Crear un nuevo lote asociado a un predio y generar notificación"""
        try:
            # Verificar si el predio existe
            property = self.db.query(Property).filter(Property.id == property_id).first()
            if not property:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "data": {
                            "title": "Creación de lote",
                            "message": "El predio especificado no existe."
                        }
                    }
                )
                
            # Crear el nuevo lote
            lot = Lot(
                name=name, 
                extension=area, 
                property_id=property_id
            )
            self.db.add(lot)
            self.db.commit()
            self.db.refresh(lot)
            
            # Crear la asociación entre predio y lote
            property_lot = PropertyLot(property_id=property_id, lot_id=lot.id)
            self.db.add(property_lot)
            self.db.commit()
            
            # Notificar a los usuarios asociados al predio
            users = self.db.query(User).join(PropertyUser).filter(PropertyUser.property_id == property_id).all()
            
            for user in users:
                await self.create_notification(
                    user_id=user.id,
                    title="Nuevo lote creado",
                    message=f"Se ha creado un nuevo lote '{name}' en el predio '{property.name}'.",
                    notification_type="lot_creation"
                )
            
            # Si se proporcionó un user_id específico (creador), notificarle también
            if user_id and not any(user.id == user_id for user in users):
                await self.create_notification(
                    user_id=user_id,
                    title="Nuevo lote creado",
                    message=f"Has creado exitosamente el lote '{name}' en el predio '{property.name}'.",
                    notification_type="lot_creation"
                )
            
            # Notificar a los administradores
            admin_users = self.db.query(User).join(user_role_table).join(Role).filter(Role.name == "Administrador").all()
            
            for admin in admin_users:
                # Evitar notificaciones duplicadas si el admin ya fue notificado como usuario del predio
                if not any(user.id == admin.id for user in users) and (not user_id or admin.id != user_id):
                    await self.create_notification(
                        user_id=admin.id,
                        title="Nuevo lote en el sistema",
                        message=f"Se ha creado un nuevo lote '{name}' en el predio '{property.name}'.",
                        notification_type="lot_creation"
                    )
                    
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {
                        "title": "Creación de lote",
                        "message": f"Se ha creado el lote satisfactoriamente",
                        "lot_id": lot.id
                    }
                }
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Creación de lote",
                        "message": f"Error al crear el lote: {str(e)}"
                    }
                }
            )

    def link_property_lot(self, property_id: int, lot_id: int):
        """Asociar un predio con un lote"""
        try:
            property_lot = PropertyLot(property_id=property_id, lot_id=lot_id)
            self.db.add(property_lot)
            self.db.commit()
            return {"success": True, "data": "Predio y lote asociados correctamente."}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Error al asociar el predio con el lote.")
        

    def get_lots_property(self, property_id: int):
        """Obtener todos los lotes de un predio"""
        try:
            # Realizar la consulta para obtener todos los lotes de un predio
            lots = self.db.query(Lot).join(PropertyLot, PropertyLot.lot_id == Lot.id).filter(PropertyLot.property_id == property_id).all()
            
            if not lots:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "data": jsonable_encoder([])
                    }
                )

            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": jsonable_encoder(lots)
                }
            )

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Error al obtener los lotes del predio",
                        "message": f"Error al obtener los lotes, Contacta al administrador: {str(e)}"
                    }
                }
            )

    async def create_notification(self, user_id: int, title: str, message: str, notification_type: str):
        """Crear una nueva notificación para un usuario y enviarla en tiempo real si está conectado"""
        try:
            # Verificar si el usuario existe
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "data": {
                            "title": "Notificaciones",
                            "message": "Usuario no encontrado"
                        }
                    }
                )

            # Crear la notificación
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                type=notification_type,
                read=False
            )
            self.db.add(notification)
            self.db.commit()
            self.db.refresh(notification)

            # Enviar la notificación en tiempo real si el usuario está conectado
            from app.websockets import notification_manager
            notification_data = {
                "id": notification.id,
                "user_id": notification.user_id,
                "title": notification.title,
                "message": notification.message,
                "type": notification.type,
                "read": notification.read,
                "created_at": notification.created_at.isoformat()
            }
            await notification_manager.send_notification(user_id, {
                "type": "new_notification",
                "data": notification_data
            })

            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": jsonable_encoder(notification)
                }
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Notificaciones",
                        "message": f"Error al crear la notificación: {str(e)}"
                    }
                }
            )

    def get_user_notifications(self, user_id: int):
        """Obtener todas las notificaciones de un usuario"""
        try:
            # Verificar si el usuario existe
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "data": {
                            "title": "Notificaciones",
                            "message": "Usuario no encontrado"
                        }
                    }
                )

            # Obtener las notificaciones
            notifications = self.db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).all()

            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": jsonable_encoder(notifications)
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Notificaciones",
                        "message": f"Error al obtener las notificaciones: {str(e)}"
                    }
                }
            )

    def mark_notification_as_read(self, notification_id: int):
        """Marcar una notificación como leída"""
        try:
            # Buscar la notificación
            notification = self.db.query(Notification).filter(Notification.id == notification_id).first()
            if not notification:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "data": {
                            "title": "Notificaciones",
                            "message": "Notificación no encontrada"
                        }
                    }
                )

            # Marcar como leída
            notification.read = True
            self.db.commit()
            self.db.refresh(notification)

            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {
                        "title": "Notificaciones",
                        "message": "Notificación marcada como leída correctamente"
                    }
                }
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Notificaciones",
                        "message": f"Error al marcar la notificación como leída: {str(e)}"
                    }
                }
            )

    def mark_all_notifications_as_read(self, user_id: int):
        """Marcar todas las notificaciones de un usuario como leídas"""
        try:
            # Verificar si el usuario existe
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "data": {
                            "title": "Notificaciones",
                            "message": "Usuario no encontrado"
                        }
                    }
                )

            # Marcar todas como leídas
            self.db.query(Notification).filter(Notification.user_id == user_id, Notification.read == False).update({"read": True})
            self.db.commit()

            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {
                        "title": "Notificaciones",
                        "message": "Todas las notificaciones han sido marcadas como leídas"
                    }
                }
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Notificaciones",
                        "message": f"Error al marcar todas las notificaciones como leídas: {str(e)}"
                    }
                }
            )