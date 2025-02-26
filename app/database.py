from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://adminintegrador:Z5CKewnHWLOwW9Nlo7BulaNsZBatSKaS@dpg-cuvnue5ds78s73f7ta3g-a.oregon-postgres.render.com/dis_riego_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
