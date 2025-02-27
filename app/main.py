from fastapi import FastAPI, HTTPException, Request, Depends , Body
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import SessionLocal
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas las fuentes (puedes cambiarlo a ['http://localhost:5173'])
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos los encabezados
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"message": "Infraestructura lista, backend en Render funcionando"}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        

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
@app.get("/users")
def check_db(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT * FROM users"))  # Usa text() para la consulta
        users = result.fetchall()
        return {"users": [dict(row._mapping) for row in users]}
    except Exception as e:
        return {"error": str(e)}
