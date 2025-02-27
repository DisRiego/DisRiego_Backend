from fastapi import FastAPI
from sqlalchemy.orm import Session
from app.database import SessionLocal

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Infraestructura lista, backend en Render funcionando"}

@app.get("/check-db")
def check_db():
    try:
        db = SessionLocal()
        db.execute("SELECT 1")  # Ejecutar una consulta simple
        return {"message": "Conexión con la base de datos exitosa"}
    except Exception as e:
        return {"error": str(e)}