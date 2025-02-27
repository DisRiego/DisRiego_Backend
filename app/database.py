from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv  # Importa load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Recupera la URL de la base de datos desde las variables de entorno
DATABASE_URL = os.getenv("DATABASE_URL")

# Crea el motor de conexión a la base de datos
engine = create_engine(DATABASE_URL)

# Crea la sesión para interactuar con la base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para la declaración de modelos
Base = declarative_base()
