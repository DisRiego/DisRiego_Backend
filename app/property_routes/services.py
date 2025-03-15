import os
import uuid
from fastapi import HTTPException, UploadFile, File
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.property_routes.models import Property, Lot, PropertyLot, LotHistory, PropertyUser
from app.property_routes.schemas import PropertyCreate, PropertyResponse
from app.users.models import User

class PropertyLotService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_properties(self):
        """Obtener todos los predios"""
        try:
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
                        "message": "Error al obtener los predios, Contacta al administrador"
                    }
                }
            )

    async def create_property(self, user_id: int, name: str, longitude: float, latitude: float, extension: float, real_estate_registration_number: int, public_deed: UploadFile = File(...), freedom_tradition_certificate: UploadFile = File(...)):
        """Crear un nuevo predio en la base de datos con la carga de archivos"""
        try:
            # Validar existencia del usuario
            existing_user = self.db.query(User).filter(User.id == user_id).first()
            if not existing_user:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Creacion de predios",
                            "message": "El usuario a relacionar no existe en el sistema"
                        }
                    }
                )

            # Validación de unicidad de registro de predio
            existing_property = self.db.query(Property).filter(Property.real_estate_registration_number == real_estate_registration_number).first()
            if existing_property:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Creacion de predios",
                            "message": "El registro de predio ya existe en el sistema"
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
                            "message": "Faltan campos requeridos."
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
                            "message": "Faltan los archivos requeridos para el predio."
                        }
                    }
                )

            # Guardar los archivos
            public_deed_path = await self.save_file(public_deed, "uploads/files_properties/")
            freedom_tradition_certificate_path = await self.save_file(freedom_tradition_certificate, "uploads/files_properties/")

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

            # Guardar la relación entre el usuario y la propiedad
            property_user = PropertyUser(
                user_id=user_id,
                property_id=property.id
            )
            self.db.add(property_user)
            self.db.commit()

            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {
                        "title": "Creacion de predios",
                        "message": "Se ha creado el predio satisfactoriamente"
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
                        "title": "Creacion de predios",
                        "message": "Error al crear el predio, Contacta al administrador"
                    }
                }
            )

    async def save_file(self, file: UploadFile, directory: str = "files/") -> str:
        """Guardar un archivo en el servidor con un nombre único"""
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
            unique_filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
            file_path = os.path.join(directory, unique_filename)
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())
            return file_path
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al guardar el archivo: {str(e)}")

    async def create_lot(self, property_id: int, name: str, longitude: float, latitude: float, extension: float, real_estate_registration_number: int, public_deed: UploadFile = File(...), freedom_tradition_certificate: UploadFile = File(...)):
        """Crear un nuevo lote en la base de datos con la carga de archivos"""
        try:
            existing_property = self.db.query(Property).filter(Property.id == property_id).first()
            if not existing_property:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Creacion de lotes",
                            "message": "El predio no existe en el sistema"
                        }
                    }
                )
            
            existing_lot = self.db.query(Lot).filter(Lot.real_estate_registration_number == str(real_estate_registration_number)).first()
            if existing_lot:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Creacion de lotes",
                            "message": "El registro de lote ya existe en el sistema"
                        }
                    }
                )

            if not name or longitude is None or latitude is None or extension is None or not real_estate_registration_number:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Creacion de lotes",
                            "message": "Faltan campos requeridos."
                        }
                    }
                )
            
            if not public_deed or not freedom_tradition_certificate:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Creacion de lotes",
                            "message": "Faltan los archivos requeridos para el lote."
                        }
                    }
                )
        
            public_deed_path = await self.save_file(public_deed, "uploads/files_lots/")
            freedom_tradition_certificate_path = await self.save_file(freedom_tradition_certificate, "uploads/files_lots/")

            lot = Lot(
                name=name,
                longitude=longitude,
                latitude=latitude,
                extension=extension,
                real_estate_registration_number=real_estate_registration_number,
                public_deed=public_deed_path,
                freedom_tradition_certificate=freedom_tradition_certificate_path,
            )

            self.db.add(lot)
            self.db.commit()
            self.db.refresh(lot)

            property_lot = PropertyLot(
                lot_id=lot.id,
                property_id=property_id
            )
            self.db.add(property_lot)
            self.db.commit()

            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {
                        "title": "Creacion de lotes",
                        "message": "Se ha creado el lote satisfactoriamente"
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
                        "title": "Creacion de lotes",
                        "message": "Error al crear el lote, Contacta al administrador"
                    }
                }
            )

    def get_lots_property(self, property_id: int):
        """Obtener todos los lotes de un predio"""
        try:
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

    async def edit_lot(self, lot_id: int, name: str, longitude: float, latitude: float, extension: float, 
                       real_estate_registration_number: int, public_deed: UploadFile = File(None), 
                       freedom_tradition_certificate: UploadFile = File(None)):
        """Editar un lote existente en la base de datos con la posibilidad de actualizar archivos"""
        try:
            lot = self.db.query(Lot).filter(Lot.id == lot_id).first()
            if not lot:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Edición de lote",
                            "message": "El lote no existe en el sistema"
                        }
                    }
                )
            
            existing_lot = self.db.query(Lot) \
                .filter(Lot.real_estate_registration_number == str(real_estate_registration_number)) \
                .filter(Lot.id != lot_id) \
                .first()
            if existing_lot:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Edición de lote",
                            "message": "El número de registro del lote ya existe en otro lote"
                        }
                    }
                )

            lot.name = name
            lot.longitude = longitude
            lot.latitude = latitude
            lot.extension = extension
            lot.real_estate_registration_number = real_estate_registration_number
            
            if public_deed:
                public_deed_path = await self.save_file(public_deed, "uploads/files_lots/")
                lot.public_deed = public_deed_path
            
            if freedom_tradition_certificate:
                freedom_tradition_certificate_path = await self.save_file(freedom_tradition_certificate, "uploads/files_lots/")
                lot.freedom_tradition_certificate = freedom_tradition_certificate_path

            self.db.commit()
            self.db.refresh(lot)

            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {
                        "title": "Edición de lote",
                        "message": "El lote ha sido editado satisfactoriamente"
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
                        "title": "Edición de lote",
                        "message": f"Error al editar el lote, Contacta al administrador: {str(e)}"
                    }
                }
            )

    async def edit_property(self, user_id: int, property_id: int, name: str, longitude: float, latitude: float, 
                            extension: float, real_estate_registration_number: int, public_deed: UploadFile = File(None), 
                            freedom_tradition_certificate: UploadFile = File(None)):
        """Editar un predio existente en la base de datos con la posibilidad de actualizar archivos"""
        try:
            # Validar existencia del usuario
            existing_user = self.db.query(User).filter(User.id == user_id).first()
            if not existing_user:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Edición de predios",
                            "message": "El usuario a relacionar no existe en el sistema"
                        }
                    }
                )
            
            # Verificar existencia del predio
            property = self.db.query(Property).filter(Property.id == property_id).first()
            if not property:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Edición de predio",
                            "message": "El predio no existe en el sistema"
                        }
                    }
                )
            
            # Validar unicidad del número de registro para el predio actualizando solo si se trata de otro predio
            existing_property = self.db.query(Property) \
                .filter(Property.real_estate_registration_number == str(real_estate_registration_number)) \
                .filter(Property.id != property_id) \
                .first()
            if existing_property:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Edición de predio",
                            "message": "El número de registro del predio ya existe en otro predio"
                        }
                    }
                )
            
            # Actualizar la información del predio
            property.name = name
            property.longitude = longitude
            property.latitude = latitude
            property.extension = extension
            property.real_estate_registration_number = real_estate_registration_number
            
            if public_deed:
                public_deed_path = await self.save_file(public_deed, "uploads/files_properties/")
                property.public_deed = public_deed_path
            
            if freedom_tradition_certificate:
                freedom_tradition_certificate_path = await self.save_file(freedom_tradition_certificate, "uploads/files_properties/")
                property.freedom_tradition_certificate = freedom_tradition_certificate_path

            self.db.commit()
            self.db.refresh(property)

            # Verificar y actualizar el usuario relacionado si se ha cambiado
            property_user = self.db.query(PropertyUser).filter(PropertyUser.property_id == property_id).first()
            if property_user and property_user.user_id != user_id:
                property_user.user_id = user_id
                self.db.commit()
                self.db.refresh(property_user)

            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {
                        "title": "Edición de predio",
                        "message": "El predio ha sido editado satisfactoriamente"
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
                        "title": "Edición de predio",
                        "message": f"Error al editar el predio, Contacta al administrador: {str(e)}"
                    }
                }
            )

    def disable_lot(self, lot_id: int, user_id: int, details: str = None):
        """Inhabilitar un lote y registrar la acción en el historial"""
        try:
            lot = self.db.query(Lot).filter(Lot.id == lot_id).first()
            if not lot:
                raise HTTPException(status_code=404, detail="Lote no encontrado")
            if not lot.is_active:
                raise HTTPException(status_code=400, detail="El lote ya está inhabilitado")
            
            lot.is_active = False
            history_entry = LotHistory(
                lot_id=lot_id,
                user_id=user_id,
                action="disable",
                details=details or "Inhabilitación de lote"
            )
            self.db.add(history_entry)
            self.db.commit()
            
            return {
                "success": True, 
                "data": {
                    "message": "Lote inhabilitado correctamente",
                    "lot_id": lot_id,
                    "timestamp": history_entry.timestamp
                }
            }
        except HTTPException as e:
            self.db.rollback()
            raise e
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al inhabilitar el lote: {str(e)}")
        
    def get_lot_history(self, lot_id: int):
        """
        Obtener el historial de cambios de un lote
        Args:
            lot_id: ID del lote
        Returns:
            Dict con el historial de cambios
        """
        try:
            lot = self.db.query(Lot).filter(Lot.id == lot_id).first()
            if not lot:
                raise HTTPException(status_code=404, detail="Lote no encontrado")
            
            history = self.db.query(LotHistory).filter(LotHistory.lot_id == lot_id).order_by(LotHistory.timestamp.desc()).all()
            
            history_data = []
            for entry in history:
                user = self.db.query(User).filter(User.id == entry.user_id).first()
                history_data.append({
                    "id": entry.id,
                    "action": entry.action,
                    "details": entry.details,
                    "timestamp": entry.timestamp,
                    "user": {
                        "id": user.id,
                        "name": user.name if user else "Usuario desconocido",
                        "email": user.email if user else None
                    }
                })
            
            return {
                "success": True,
                "data": history_data
            }
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al obtener el historial del lote: {str(e)}")
