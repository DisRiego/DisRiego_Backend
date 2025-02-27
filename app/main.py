from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from sqlalchemy import text 

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Infraestructura lista, backend en Render funcionando"}

@app.get("/check-db")
def check_db():
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))  # Usa text() para la consulta
        return {"message": "Conexión con la base de datos exitosa"}
    except Exception as e:
        return {"error": str(e)}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@app.get("/users")
def check_db(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT * FROM users"))  # Usa text() para la consulta
        users = result.fetchall()
        return {"users": [dict(row._mapping) for row in users]}
    except Exception as e:
        return {"error": str(e)}