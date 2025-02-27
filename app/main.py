from fastapi import FastAPI, HTTPException, Request, Depends , Body
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import SessionLocal


app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"message": "Infraestructura lista, backend en Render funcionando"}


@app.post("/login")
def login(data: dict = Body(...), db: Session = Depends(get_db)):
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Se requieren email y password")

    query = text("SELECT name FROM users WHERE email = :email AND password = :password")
    result = db.execute(query, {"email": email, "password": password}).fetchone()

    if not result:
        raise HTTPException(status_code=400, detail="Credenciales inválidas")
    
    return {"message": "Login exitoso", "name": result[0]}