from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import date

# Esquemas para ColorPalette
class ColorPaletteBase(BaseModel):
    primary_color: str = Field(..., min_length=1, max_length=45)
    secondary_color: str = Field(..., min_length=1, max_length=45)
    tertiary_color: str = Field(..., min_length=1, max_length=45)
    primary_text: str = Field(..., min_length=1, max_length=45)
    secondary_text: str = Field(..., min_length=1, max_length=45)
    background_color: str = Field(..., min_length=1, max_length=45)
    border_color: str = Field(..., min_length=1, max_length=45)

class ColorPaletteCreate(ColorPaletteBase):
    pass

class ColorPaletteResponse(ColorPaletteBase):
    id: int
    
    class Config:
        orm_mode = True

# Esquemas para Company
class CompanyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    nit: int = Field(..., gt=0)
    email: str = Field(...)
    phone: str = Field(..., min_length=1, max_length=45)
    country: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    address: str = Field(..., min_length=1, max_length=45)
    color_palette_id: int

class CompanyCreate(CompanyBase):
    pass

class CompanyResponse(CompanyBase):
    id: int
    color_palette: ColorPaletteResponse
    
    class Config:
        orm_mode = True


class DigitalCertificateBase(BaseModel):
    serial_number: int = Field(..., gt=0)
    start_date: date
    expiration_date: date
    attached: str = Field("", min_length=0, max_length=255)
    nit: int = Field(..., gt=0)  
    
    @validator('expiration_date')
    def expiration_date_must_be_after_start_date(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('La fecha de expiración debe ser posterior a la fecha de inicio')
        return v

class DigitalCertificateCreate(DigitalCertificateBase):
    pass

class DigitalCertificateResponse(DigitalCertificateBase):
    id: int
    
    class Config:
        orm_mode = True

# Para TypeCrop
class TypeCropBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    harvest_time: int = Field(..., gt=0)
    payment_interval_id: int = Field(..., gt=0)

class TypeCropCreate(TypeCropBase):
    pass

class TypeCropResponse(TypeCropBase):
    id: int
    class Config:
        orm_mode = True

# Para PaymentInterval
class PaymentIntervalBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    interval_days: int = Field(..., gt=0)

class PaymentIntervalCreate(PaymentIntervalBase):
    pass

class PaymentIntervalResponse(PaymentIntervalBase):
    id: int
    class Config:
        orm_mode = True


# Esquemas para CompanyCertificate
class CompanyCertificateBase(BaseModel):
    company_id: int
    digital_certificate_id: int

class CompanyCertificateCreate(CompanyCertificateBase):
    pass

class CompanyCertificateResponse(CompanyCertificateBase):
    id: int
    company: CompanyResponse
    digital_certificate: DigitalCertificateResponse
    
    class Config:
        orm_mode = True

# Esquemas para CompanyUser
class CompanyUserBase(BaseModel):
    company_id: int
    user_id: int

class CompanyUserCreate(CompanyUserBase):
    pass

class CompanyUserResponse(CompanyUserBase):
    id: int
    
    class Config:
        orm_mode = True

# Respuestas generales
class SimpleResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None