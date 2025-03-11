import os
import shutil
from sqlalchemy.orm import Session
from app.property_routes.models import Property, Lot, PropertyLot, LotHistory
from fastapi import HTTPException, UploadFile, File
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
                return {
                    "success": False,
                    "data": []
                    }
            return properties
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al obtener los predios: {str(e)}")

    async def create_property(self, name: str, longitude: float, latitude: float, extension: float, 
                        real_estate_registration_number: int, description: str = None, location: str = None,
                        freedom_tradition_certificate: UploadFile = File(...), public_deed: UploadFile = File(...)):
        """Crear un nuevo predio en la base de datos con la carga de archivos"""

        # Validaciones previas
        if not name or longitude is None or latitude is None or extension is None or not real_estate_registration_number:
            raise HTTPException(status_code=400, detail="Faltan campos requeridos.")

        try:
            # Guardar archivos en el servidor
            freedom_tradition_certificate_path = await self.save_file(freedom_tradition_certificate)
            public_deed_path                   = await self.save_file(public_deed)

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


            # Agregar el nuevo predio a la base de datos
            self.db.add(property)
            self.db.commit()
            self.db.refresh(property)

            return {"success": True, "data": {"id": property.id, "name": property.name}}

        except Exception as e:
            self.db.rollback()  # Revertir cambios si ocurre algún error
            raise HTTPException(status_code=500, detail=f"Error al crear el predio: {str(e)}")

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
        try:
            property_lot = PropertyLot(property_id=property_id, lot_id=lot_id)
            self.db.add(property_lot)
            self.db.commit()
            return {"success": True, "data": "Predio y lote asociados correctamente."}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Error al asociar el predio con el lote.")

    # def get_all_properties(self):
    #     try:
    #         properties = self.db.query(Property).all()
    #         return {"success": True, "data": properties}
    #     except Exception as e:
    #         raise HTTPException(status_code=500, detail="Error al obtener los predios.")

# Añadir al archivo app/property_routes/services.py

def disable_lot(self, lot_id: int, user_id: int, details: str = None):
 
    try:
        # Verificar que el lote existe
        lot = self.db.query(Lot).filter(Lot.id == lot_id).first()
        if not lot:
            raise HTTPException(status_code=404, detail="Lote no encontrado")
        
        # Verificar que el lote esté activo
        if not lot.is_active:
            raise HTTPException(status_code=400, detail="El lote ya está inhabilitado")

        # Inhabilitar el lote
        lot.is_active = False
        
        # Registrar la acción en el historial
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
        # Verificar que el lote existe
        lot = self.db.query(Lot).filter(Lot.id == lot_id).first()
        if not lot:
            raise HTTPException(status_code=404, detail="Lote no encontrado")
        
        # Obtener el historial
        history = self.db.query(LotHistory).filter(LotHistory.lot_id == lot_id).order_by(LotHistory.timestamp.desc()).all()
        
        # Convertir a formato JSON
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
