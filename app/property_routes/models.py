from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey, Float, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
import datetime

class Property(Base):
    __tablename__ = 'property'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    extension = Column(Float, nullable=False)
    real_estate_registration_number = Column(Integer, nullable=False)
    public_deed = Column(String, nullable=True)
    freedom_tradition_certificate = Column(String, nullable=True)
    # description = Column(Text, nullable=True)
    # location = Column(String, nullable=True)

    # Nuevas columnas para almacenar las rutas de los archivos
    # file1_path = Column(String, nullable=True)
    # file2_path = Column(String, nullable=True)

    def __repr__(self):
        return f"<Property(id={self.id}, name={self.name})>"

class Lot(Base):
    __tablename__ = 'lot'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    extension = Column(Float, nullable=False)
    real_estate_registration_number = Column(Integer, nullable=False)
    public_deed = Column(String, nullable=True)
    freedom_tradition_certificate = Column(String, nullable=True)


    # Relación con las propiedades (relación muchos a muchos)
    # properties = relationship("Property", secondary="property_lot", back_populates="lots")
    history = relationship("LotHistory", back_populates="lot")

    def __repr__(self):
        return f"<Lot(id={self.id}, name={self.name})>"
    
class LotHistory(Base):
    __tablename__ = 'lot_history'

    id = Column(Integer, primary_key=True, index=True)
    lot_id = Column(Integer, ForeignKey('lot.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False) 
    action = Column(String, nullable=False)  # 'disable', 'enable', etc.
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relaciones
    lot = relationship("Lot", back_populates="history")
    user = relationship("User")  # Relación con el usuario que realizó la acción
class PropertyLot(Base):
    __tablename__ = 'property_lot'

    property_id = Column(Integer, ForeignKey('property.id'), primary_key=True)
    lot_id = Column(Integer, ForeignKey('lot.id'), primary_key=True)

class PropertyUser(Base):
    __tablename__ = 'user_property'

    property_id = Column(Integer, ForeignKey('property.id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)