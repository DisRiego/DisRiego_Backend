import os
import uuid
from datetime import datetime
from fastapi import HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.my_company.models import (
    Company, ColorPalette, DigitalCertificate, 
    CompanyCertificate, TypeCrop, PaymentInterval, CompanyUser
)
from app.my_company import schemas

class CompanyService:
    """Servicio para la gestión de la información de la empresa"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_company_info(self):
        """Obtener la información de la empresa"""
        try:
            company = self.db.query(Company).first()
            if not company:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "message": "No hay información de empresa registrada",
                        "data": None
                    }
                )
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Información de empresa obtenida correctamente",
                    "data": jsonable_encoder(company)
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Error al obtener información de empresa: {str(e)}",
                    "data": None
                }
            )
    
    async def create_company_info(self, company_data, logo_file):
        """Crear o actualizar la información de la empresa"""
        try:
            # Verificar si ya existe info de empresa
            existing_company = self.db.query(Company).first()
            
            # Verificar que la paleta de colores exista
            color_palette = self.db.query(ColorPalette).filter(
                ColorPalette.id == company_data.color_palette_id
            ).first()
            
            if not color_palette:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "message": "La paleta de colores especificada no existe",
                        "data": None
                    }
                )
            
            if existing_company:
                # Actualizar la empresa existente
                existing_company.name = company_data.name
                existing_company.nit = company_data.nit
                existing_company.email = company_data.email
                existing_company.phone = company_data.phone
                existing_company.country = company_data.country
                existing_company.state = company_data.state
                existing_company.city = company_data.city
                existing_company.address = company_data.address
                existing_company.color_palette_id = company_data.color_palette_id
                
                self.db.commit()
                self.db.refresh(existing_company)
                
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "message": "Información de empresa actualizada correctamente",
                        "data": jsonable_encoder(existing_company)
                    }
                )
            else:
                # Crear nueva entrada de empresa
                new_company = Company(
                    name=company_data.name,
                    nit=company_data.nit,
                    email=company_data.email,
                    phone=company_data.phone,
                    country=company_data.country,
                    state=company_data.state,
                    city=company_data.city,
                    address=company_data.address,
                    color_palette_id=company_data.color_palette_id
                )
                
                self.db.add(new_company)
                self.db.commit()
                self.db.refresh(new_company)
                
                return JSONResponse(
                    status_code=201,
                    content={
                        "success": True,
                        "message": "Información de empresa creada correctamente",
                        "data": jsonable_encoder(new_company)
                    }
                )
        except IntegrityError as e:
            self.db.rollback()
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": f"Error de integridad de datos: {str(e)}",
                    "data": None
                }
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Error al crear/actualizar información de empresa: {str(e)}",
                    "data": None
                }
            )
    
    async def save_file(self, file: UploadFile, directory: str = "uploads/") -> str:
        """Guardar un archivo en el servidor con un nombre único"""
        try:
            # Crear el directorio si no existe
            if not os.path.exists(directory):
                os.makedirs(directory)

            # Generar un nombre único para el archivo
            unique_filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
            
            # Ruta completa del archivo
            file_path = os.path.join(directory, unique_filename)
            
            # Guardar el archivo
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())
            
            return file_path
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al guardar el archivo: {str(e)}")

class ColorPaletteService:
    """Servicio para la gestión de paletas de colores"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_color_palettes(self):
        """Obtener todas las paletas de colores"""
        try:
            palettes = self.db.query(ColorPalette).all()
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Paletas de colores obtenidas correctamente",
                    "data": jsonable_encoder(palettes)
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Error al obtener paletas de colores: {str(e)}",
                    "data": None
                }
            )
    
    def get_color_palette(self, palette_id: int):
        """Obtener una paleta de colores por ID"""
        try:
            palette = self.db.query(ColorPalette).filter(ColorPalette.id == palette_id).first()
            if not palette:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "message": "Paleta de colores no encontrada",
                        "data": None
                    }
                )
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Paleta de colores obtenida correctamente",
                    "data": jsonable_encoder(palette)
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Error al obtener paleta de colores: {str(e)}",
                    "data": None
                }
            )
    
    def create_color_palette(self, palette_data: schemas.ColorPaletteCreate):
        """Crear una nueva paleta de colores"""
        try:
            new_palette = ColorPalette(
                primary_color=palette_data.primary_color,
                secondary_color=palette_data.secondary_color,
                tertiary_color=palette_data.tertiary_color,
                primary_text=palette_data.primary_text,
                secondary_text=palette_data.secondary_text,
                background_color=palette_data.background_color,
                border_color=palette_data.border_color
            )
            
            self.db.add(new_palette)
            self.db.commit()
            self.db.refresh(new_palette)
            
            return JSONResponse(
                status_code=201,
                content={
                    "success": True,
                    "message": "Paleta de colores creada correctamente",
                    "data": jsonable_encoder(new_palette)
                }
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Error al crear paleta de colores: {str(e)}",
                    "data": None
                }
            )
    
    def update_color_palette(self, palette_id: int, palette_data: schemas.ColorPaletteCreate):
        """Actualizar una paleta de colores existente"""
        try:
            palette = self.db.query(ColorPalette).filter(ColorPalette.id == palette_id).first()
            if not palette:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "message": "Paleta de colores no encontrada",
                        "data": None
                    }
                )
            
            palette.primary_color = palette_data.primary_color
            palette.secondary_color = palette_data.secondary_color
            palette.tertiary_color = palette_data.tertiary_color
            palette.primary_text = palette_data.primary_text
            palette.secondary_text = palette_data.secondary_text
            palette.background_color = palette_data.background_color
            palette.border_color = palette_data.border_color
            
            self.db.commit()
            self.db.refresh(palette)
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Paleta de colores actualizada correctamente",
                    "data": jsonable_encoder(palette)
                }
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Error al actualizar paleta de colores: {str(e)}",
                    "data": None
                }
            )
    
    def delete_color_palette(self, palette_id: int):
        """Eliminar una paleta de colores"""
        try:
            palette = self.db.query(ColorPalette).filter(ColorPalette.id == palette_id).first()
            if not palette:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "message": "Paleta de colores no encontrada",
                        "data": None
                    }
                )
            
            # Verificar si hay empresas que usan esta paleta
            companies_using_palette = self.db.query(Company).filter(
                Company.color_palette_id == palette_id
            ).count()
            
            if companies_using_palette > 0:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "message": f"No se puede eliminar la paleta porque está siendo usada por {companies_using_palette} empresa(s)",
                        "data": None
                    }
                )
            
            self.db.delete(palette)
            self.db.commit()
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Paleta de colores eliminada correctamente",
                    "data": None
                }
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Error al eliminar paleta de colores: {str(e)}",
                    "data": None
                }
            )

