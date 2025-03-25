import os
import uuid
from fastapi import HTTPException, UploadFile, File, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.property_routes.models import Property, Lot, PropertyLot, PropertyUser
from sqlalchemy.orm import Session
from app.property_routes.schemas import PropertyCreate, PropertyResponse
from app.users.models import User
from datetime import date
from app.roles.models import Vars
from app.firebase_config import bucket
from app.my_company.models import TypeCrop, PaymentInterval


class PropertyLotService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_properties(self):
        """Obtener todos los predios, incluyendo el nombre del estado y el número de documento del dueño"""
        try:
            # Se realiza un join: Property -> Vars (para obtener el nombre del estado) y PropertyUser -> User (para el documento)
            results = (
                self.db.query(
                    Property,
                    Vars.name.label("state_name"),
                    User.document_number.label("owner_document_number")
                )
                .join(PropertyUser, Property.id == PropertyUser.property_id)
                .join(User, PropertyUser.user_id == User.id)
                .join(Vars, Property.state == Vars.id)
                .all()
            )
            properties_list = []
            for property_obj, state_name, owner_document_number in results:
                property_dict = jsonable_encoder(property_obj)
                property_dict["state_name"] = state_name
                property_dict["owner_document_number"] = owner_document_number
                properties_list.append(property_dict)

            if not properties_list:
                return JSONResponse(status_code=404, content={"success": False, "data": []})

            return JSONResponse(
                status_code=200,
                content={"success": True, "data": properties_list}
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Predios",
                        "message": f"Error al obtener los predios, contacta al administrador: {str(e)}"
                    }
                }
            )
    def get_lot_by_id(self, lot_id: int):
        """Obtener un lote por su id, incluyendo nombres descriptivos y el id del predio vinculado."""
        try:
            result = (
                self.db.query(
                    Lot,
                    TypeCrop.name.label("nombre_tipo_cultivo"),
                    PaymentInterval.name.label("nombre_intervalo_pago"),
                    Vars.name.label("nombre_estado"),
                    PropertyLot.property_id.label("property_id")
                )
                .outerjoin(TypeCrop, Lot.type_crop_id == TypeCrop.id)
                .outerjoin(PaymentInterval, Lot.payment_interval == PaymentInterval.id)
                .join(Vars, Lot.state == Vars.id)
                .join(PropertyLot, PropertyLot.lot_id == Lot.id)
                .filter(Lot.id == lot_id)
                .first()
            )
            if not result:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": "Lote no encontrado"}
                )
            lot, nombre_tipo_cultivo, nombre_intervalo_pago, nombre_estado, property_id = result
            lot_data = jsonable_encoder(lot)
            lot_data["nombre_tipo_cultivo"] = nombre_tipo_cultivo
            lot_data["nombre_intervalo_pago"] = nombre_intervalo_pago
            lot_data["nombre_estado"] = nombre_estado
            lot_data["property_id"] = property_id

            return JSONResponse(
                status_code=200,
                content={"success": True, "data": lot_data}
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"success": False, "data": f"Error al obtener el lote: {str(e)}"}
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
            self.db.rollback()
            print("Error al crear predio:", e)
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Creacion de predios",
                        "message": f"Error al crear el predio, Contacta al administrador: {str(e)}"
                    }
                }
            )

        

    def update_property_state(self, property_id: int, new_state: bool):
        """
        Actualiza el estado del predio.
        Si se intenta inactivar (new_state == False), se verifica que no tenga lotes asociados activos.
        Se mapea new_state a:
        - True  -> state = 16 (Activo)
        - False -> state = 17 (Inactivo)
        """
        try:
            property_obj = self.db.query(Property).filter(Property.id == property_id).first()
            if not property_obj:
                raise HTTPException(status_code=404, detail="Predio no encontrado.")
            
            # Si se intenta inactivar, verificar que no existan lotes asociados activos (state == 18)
            if new_state is False:
                active_lots = (
                    self.db.query(Lot)
                    .join(PropertyLot, PropertyLot.lot_id == Lot.id)
                    .filter(PropertyLot.property_id == property_id, Lot.state == 18)
                    .all()
                )
                if active_lots:
                    raise HTTPException(
                        status_code=400,
                        detail="No se puede inactivar el predio porque tiene lotes activos."
                    )
            # Mapear el valor booleano a la columna state:
            property_obj.state = 16 if new_state else 17
            self.db.commit()
            self.db.refresh(property_obj)
            return property_obj
        except HTTPException as e:
            raise e
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al actualizar el estado del predio: {str(e)}")

    def update_lot_state(self, lot_id: int, new_state: bool):
        """
        Actualiza el estado del lote.
        Se mapea new_state a:
        - True  -> state = 18 (Activo)
        - False -> state = 19 (Inactivo)
        Además, si se intenta activar (new_state == True), se verifica que el predio asociado esté activo (state == 16).
        """
        try:
            lot_obj = self.db.query(Lot).filter(Lot.id == lot_id).first()
            if not lot_obj:
                raise HTTPException(status_code=404, detail="Lote no encontrado.")
            
            if new_state is True:
                association = self.db.query(PropertyLot).filter(PropertyLot.lot_id == lot_id).first()
                if not association:
                    raise HTTPException(status_code=400, detail="No existe asociación del lote con un predio.")
                property_obj = self.db.query(Property).filter(Property.id == association.property_id).first()
                if not property_obj:
                    raise HTTPException(status_code=400, detail="Predio asociado no encontrado.")
                if property_obj.state != 16:  # El predio debe estar activo (16)
                    raise HTTPException(status_code=400, detail="No se puede activar el lote porque el predio está desactivado.")
            
            lot_obj.state = 18 if new_state else 19
            self.db.commit()
            self.db.refresh(lot_obj)
            return lot_obj
        except HTTPException as e:
            raise e
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al actualizar el estado del lote: {str(e)}")

    def search_user_by_document(self, document_type: int, document_number: str):
        try:
            user = self.db.query(User).filter(
                User.document_number == document_number,
                User.type_document_id == document_type
            ).first()
            if not user:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "data": {
                            "message": "Usuario no encontrado."
                        }
                    }
                )
            
            user_info = {
                "user_id": user.id,
                "name": user.name,
                "first_lastname": user.first_last_name,
                "second_lastname": user.second_last_name
            }
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": user_info
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "message": f"Error al buscar el usuario: {str(e)}"
                    }
                }
            )

    async def save_file(self, file: UploadFile, directory: str = "files/") -> str:
        """Guardar un archivo en Firebase Storage y devolver su URL pública"""
        try:
            # Leer el contenido del archivo
            file_content = await file.read()

            # Generar un nombre único para el archivo usando UUID y conservar la extensión
            unique_filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"

            # Crear el blob en el bucket dentro del directorio deseado
            blob = bucket.blob(f"{directory}/{unique_filename}")

            # Subir el contenido del archivo a Firebase Storage
            blob.upload_from_string(file_content, content_type=file.content_type)

            # (Opcional) Hacer el archivo público para obtener una URL de acceso directo
            blob.make_public()

            # Retornar la URL pública del archivo
            return blob.public_url
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al guardar el archivo en Firebase: {str(e)}")

    async def edit_lot_fields(self, lot_id: int, payment_interval: int, type_crop_id: int, planting_date: date, estimated_harvest_date: date):
        try:
            lot = self.db.query(Lot).filter(Lot.id == lot_id).first()
            if not lot:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "data": {
                            "title": "Edición de lote",
                            "message": "El lote no existe en el sistema"
                        }
                    }
                )

            # Actualizar únicamente los campos editables
            lot.payment_interval = payment_interval
            lot.type_crop_id = type_crop_id
            lot.planting_date = planting_date
            lot.estimated_harvest_date = estimated_harvest_date

            self.db.commit()
            self.db.refresh(lot)

            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {
                        "title": "Edición de lote",
                        "message": "Los campos del lote han sido actualizados satisfactoriamente"
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
        """Obtener todos los lotes de un predio incluyendo los nombres descriptivos"""
        try:
            lots = (
                self.db.query(
                    Lot,
                    TypeCrop.name.label("nombre_tipo_cultivo"),
                    PaymentInterval.name.label("nombre_intervalo_pago"),
                    Vars.name.label("nombre_estado")
                )
                .join(PropertyLot, PropertyLot.lot_id == Lot.id)
                # Usamos outerjoin en caso de que algún lote no tenga asignado tipo de cultivo o intervalo de pago
                .outerjoin(TypeCrop, Lot.type_crop_id == TypeCrop.id)
                .outerjoin(PaymentInterval, Lot.payment_interval == PaymentInterval.id)
                .join(Vars, Lot.state == Vars.id)
                .filter(PropertyLot.property_id == property_id)
                .all()
            )

            if not lots:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "data": []
                    }
                )

            # Convertir resultados a una lista de diccionarios
            results = []
            for lot, nombre_tipo_cultivo, nombre_intervalo_pago, nombre_estado in lots:
                lot_data = jsonable_encoder(lot)
                lot_data["nombre_tipo_cultivo"] = nombre_tipo_cultivo
                lot_data["nombre_intervalo_pago"] = nombre_intervalo_pago
                lot_data["nombre_estado"] = nombre_estado
                results.append(lot_data)

            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": results
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
        """Editar un lote existente en la base de datos con la posibilidad de actualizar archivos opcionales"""
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
            
            # Actualizar la información del lote
            lot.name = name
            lot.longitude = longitude
            lot.latitude = latitude
            lot.extension = extension
            lot.real_estate_registration_number = real_estate_registration_number
            
            # Actualizar archivos si se proporcionan
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
        
    def get_properties_for_user(self, user_id: int):
        """Obtener todos los predios de un usuario"""
        try:
            # Realizar la consulta para obtener todos los predios de un lote
            properties = self.db.query(Property).join(PropertyUser, PropertyUser.property_id == Property.id).filter(PropertyUser.user_id == user_id).all()
            
            if not properties:
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
                    "data": jsonable_encoder(properties)
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
        
    def get_property_by_id(self, property_id: int):
        """Obtener la información de un predio específico por su ID, incluyendo el estado, el documento y el id del dueño."""
        try:
            # Realizamos un join similar a get_all_properties para obtener información adicional,
            # incluyendo el id del dueño (User.id)
            result = (
                self.db.query(
                    Property,
                    Vars.name.label("state_name"),
                    User.document_number.label("owner_document_number"),
                    User.id.label("owner_id")
                )
                .join(PropertyUser, Property.id == PropertyUser.property_id)
                .join(User, PropertyUser.user_id == User.id)
                .join(Vars, Property.state == Vars.id)
                .filter(Property.id == property_id)
                .first()
            )
            if not result:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "data": "Predio no encontrado"}
                )
            property_obj, state_name, owner_document_number, owner_id = result
            property_dict = jsonable_encoder(property_obj)
            property_dict["state_name"] = state_name
            property_dict["owner_document_number"] = owner_document_number
            property_dict["owner_id"] = owner_id

            return JSONResponse(
                status_code=200,
                content={"success": True, "data": property_dict}
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"success": False, "data": f"Error al obtener la información del predio: {str(e)}"}
            )
