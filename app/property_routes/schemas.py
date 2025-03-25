from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

# Modelo de predio para recibir datos de entrada
class PropertyCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    longitude: float = Field(..., gt=-180, lt=180)  # Longitude debe estar en el rango de -180 a 180
    latitude: float = Field(..., gt=-90, lt=90)  # Latitude debe estar en el rango de -90 a 90
    extension: float = Field(..., gt=0)  # Área de la propiedad en metros cuadrados
    real_estate_registration_number: int = Field(..., gt=0)
    description: Optional[str] = None
    location: Optional[str] = None
    public_deed: str  # Ruta al archivo
    freedom_tradition_certificate: str  # Ruta al archivo

    class Config:
        orm_mode = True  # Permite convertir el modelo de Pydantic a un objeto de SQLAlchemy

# Modelo de respuesta para un predio
class PropertyResponse(BaseModel):
    id: int
    name: str
    longitude: float
    latitude: float
    extension: float
    real_estate_registration_number: int
    public_deed: str
    freedom_tradition_certificate: str
    description: Optional[str] = None
    location: Optional[str] = None

    class Config:
        orm_mode = True

class LotEditFields(BaseModel):
    payment_interval: Optional[int] = Field(None, description="Intervalo de pago en número entero")
    type_crop_id: Optional[int] = Field(None, description="ID del tipo de cultivo")
    planting_date: Optional[date] = Field(None, description="Fecha de siembra (YYYY-MM-DD)")
    estimated_harvest_date: Optional[date] = Field(None, description="Fecha estimada de cosecha (YYYY-MM-DD)")

    class Config:
        orm_mode = True
