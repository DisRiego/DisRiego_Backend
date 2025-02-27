from sqlalchemy import Column, Integer, String
from app.database import Base  # Importa Base desde el archivo database.py
from pydantic import BaseModel

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    name = Column(String)


class Token(BaseModel):
    access_token: str
    token_type: str