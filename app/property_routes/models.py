from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey, Float, Text , Boolean
from sqlalchemy.orm import relationship
from app.database import Base

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
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    extension = Column(Float, nullable=False)
    real_estate_registration_number = Column(Integer, nullable=False)
    public_deed = Column(String, nullable=True)
    freedom_tradition_certificate = Column(String, nullable=True)
    
    # Nuevos campos
    payment_interval = Column(Integer, nullable=True)
    type_crop_id = Column(Integer, ForeignKey('type_crop.id'), nullable=True)
    planting_date = Column(Date, nullable=True)
    estimated_harvest_date = Column(Date, nullable=True)
    state = Column("State", Boolean, nullable=True)

    # Relación con TypeCrop
    type_crop = relationship("TypeCrop", back_populates="lots")

    def __repr__(self):
        return f"<Lot(id={self.id}, name={self.name})>"

class PropertyLot(Base):
    __tablename__ = 'property_lot'

    property_id = Column(Integer, ForeignKey('property.id'), primary_key=True)
    lot_id = Column(Integer, ForeignKey('lot.id'), primary_key=True)

class PropertyUser(Base):
    __tablename__ = 'user_property'

    property_id = Column(Integer, ForeignKey('property.id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)