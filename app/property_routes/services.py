import os
from fastapi import HTTPException, UploadFile, File, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.property_routes.models import Property, Lot, PropertyLot
from sqlalchemy.orm import Session
from app.property_routes.schemas import PropertyCreate, PropertyResponse

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
                        public_deed: UploadFile = File(...), freedom_tradition_certificate: UploadFile = File(...)):
        """Crear un nuevo predio en la base de datos con la carga de archivos"""
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
            # raise HTTPException(status_code=400, detail="Faltan los archivos requeridos para el predio.")

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

    def create_lot(self, name: str, area: float, property_id: int):
        """Crear un nuevo lote asociado a un predio"""
        try:
            lot = Lot(name=name, area=area, property_id=property_id)
            self.db.add(lot)
            self.db.commit()
            self.db.refresh(lot)
            return {"success": True, "data": lot}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Error al crear el lote.")

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