class CertificateService:
    """Servicio para la gestión de certificados digitales"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_certificates(self):
        """Obtener todos los certificados digitales"""
        try:
            certificates = self.db.query(DigitalCertificate).all()
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Certificados obtenidos correctamente",
                    "data": jsonable_encoder(certificates)
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Error al obtener certificados: {str(e)}",
                    "data": None
                }
            )
    
    async def get_certificate(self, certificate_id: int):
        """Obtener un certificado digital por su ID"""
        try:
            certificate = self.db.query(DigitalCertificate).filter(DigitalCertificate.id == certificate_id).first()
            if not certificate:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "message": "Certificado no encontrado",
                        "data": None
                    }
                )
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Certificado obtenido correctamente",
                    "data": jsonable_encoder(certificate)
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Error al obtener certificado: {str(e)}",
                    "data": None
                }
            )
    
    async def create_certificate(self, certificate_data, certificate_file: UploadFile):
        """Crear un nuevo certificado digital"""
        try:
            # Guardar el archivo de certificado
            attached_path = await self.save_file(certificate_file, "uploads/certificates/")
            
            # Crear el certificado
            new_certificate = DigitalCertificate(
                serial_number=certificate_data.serial_number,
                start_date=certificate_data.start_date,
                expiration_date=certificate_data.expiration_date,
                attached=attached_path,
                digital_certificateid=certificate_data.digital_certificateid
            )
            
            self.db.add(new_certificate)
            self.db.commit()
            self.db.refresh(new_certificate)
            
            return JSONResponse(
                status_code=201,
                content={
                    "success": True,
                    "message": "Certificado creado correctamente",
                    "data": jsonable_encoder(new_certificate)
                }
            )
        except IntegrityError as e:
            self.db.rollback()
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": f"Error de integridad de datos: {str(e)}",
                    "data": None
                }
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Error al crear el certificado: {str(e)}",
                    "data": None
                }
            )
    
    async def update_certificate(self, certificate_id: int, certificate_data, certificate_file: UploadFile = None):
        """Actualizar un certificado digital existente"""
        try:
            certificate = self.db.query(DigitalCertificate).filter(DigitalCertificate.id == certificate_id).first()
            if not certificate:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "message": "Certificado no encontrado",
                        "data": None
                    }
                )
            
            # Actualizar los datos del certificado
            certificate.serial_number = certificate_data.serial_number
            certificate.start_date = certificate_data.start_date
            certificate.expiration_date = certificate_data.expiration_date
            certificate.digital_certificateid = certificate_data.digital_certificateid
            
            # Si se proporciona un nuevo archivo, actualizar la ruta
            if certificate_file:
                attached_path = await self.save_file(certificate_file, "uploads/certificates/")
                certificate.attached = attached_path
            
            self.db.commit()
            self.db.refresh(certificate)
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Certificado actualizado correctamente",
                    "data": jsonable_encoder(certificate)
                }
            )
        except IntegrityError as e:
            self.db.rollback()
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": f"Error de integridad de datos: {str(e)}",
                    "data": None
                }
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Error al actualizar el certificado: {str(e)}",
                    "data": None
                }
            )
    
    async def delete_certificate(self, certificate_id: int):
        """Eliminar un certificado digital"""
        try:
            certificate = self.db.query(DigitalCertificate).filter(DigitalCertificate.id == certificate_id).first()
            if not certificate:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "message": "Certificado no encontrado",
                        "data": None
                    }
                )
            
            # Verificar si hay relaciones con compañías
            company_certificates = self.db.query(CompanyCertificate).filter(
                CompanyCertificate.digital_certificate_id == certificate_id
            ).all()
            
            # Eliminar primero las relaciones
            for company_cert in company_certificates:
                self.db.delete(company_cert)
            
            # Luego eliminar el certificado
            self.db.delete(certificate)
            self.db.commit()
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Certificado eliminado correctamente",
                    "data": None
                }
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Error al eliminar el certificado: {str(e)}",
                    "data": None
                }
            )
    
    async def save_file(self, file: UploadFile, directory: str = "uploads/") -> str:
        """Guardar un archivo en el servidor con un nombre único"""
        try:
            # Crear el directorio si no existe
            if not os.path.exists(directory):
                os.makedirs(directory)

            # Generar un nombre único para el archivo
            unique_filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
            
            # Ruta completa del archivo
            file_path = os.path.join(directory, unique_filename)
            
            # Guardar el archivo
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())
            
            return file_path
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al guardar el archivo: {str(e)}")

class TypeCropService:
    """Servicio para gestionar tipos de cultivo"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_types(self):
        """Obtener todos los tipos de cultivo"""
        try:
            types = self.db.query(TypeCrop).all()
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Tipos de cultivo obtenidos correctamente",
                    "data": jsonable_encoder(types)
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Error al obtener tipos de cultivo: {str(e)}",
                    "data": None
                }
            )
    
    def get_type(self, type_id: int):
        """Obtener un tipo de cultivo por ID"""
        try:
            type_crop = self.db.query(TypeCrop).filter(TypeCrop.id == type_id).first()
            if not type_crop:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "message": "Tipo de cultivo no encontrado",
                        "data": None
                    }
                )
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Tipo de cultivo obtenido correctamente",
                    "data": jsonable_encoder(type_crop)
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Error al obtener tipo de cultivo: {str(e)}",
                    "data": None
                }
            )
    
    def create_type(self, type_data: schemas.TypeCropCreate):
        """Crear un nuevo tipo de cultivo"""
        try:
            new_type = TypeCrop(
                name=type_data.name
            )
            
            self.db.add(new_type)
            self.db.commit()
            self.db.refresh(new_type)
            
            return JSONResponse(
                status_code=201,
                content={
                    "success": True,
                    "message": "Tipo de cultivo creado correctamente",
                    "data": jsonable_encoder(new_type)
                }
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Error al crear tipo de cultivo: {str(e)}",
                    "data": None
                }
            )
    
    def update_type(self, type_id: int, type_data: schemas.TypeCropCreate):
        """Actualizar un tipo de cultivo"""
        try:
            type_crop = self.db.query(TypeCrop).filter(TypeCrop.id == type_id).first()
            if not type_crop:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "message": "Tipo de cultivo no encontrado",
                        "data": None
                    }
                )
            
            type_crop.name = type_data.name
            
            self.db.commit()
            self.db.refresh(type_crop)
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Tipo de cultivo actualizado correctamente",
                    "data": jsonable_encoder(type_crop)
                }
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Error al actualizar tipo de cultivo: {str(e)}",
                    "data": None
                }
            )
    
    def delete_type(self, type_id: int):
        """Eliminar un tipo de cultivo"""
        try:
            type_crop = self.db.query(TypeCrop).filter(TypeCrop.id == type_id).first()
            if not type_crop:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "message": "Tipo de cultivo no encontrado",
                        "data": None
                    }
                )
            
            self.db.delete(type_crop)
            self.db.commit()
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Tipo de cultivo eliminado correctamente",
                    "data": None
                }
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Error al eliminar tipo de cultivo: {str(e)}",
                    "data": None
                }
            )

