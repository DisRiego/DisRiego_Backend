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
from app.firebase_config import bucket
import logging



class BaseService:
    """Clase base para servicios con funcionalidades comunes utilizando Firebase Storage."""

    async def save_file(self, file: UploadFile, directory: str = "uploads") -> str:
        """Sube un archivo a Firebase Storage y retorna su URL pública.
        
        Se genera un nombre único para evitar conflictos y se sube el contenido del archivo.
        """
        try:
            unique_filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
            blob_path = f"{directory}/{unique_filename}"
            blob = bucket.blob(blob_path)
            file_content = await file.read()
            blob.upload_from_string(file_content, content_type=file.content_type)
            # Hacer el blob público para obtener una URL accesible (opcional)
            blob.make_public()
            return blob.public_url  # Retorna la URL pública del archivo
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al subir el archivo a Firebase: {str(e)}")

    def delete_file(self, file_identifier: str):
        """Elimina un archivo de Firebase Storage.
        
        Se asume que en la base de datos se guarda el blob_path o blob.name.
        """
        try:
            blob = bucket.blob(file_identifier)
            blob.delete()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al eliminar el archivo de Firebase: {str(e)}")
        

class CompanyService(BaseService):
    """Servicio para la gestión de la información de la empresa"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_company_info(self):
        """Obtener la información de la empresa, incluyendo el certificado vigente (número de serie)"""
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
            
            # Convertir la información de la empresa a diccionario
            company_data = jsonable_encoder(company)
            
            # Obtener el certificado vigente (si existe)
            now = datetime.utcnow()
            company_cert = (
                self.db.query(CompanyCertificate)
                .join(DigitalCertificate)
                .filter(
                    CompanyCertificate.company_id == company.id,
                    DigitalCertificate.start_date <= now,
                    DigitalCertificate.expiration_date > now
                )
                .first()
            )
            if company_cert:
                company_data["certificate"] = {
                    "serial_number": company_cert.digital_certificate.serial_number,
                    "digital_certificate_id": company_cert.digital_certificate.id
                }
            else:
                company_data["certificate"] = None

            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Información de empresa obtenida correctamente",
                    "data": company_data
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
    

    async def update_company_logo(self, logo_file: UploadFile):
        """Actualiza únicamente la foto/imagen (logo) de la empresa."""
        # Obtener la empresa registrada
        company = self.db.query(Company).first()
        if not company:
            raise HTTPException(status_code=404, detail="No existe información de empresa registrada")
        
        # Si la empresa tiene un logo anterior, eliminarlo del Firebase Storage
        if company.logo:
            try:
                self.delete_file(company.logo)
            except Exception as e:
                # Puedes optar por continuar si falla la eliminación
                logging.warning(f"No se pudo eliminar el logo anterior: {str(e)}")
        
        # Guardar el nuevo logo en Firebase Storage (el método save_file se actualizó para Firebase)
        new_logo_url = await self.save_file(logo_file, "uploads/logos")
        company.logo = new_logo_url
        self.db.commit()
        self.db.refresh(company)
        
        return {
            "success": True,
            "message": "Logo actualizado correctamente",
            "data": new_logo_url
        }
    
    async def create_company_info(self, company_data, logo_file, digital_certificate_id: int):
        try:
            # Guardar el logo y actualizar company_data.logo
            if logo_file:
                logo_path = await self.save_file(logo_file, "uploads/logos")
                company_data.logo = logo_path
            else:
                company_data.logo = ""
            
            # Verificar si el certificado digital seleccionado está activo
            certificate = self.db.query(DigitalCertificate).filter(DigitalCertificate.id == digital_certificate_id).first()
            if not certificate or certificate.has_expired():
                raise HTTPException(status_code=400, detail="El certificado digital seleccionado no está activo")
            
            # Verificar si ya existe información de la empresa
            existing_company = self.db.query(Company).first()
            
            if existing_company:
                # Actualizar los datos de la empresa existente
                existing_company.name = company_data.name
                existing_company.nit = company_data.nit
                existing_company.email = company_data.email
                existing_company.phone = company_data.phone
                existing_company.country = company_data.country
                existing_company.state = company_data.state
                existing_company.city = company_data.city
                existing_company.address = company_data.address
                existing_company.logo = company_data.logo
                existing_company.color_palette_id = company_data.color_palette_id
                self.db.commit()
                self.db.refresh(existing_company)
                
                # Actualizar o crear la relación del certificado digital
                company_cert = self.db.query(CompanyCertificate).filter(CompanyCertificate.company_id == existing_company.id).first()
                if company_cert:
                    company_cert.digital_certificate_id = digital_certificate_id
                else:
                    new_company_cert = CompanyCertificate(
                        company_id=existing_company.id,
                        digital_certificate_id=digital_certificate_id
                    )
                    self.db.add(new_company_cert)
                self.db.commit()
                
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "message": "Información de empresa actualizada correctamente",
                        "data": jsonable_encoder(existing_company)
                    }
                )
            else:
                # Crear nueva empresa
                new_company = Company(
                    name=company_data.name,
                    nit=company_data.nit,
                    email=company_data.email,
                    phone=company_data.phone,
                    country=company_data.country,
                    state=company_data.state,
                    city=company_data.city,
                    address=company_data.address,
                    logo=company_data.logo,
                    color_palette_id=company_data.color_palette_id
                )
                self.db.add(new_company)
                self.db.commit()
                self.db.refresh(new_company)
                
                # Crear la relación con el certificado digital
                new_company_cert = CompanyCertificate(
                    company_id=new_company.id,
                    digital_certificate_id=digital_certificate_id
                )
                self.db.add(new_company_cert)
                self.db.commit()
                
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

    async def update_basic_info(self, name: str, nit: int, digital_certificate_id: int, logo_file: UploadFile = None):
        # Obtener o crear la empresa
        company = self.db.query(Company).first()
        if not company:
            company = Company()
            self.db.add(company)
            self.db.commit()
            self.db.refresh(company)
        
        # Actualizar campos básicos
        company.name = name
        company.nit = nit

        # Guardar el logo si se proporcionó
        if logo_file:
            logo_path = await self.save_file(logo_file, "uploads/logos/")
            company.logo = logo_path

        # Verificar que el certificado digital exista y esté activo
        certificate = self.db.query(DigitalCertificate).filter(DigitalCertificate.id == digital_certificate_id).first()
        if not certificate or certificate.has_expired():
            raise HTTPException(status_code=400, detail="El certificado digital seleccionado no está activo")

        self.db.commit()
        self.db.refresh(company)
        
        # Actualizar o crear la relación en CompanyCertificate
        company_cert = self.db.query(CompanyCertificate).filter(CompanyCertificate.company_id == company.id).first()
        if company_cert:
            company_cert.digital_certificate_id = digital_certificate_id
        else:
            new_company_cert = CompanyCertificate(
                company_id=company.id,
                digital_certificate_id=digital_certificate_id
            )
            self.db.add(new_company_cert)
        self.db.commit()
        
        return {
            "success": True,
            "message": "Información básica actualizada correctamente",
            "data": company.name  # O la representación completa que desees retornar
        }

    async def update_contact_info(self, email: str, phone: str):
        company = self.db.query(Company).first()
        if not company:
            raise HTTPException(status_code=404, detail="No existe información de empresa registrada")
        
        company.email = email
        company.phone = phone
        self.db.commit()
        self.db.refresh(company)
        
        return {
            "success": True,
            "message": "Información de contacto actualizada correctamente",
            "data": company.email
        }

    async def update_location_info(self, country: str, state: str, city: str, address: str):
        company = self.db.query(Company).first()
        if not company:
            raise HTTPException(status_code=404, detail="No existe información de empresa registrada")
        
        company.country = country
        company.state = state
        company.city = city
        company.address = address
        self.db.commit()
        self.db.refresh(company)
        
        return {
            "success": True,
            "message": "Información de ubicación actualizada correctamente",
            "data": company.country
        }


    
    

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

class CertificateService(BaseService):
    """Servicio para la gestión de certificados digitales"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_certificates(self):
        """Obtener todos los certificados digitales incluyendo el nombre del estado"""
        try:
            certificates = self.db.query(DigitalCertificate).all()
            certificates_list = []
            for certificate in certificates:
                cert_data = jsonable_encoder(certificate)
                # Usamos la relación para obtener el nombre del estado
                cert_data["nombre_estado"] = certificate.status.name if certificate.status else None
                certificates_list.append(cert_data)
                
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Certificados obtenidos correctamente",
                    "data": certificates_list
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
        
    
    def update_certificate_status(self, certificate_id: int, new_status: int):
        """
        Actualiza el estado de un certificado digital.
        Los valores válidos para new_status son 22 (Activo) y 23 (Inactivo).
        Devuelve la información del certificado, incluyendo el nombre del estado.
        """
        if new_status not in (22, 23):
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "El estado debe ser 22 (Activo) o 23 (Inactivo)",
                    "data": None
                }
            )
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
            certificate.status_id = new_status
            self.db.commit()
            self.db.refresh(certificate)

            cert_data = jsonable_encoder(certificate)
            # Accedemos al nombre del estado a través de la relación
            cert_data["nombre_estado"] = certificate.status.name if certificate.status else None

            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Estado del certificado actualizado correctamente",
                    "data": cert_data
                }
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Error al actualizar el estado del certificado: {str(e)}",
                    "data": None
                }
            )
    async def get_certificate(self, certificate_id: int):
        """Obtener un certificado digital por su ID, incluyendo el nombre del estado"""
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
            # Utilizamos la relación 'status' para obtener el nombre del estado
            cert_data = jsonable_encoder(certificate)
            cert_data["nombre_estado"] = certificate.status.name if certificate.status else None

            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Certificado obtenido correctamente",
                    "data": cert_data
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
            # Guardar el archivo y obtener la ruta real
            attached_path = await self.save_file(certificate_file, "uploads/certificates/")
            
            # Crear el objeto final usando la ruta real en 'attached'
            new_certificate = DigitalCertificate(
                serial_number=certificate_data.serial_number,
                start_date=certificate_data.start_date,
                expiration_date=certificate_data.expiration_date,
                attached=attached_path,
                nit=certificate_data.nit
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
            certificate.nit = certificate_data.nit
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
    

class TypeCropService:
    """Servicio para gestionar tipos de cultivo"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def update_state(self, type_id: int, new_state: int):
        """
        Actualiza el estado de un tipo de cultivo.
        Se espera que new_state sea 20 (activo) o 21 (inactivo).
        """
        if new_state not in (20, 21):
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "El estado debe ser 20 (activo) o 21 (inactivo)",
                    "data": None
                }
            )
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
            type_crop.state_id = new_state
            self.db.commit()
            self.db.refresh(type_crop)
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Estado del tipo de cultivo actualizado correctamente",
                    "data": jsonable_encoder(type_crop)
                }
            )
        except Exception as e:
            self.db.rollback()
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Error al actualizar el estado del tipo de cultivo: {str(e)}",
                    "data": None
                }
            )
    def get_all_types(self):
        """Obtener todos los tipos de cultivo incluyendo el nombre del estado y del intervalo de pago"""
        try:
            types = self.db.query(TypeCrop).all()
            types_list = []
            for t in types:
                t_data = jsonable_encoder(t)
                t_data["nombre_estado"] = t.state.name if t.state else None
                t_data["nombre_intervalo_pago"] = t.payment_interval.name if t.payment_interval else None
                types_list.append(t_data)
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Tipos de cultivo obtenidos correctamente",
                    "data": types_list
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
        """Obtener un tipo de cultivo por ID con el nombre del estado y del intervalo de pago"""
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
            type_crop_data = jsonable_encoder(type_crop)
            type_crop_data["nombre_estado"] = type_crop.state.name if type_crop.state else None
            type_crop_data["nombre_intervalo_pago"] = type_crop.payment_interval.name if type_crop.payment_interval else None

            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Tipo de cultivo obtenido correctamente",
                    "data": type_crop_data
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
        try:
            interval = self.db.query(PaymentInterval).filter(PaymentInterval.id == type_data.payment_interval_id).first()
            if not interval:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "message": "Intervalo de pago no encontrado",
                        "data": None
                    }
                )
            
            new_type = TypeCrop(
                name=type_data.name,
                harvest_time=type_data.harvest_time,
                payment_interval_id=type_data.payment_interval_id
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
            
            # Verificar que el nuevo payment_interval_id exista
            interval = self.db.query(PaymentInterval).filter(PaymentInterval.id == type_data.payment_interval_id).first()
            if not interval:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "message": "Intervalo de pago no encontrado",
                        "data": None
                    }
                )
            
            type_crop.name = type_data.name
            type_crop.harvest_time = type_data.harvest_time
            type_crop.payment_interval_id = type_data.payment_interval_id
            
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
        try:
            new_interval = PaymentInterval(
                name=interval_data.name,
                interval_days=interval_data.interval_days
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
            interval.interval_days = interval_data.interval_days
            
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