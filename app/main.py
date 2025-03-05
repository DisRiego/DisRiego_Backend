from fastapi import FastAPI, HTTPException, Request, Depends , Body
from app.database import Base, engine,    get_db
from app.roles.routes import router as roles_router
from app.middlewares import setup_middlewares
from app.exceptions import setup_exception_handlers

from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware

# **Configurar FastAPI**
app = FastAPI( 
    title="Distrito de Riego API Gateway - Gestion de usuario",
    description="API Gateway para gestión de usuarios, roles y permisos en el sistema de riego",
    version="1.0.0"
)

# **Configurar Middlewares**
setup_middlewares(app)

# **Configurar Manejadores de Excepciones**
setup_exception_handlers(app)

# **Registrar Rutas**
app.include_router(roles_router)

# **Crear tablas si no existen**
Base.metadata.create_all(bind=engine)

        


#temporal
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
#termina temporal



# **Endpoint de Salud**
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "message": "API funcionando correctamente"}
