from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

<<<<<<< HEAD
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:8520741963@localhost:5432/dis_riego_db")
=======
DATABASE_URL = os.getenv("DATABASE_URL")
>>>>>>> a83a69dee7dc453e51162e8514afd8204121ab4b

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