class PaymentIntervalService:
    """Servicio para intervalos de pago"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_intervals(self):
        """Obtener todos los intervalos de pago"""
        try:
            intervals = self.db.query(PaymentInterval).all()
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Intervalos de pago obtenidos correctamente",
                    "data": jsonable_encoder(intervals)
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Error al obtener intervalos de pago: {str(e)}",
                    "data": None
                }
            )
    
    def get_interval(self, interval_id: int):
        """Obtener un intervalo de pago por ID"""
        try:
            interval = self.db.query(PaymentInterval).filter(PaymentInterval.id == interval_id).first()
            if not interval:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "message": "Intervalo de pago no encontrado",
                        "data": None
                    }
                )
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Intervalo de pago obtenido correctamente",
                    "data": jsonable_encoder(interval)
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Error al obtener intervalo de pago: {str(e)}",
                    "data": None
                }
            )
    
    def create_interval(self, interval_data: schemas.PaymentIntervalCreate):
        """Crear un nuevo intervalo de pago"""
        try:
            new_interval = PaymentInterval(
                name=interval_data.name,
                description=interval_data.description
            )
            
            self.db.add(new_interval)
            self.db.commit()
            self.db.refresh(new_interval)
            
            return JSONResponse(
                status_code=201,
                content={
                    "success": True,
                    "message": "Intervalo de pago creado correctamente",
                    "data": jsonable_encoder(new_interval)
                }
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Error al crear intervalo de pago: {str(e)}",
                    "data": None
                }
            )
    
    def update_interval(self, interval_id: int, interval_data: schemas.PaymentIntervalCreate):
        """Actualizar un intervalo de pago"""
        try:
            interval = self.db.query(PaymentInterval).filter(PaymentInterval.id == interval_id).first()
            if not interval:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "message": "Intervalo de pago no encontrado",
                        "data": None
                    }
                )
            
            interval.name = interval_data.name
            interval.description = interval_data.description
            
            self.db.commit()
            self.db.refresh(interval)
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Intervalo de pago actualizado correctamente",
                    "data": jsonable_encoder(interval)
                }
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Error al actualizar intervalo de pago: {str(e)}",
                    "data": None
                }
            )
    
    def delete_interval(self, interval_id: int):
        """Eliminar un intervalo de pago"""
        try:
            interval = self.db.query(PaymentInterval).filter(PaymentInterval.id == interval_id).first()
            if not interval:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "message": "Intervalo de pago no encontrado",
                        "data": None
                    }
                )
            
            self.db.delete(interval)
            self.db.commit()
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Intervalo de pago eliminado correctamente",
                    "data": None
                }
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Error al eliminar intervalo de pago: {str(e)}",
                    "data": None
                }
            )