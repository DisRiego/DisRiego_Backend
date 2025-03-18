
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class DisableLotRequest(BaseModel):
    details: Optional[str] = None

class HistoryEntry(BaseModel):
    id: int
    action: str
    details: Optional[str] = None
    timestamp: datetime
    user: dict

    class Config:
        from_attributes = True

class LotHistoryResponse(BaseModel):
    success: bool
    data: List[HistoryEntry]

class DisableLotResponse(BaseModel):
    success: bool
    data: dict

    class Config:
        from_attributes = True



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

