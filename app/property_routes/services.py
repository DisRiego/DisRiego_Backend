import os
import uuid
from fastapi import HTTPException, UploadFile, File, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.property_routes.models import Property, Lot, PropertyLot, PropertyUser
from sqlalchemy.orm import Session
from app.property_routes.schemas import PropertyCreate, PropertyResponse
from app.users.models import User

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

    async def create_property(self,user_id: int,  name: str, longitude: float, latitude: float, extension: float, real_estate_registration_number: int, public_deed: UploadFile = File(...), freedom_tradition_certificate: UploadFile = File(...)):
        """Crear un nuevo predio en la base de datos con la carga de archivos"""

        try:
            # validar si existe la propiedad
            existing_user = self.db.query(User).filter(User.id == user_id).first()
            if not existing_user:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Creacion de predios",
                            "message": f"El usuario a relacionar no existe en el sistema"
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
                            "message": f"El registro de predio ya existe en el sistema"
                        }
                    }
                )
                # raise HTTPException(status_code=400, detail="")

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
                # raise HTTPException(status_code=400, detail="Faltan campos requeridos.")
            
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

            # Obtener el id del predio
            property_id = property.id

            # Guardar la relación entre el usuario y la propiedad
            property_user = PropertyUser(
                user_id=user_id,
                property_id=property_id
            )

            # Agregar la relación entre el lote y la propiedad
            self.db.add(property_user)
            self.db.commit()  # Realizar la transacción para la relación

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

    async def save_file(self, file: UploadFile, directory: str = "files/") -> str:
        """Guardar un archivo en el servidor con un nombre único"""
        try:
            # Crear el directorio si no existe
            if not os.path.exists(directory):
                os.makedirs(directory)

            # Generar un nombre único para el archivo usando UUID
            unique_filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"  # Usamos el nombre original de la extensión

            # Guardar el archivo en el directorio con el nombre único
            file_path = os.path.join(directory, unique_filename)

            # Guardar el archivo en el sistema de archivos
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())

            return file_path  # Devolver la ruta del archivo guardado
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al guardar el archivo: {str(e)}")

    async def create_lot(self, property_id: int, name: str, longitude: float, latitude: float, extension: float, real_estate_registration_number: int,public_deed: UploadFile = File(...), freedom_tradition_certificate: UploadFile = File(...)):
        """Crear un nuevo predio en la base de datos con la carga de archivos"""

        try:

            # validar si existe la propiedad
            existing_property = self.db.query(Property).filter(Property.id == property_id).first()
            if not existing_property:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Creacion de lotes",
                            "message": f"El predio no existe en el sistema"
                        }
                    }
                )
            
            # Validación de unicidad de registro de predio
            existing_lot = self.db.query(Lot).filter(Lot.real_estate_registration_number == str(real_estate_registration_number)).first()
            if existing_lot:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Creacion de lotes",
                            "message": f"El registro de lote ya existe en el sistema"
                        }
                    }
                )
                # raise HTTPException(status_code=400, detail="")

            if not name or longitude is None or latitude is None or extension is None or not real_estate_registration_number:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Creacion de lotes",
                            "message": f"Faltan campos requeridos."
                        }
                    }
                )
                # raise HTTPException(status_code=400, detail="Faltan campos requeridos.")
            
            # Validar que los archivos hayan sido enviados
            if not public_deed or not freedom_tradition_certificate:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Creacion de lotes",
                            "message": f"Faltan los archivos requeridos para el lote."
                        }
                    }
                )
        
            # Guardar los archivos
            public_deed_path = await self.save_file(public_deed, "uploads/files_lots/")
            freedom_tradition_certificate_path = await self.save_file(freedom_tradition_certificate, "uploads/files_lots/")

            # Crear el objeto lote
            lot = Lot(
                name=name,
                longitude=longitude,
                latitude=latitude,
                extension=extension,
                real_estate_registration_number=real_estate_registration_number,
                public_deed=public_deed_path,
                freedom_tradition_certificate=freedom_tradition_certificate_path,
            )

            # Guardar el lote en la base de datos
            self.db.add(lot)
            self.db.commit()  # Realizar la transacción
            self.db.refresh(lot)  # Obtener el id del lote recién creado

            # Obtener el id del lote
            lot_id = lot.id

            # Guardar la relación entre el lote y la propiedad
            property_lot = PropertyLot(
                lot_id=lot_id,        # Usamos el id del lote recién creado
                property_id=property_id
            )

            # Agregar la relación entre el lote y la propiedad
            self.db.add(property_lot)
            self.db.commit()  # Realizar la transacción para la relación

            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {
                        "title": "Creacion de lotes",
                        "message": f"Se ha creado el lote satisfactoriamente"
                    }
                }
            )

        except Exception as e:
            self.db.rollback()  # Revertir cambios si ocurre algún error
            # print(str(e))
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Creacion de lotes",
                        "message": f"Error al crear el lote, Contacta al administrador"
                    }
                }
            )        

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

    async def edit_lot(self, lot_id: int, name: str, longitude: float, latitude: float, extension: float, 
                   real_estate_registration_number: int, public_deed: UploadFile = File(None), 
                    freedom_tradition_certificate: UploadFile = File(None)):
        """Editar un lote existente en la base de datos con la posibilidad de actualizar archivos"""

        try:
            # Verificar si el lote existe
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
            
            # Verificar si el número de registro de propiedad es único, pero no en el lote actual
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

            # Actualizar la información del lote
            lot.name = name
            lot.longitude = longitude
            lot.latitude = latitude
            lot.extension = extension
            lot.real_estate_registration_number = real_estate_registration_number
            
            # Si los archivos se proporcionan, los actualizamos
            if public_deed:
                public_deed_path = await self.save_file(public_deed, "uploads/files_lots/")
                lot.public_deed = public_deed_path
            
            if freedom_tradition_certificate:
                freedom_tradition_certificate_path = await self.save_file(freedom_tradition_certificate, "uploads/files_lots/")
                lot.freedom_tradition_certificate = freedom_tradition_certificate_path

            # Guardar los cambios en la base de datos
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
            self.db.rollback()  # Revertir cambios si ocurre algún error
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
            # validar si existe la propiedad
            existing_user = self.db.query(User).filter(User.id == user_id).first()
            if not existing_user:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "data": {
                            "title": "Edición de predios",
                            "message": f"El usuario a relacionar no existe en el sistema"
                        }
                    }
                )
            
            # Verificar si el predio existe
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
            
            # Verificar si el número de registro de propiedad es único, pero no en el predio actual
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
            
            # Si los archivos se proporcionan, los actualizamos
            if public_deed:
                public_deed_path = await self.save_file(public_deed, "uploads/files_properties/")
                property.public_deed = public_deed_path
            
            if freedom_tradition_certificate:
                freedom_tradition_certificate_path = await self.save_file(freedom_tradition_certificate, "uploads/files_properties/")
                property.freedom_tradition_certificate = freedom_tradition_certificate_path

            # Guardar los cambios en la base de datos
            self.db.commit()
            self.db.refresh(property)


            # validar si el predio cambio de usuario o dueno
            property_user = self.db.query(PropertyUser).filter(PropertyUser.property_id == property_id).first()

            if property_user and property_user.user_id != user_id:
                # si cambio de usuario, actualizar el usuario actual en el predio
                property_user.user_id = user_id

                # Guardar los cambios en la base de datos
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
            self.db.rollback()  # Revertir cambios si ocurre algún error
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