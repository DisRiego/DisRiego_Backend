from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

DATABASE_URL = "postgresql://adminintegrador:Z5CKewnHWLOwW9Nlo7BulaNsZBatSKaS@dpg-cuvnue5ds78s73f7ta3g-a.oregon-postgres.render.com/dis_riego_db"

# Configurar la base de datos
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependencia para obtener la sesión
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
