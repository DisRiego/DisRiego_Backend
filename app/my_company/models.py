from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
from app.roles.models import Vars
from app.users.models import User


class ColorPalette(Base):
    """Modelo para almacenar paletas de colores"""
    __tablename__ = "color_palette"

    id = Column(Integer, primary_key=True, index=True)
    primary_color = Column(String(45), nullable=False)
    secondary_color = Column(String(45), nullable=False)
    tertiary_color = Column(String(45), nullable=False)
    primary_text = Column(String(45), nullable=False)
    secondary_text = Column(String(45), nullable=False)
    background_color = Column(String(45), nullable=False)
    border_color = Column(String(45), nullable=False)

    def __repr__(self):
        return f"<ColorPalette(id={self.id}, primary_color={self.primary_color})>"

class Company(Base):
    """Modelo para almacenar información de la empresa"""
    __tablename__ = "company"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)            
    nit = Column(Integer, nullable=False)                   
    email = Column(String(50), nullable=False)              
    phone = Column(String(30), nullable=False)              
    country = Column(String(128), nullable=False)          
    state = Column(String(128), nullable=False)             
    city = Column(String(128), nullable=False)              
    address = Column(String(128), nullable=False)          
    logo = Column(String(255), nullable=False)              
    color_palette_id = Column(Integer, ForeignKey("color_palette.id"), nullable=False) 

    
    color_palette = relationship("ColorPalette")

    def __repr__(self):
        return f"<Company(id={self.id}, name={self.name}, nit={self.nit})>"

class CompanyCertificate(Base):
    """Modelo para almacenar certificados de la empresa"""
    __tablename__ = "company_certificate"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("company.id"), nullable=False)
    digital_certificate_id = Column(Integer, ForeignKey("digital_certificate.id"), nullable=False)
    
    # Relaciones
    company = relationship("Company")
    digital_certificate = relationship("DigitalCertificate")
    
    def __repr__(self):
        return f"<CompanyCertificate(id={self.id}, company_id={self.company_id})>"

class DigitalCertificate(Base):
    """Modelo para almacenar certificados digitales"""
    __tablename__ = "digital_certificate"

    id = Column(Integer, primary_key=True, index=True)
    serial_number = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=False)
    attached = Column(String(255), nullable=False)
    nit = Column(Integer, nullable=False)  
    # Columna para el estado del certificado (22: Activo, 23: Inactivo)
    status_id = Column(Integer, ForeignKey("vars.id"), nullable=False, default=22)

    # Relación para acceder al nombre del estado sin llamar directamente a Vars en los servicios
    status = relationship("Vars", foreign_keys=[status_id])

    def __repr__(self):
        return f"<DigitalCertificate(id={self.id}, serial_number={self.serial_number})>"
    
    def has_expired(self):
        """Método para verificar si el certificado ha expirado"""
        return datetime.now().date() > self.expiration_date

class TypeCrop(Base):
    __tablename__ = "type_crop"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    harvest_time = Column(Integer, nullable=False)
    payment_interval_id = Column(Integer, ForeignKey("payment_interval.id"), nullable=False)
    # Nueva columna que relaciona con la tabla vars:
    state_id = Column(Integer, ForeignKey("vars.id"), nullable=False, default=20)
    
    # Relaciones
    payment_interval = relationship("PaymentInterval")
    state = relationship("Vars")
    lots = relationship("Lot", back_populates="type_crop")

    def __repr__(self):
        return f"<TypeCrop(id={self.id}, name={self.name}, state_id={self.state_id})>"

class PaymentInterval(Base):
    """Modelo para almacenar intervalos de pago"""
    __tablename__ = "payment_interval"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)         
    interval_days = Column(Integer, nullable=False)      
    
    def __repr__(self):
        return f"<PaymentInterval(id={self.id}, name={self.name})>"

class CompanyUser(Base):
    """Modelo para la relación entre empresas y usuarios"""
    __tablename__ = "company_user"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("company.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    company = relationship("Company")
    
    def __repr__(self):
        return f"<CompanyUser(company_id={self.company_id}, user_id={self.user_id})>"
