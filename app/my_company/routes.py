from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.my_company import schemas, services
from app.my_company.models import Company, ColorPalette, DigitalCertificate, TypeCrop, PaymentInterval
from typing import Optional, List
from datetime import date
import logging

router = APIRouter(prefix="/my-company", tags=["Mi Empresa"])

# Rutas para información de la empresa
@router.get("/company", summary="Obtener información de la empresa")
async def get_company_info(
    db: Session = Depends(get_db)
):
    """
    Obtiene la información actual de la empresa.
    """
    company_service = services.CompanyService(db)
    return await company_service.get_company_info()

@router.post("/company", summary="Crear o actualizar información de la empresa")
async def create_update_company_info(
    # Sección de Información Básica
    name: str = Form(...),
    nit: int = Form(...),
    digital_certificate_id: int = Form(...),  
    logo: UploadFile = File(...),
    # Sección de Información de Contacto
    email: str = Form(...),
    phone: str = Form(...),
    # Sección de Ubicación
    country: str = Form(...),
    state: str = Form(...),
    city: str = Form(...),
    address: str = Form(...),
    color_palette_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    Crea o actualiza la información de la empresa, dividiendo el formulario en:
    - Información básica: nombre, NIT, certificado digital activo y logo.
    - Información de contacto: correo y teléfono.
    - Ubicación: país, departamento, ciudad y dirección.
    """
    
    company_data = schemas.CompanyBase(
        name=name,
        nit=nit,
        email=email,
        phone=phone,
        country=country,
        state=state,
        city=city,
        address=address,
        color_palette_id=color_palette_id
    )
    
    company_service = services.CompanyService(db)
   
    return await company_service.create_company_info(company_data, logo, digital_certificate_id)

# Endpoint para información básica: nombre, NIT, certificado digital y logo
@router.patch("/company/basic", summary="Actualizar información básica de la empresa")
async def update_company_basic(
    name: str = Form(...),
    nit: int = Form(...),
    digital_certificate_id: int = Form(...),
    db: Session = Depends(get_db)
):
    company_service = services.CompanyService(db)
    return await company_service.update_basic_info(name, nit, digital_certificate_id)

# Endpoint para información de contacto: correo y teléfono
@router.patch("/company/contact", summary="Actualizar información de contacto de la empresa")
async def update_company_contact(
    email: str = Form(...),
    phone: str = Form(...),
    db: Session = Depends(get_db)
):
    company_service = services.CompanyService(db)
    return await company_service.update_contact_info(email, phone)

# Endpoint para información de ubicación: país, departamento, ciudad y dirección
@router.patch("/company/location", summary="Actualizar información de ubicación de la empresa")
async def update_company_location(
    country: str = Form(...),
    state: str = Form(...),
    city: str = Form(...),
    address: str = Form(...),
    db: Session = Depends(get_db)
):
    company_service = services.CompanyService(db)
    return await company_service.update_location_info(country, state, city, address)

# Rutas para paletas de colores
@router.get("/color-palettes", summary="Listar todas las paletas de colores")
def list_color_palettes(
    db: Session = Depends(get_db)
):
    """
    Lista todas las paletas de colores registradas.
    """
    palette_service = services.ColorPaletteService(db)
    return palette_service.get_color_palettes()

@router.get("/color-palettes/{palette_id}", summary="Obtener una paleta de colores")
def get_color_palette(
    palette_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene detalles de una paleta de colores por su ID.
    """
    palette_service = services.ColorPaletteService(db)
    return palette_service.get_color_palette(palette_id)

@router.post("/color-palettes", summary="Crear una nueva paleta de colores")
def create_color_palette(
    palette: schemas.ColorPaletteCreate,
    db: Session = Depends(get_db)
):
    """
    Crea una nueva paleta de colores.
    """
    palette_service = services.ColorPaletteService(db)
    return palette_service.create_color_palette(palette)

@router.put("/color-palettes/{palette_id}", summary="Actualizar una paleta de colores")
def update_color_palette(
    palette_id: int,
    palette: schemas.ColorPaletteCreate,
    db: Session = Depends(get_db)
):
    """
    Actualiza una paleta de colores existente.
    """
    palette_service = services.ColorPaletteService(db)
    return palette_service.update_color_palette(palette_id, palette)

@router.delete("/color-palettes/{palette_id}", summary="Eliminar una paleta de colores")
def delete_color_palette(
    palette_id: int,
    db: Session = Depends(get_db)
):
    """
    Elimina una paleta de colores.
    """
    palette_service = services.ColorPaletteService(db)
    return palette_service.delete_color_palette(palette_id)

# Rutas para certificados digitales
@router.get("/certificates", summary="Listar todos los certificados digitales")
async def list_certificates(
    db: Session = Depends(get_db)
):
    """
    Lista todos los certificados digitales registrados.
    """
    certificate_service = services.CertificateService(db)
    return await certificate_service.get_certificates()

@router.get("/certificates/{certificate_id}", summary="Obtener un certificado digital")
async def get_certificate(
    certificate_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene detalles de un certificado digital específico por su ID.
    """
    certificate_service = services.CertificateService(db)
    return await certificate_service.get_certificate(certificate_id)


@router.post("/certificates", summary="Crear un nuevo certificado digital")
async def create_certificate(
    serial_number: int = Form(...),
    start_date: date = Form(...),
    expiration_date: date = Form(...),
    nit: int = Form(...),  
    certificate_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo certificado digital.
    """

    certificate_data = schemas.DigitalCertificateCreate(
        serial_number=serial_number,
        start_date=start_date,
        expiration_date=expiration_date,
        attached="",  
        nit=nit
    )
    
    certificate_service = services.CertificateService(db)
    return await certificate_service.create_certificate(certificate_data, certificate_file)

@router.put("/certificates/{certificate_id}", summary="Actualizar un certificado digital")
async def update_certificate(
    certificate_id: int,
    serial_number: int = Form(...),
    start_date: date = Form(...),
    expiration_date: date = Form(...),
    nit: int = Form(...),  
    certificate_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Actualiza un certificado digital existente.
    
    - Si se proporciona un nuevo archivo, se actualiza.
    - Si no se proporciona, se mantiene el archivo existente.
    """
    certificate_data = schemas.DigitalCertificateCreate(
        serial_number=serial_number,
        start_date=start_date,
        expiration_date=expiration_date,
        attached="",  
        nit=nit
    )
    
    certificate_service = services.CertificateService(db)
    return await certificate_service.update_certificate(certificate_id, certificate_data, certificate_file)


@router.delete("/certificates/{certificate_id}", summary="Eliminar un certificado digital")
async def delete_certificate(
    certificate_id: int,
    db: Session = Depends(get_db)
):
    """
    Elimina un certificado digital.
    """
    certificate_service = services.CertificateService(db)
    return await certificate_service.delete_certificate(certificate_id)


@router.patch("/certificates/{certificate_id}/status", response_model=dict, summary="Habilitar/Inhabilitar un certificado digital")
def update_certificate_status(certificate_id: int, new_status: int = Form(...), db: Session = Depends(get_db)):
    """
    Actualiza el estado de un certificado digital.
    new_status debe ser 9 (Activo) o 10 (Inactivo).
    """
    certificate_service = services.CertificateService(db)
    return certificate_service.update_certificate_status(certificate_id, new_status)


# Rutas para tipos de cultivo
@router.get("/type-crops", summary="Listar todos los tipos de cultivo")
def list_type_crops(
    db: Session = Depends(get_db)
):
    """
    Lista todos los tipos de cultivo registrados.
    """
    type_service = services.TypeCropService(db)
    return type_service.get_all_types()

@router.get("/type-crops/{type_id}", summary="Obtener un tipo de cultivo")
def get_type_crop(
    type_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene detalles de un tipo de cultivo específico por su ID.
    """
    type_service = services.TypeCropService(db)
    return type_service.get_type(type_id)

@router.post("/type-crops", summary="Crear un nuevo tipo de cultivo")
def create_type_crop(
    type_crop: schemas.TypeCropCreate,
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo tipo de cultivo.
    """
    type_service = services.TypeCropService(db)
    return type_service.create_type(type_crop)


@router.patch("/type-crops/{type_id}/state", summary="Actualizar estado del tipo de cultivo")
def update_type_crop_state(
    type_id: int,
    new_state: int = Form(...),  # Espera 7 (activo) o 8 (inactivo)
    db: Session = Depends(get_db)
):
    """
    Actualiza el estado (activo/inactivo) de un tipo de cultivo.
    El parámetro new_state debe ser 7 (activo) o 8 (inactivo).
    """
    type_service = services.TypeCropService(db)
    return type_service.update_state(type_id, new_state)


@router.put("/type-crops/{type_id}", summary="Actualizar un tipo de cultivo")
def update_type_crop(
    type_id: int,
    type_crop: schemas.TypeCropCreate,
    db: Session = Depends(get_db)
):
    """
    Actualiza un tipo de cultivo existente.
    """
    type_service = services.TypeCropService(db)
    return type_service.update_type(type_id, type_crop)

@router.delete("/type-crops/{type_id}", summary="Eliminar un tipo de cultivo")
def delete_type_crop(
    type_id: int,
    db: Session = Depends(get_db)
):
    """
    Elimina un tipo de cultivo.
    """
    type_service = services.TypeCropService(db)
    return type_service.delete_type(type_id)

# Rutas para intervalos de pago
@router.get("/payment-intervals", summary="Listar todos los intervalos de pago")
def list_payment_intervals(
    db: Session = Depends(get_db)
):
    """
    Lista todos los intervalos de pago registrados.
    """
    interval_service = services.PaymentIntervalService(db)
    return interval_service.get_all_intervals()

@router.get("/payment-intervals/{interval_id}", summary="Obtener un intervalo de pago")
def get_payment_interval(
    interval_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene detalles de un intervalo de pago específico por su ID.
    """
    interval_service = services.PaymentIntervalService(db)
    return interval_service.get_interval(interval_id)

@router.post("/payment-intervals", summary="Crear un nuevo intervalo de pago")
def create_payment_interval(
    interval: schemas.PaymentIntervalCreate,
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo intervalo de pago.
    """
    interval_service = services.PaymentIntervalService(db)
    return interval_service.create_interval(interval)

@router.put("/payment-intervals/{interval_id}", summary="Actualizar un intervalo de pago")
def update_payment_interval(
    interval_id: int,
    interval: schemas.PaymentIntervalCreate,
    db: Session = Depends(get_db)
):
    """
    Actualiza un intervalo de pago existente.
    """
    interval_service = services.PaymentIntervalService(db)
    return interval_service.update_interval(interval_id, interval)

@router.delete("/payment-intervals/{interval_id}", summary="Eliminar un intervalo de pago")
def delete_payment_interval(
    interval_id: int,
    db: Session = Depends(get_db)
):
    """
    Elimina un intervalo de pago.
    """
    interval_service = services.PaymentIntervalService(db)
    return interval_service.delete_interval(interval_id)

@router.patch("/company/logo", summary="Actualizar foto/imagen de la empresa")
async def update_company_logo(
    logo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    company_service = services.CompanyService(db)
    return await company_service.update_company_logo(logo)
