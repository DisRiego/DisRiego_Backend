from fastapi import FastAPI
from app.database import Base, engine
from app.middlewares import setup_middlewares
from app.exceptions import setup_exception_handlers
# Importar los routers de cada módulo
from app.auth.routes import router as auth_router
from app.roles.routes import router as roles_router
from app.password_change.routes import router as password_router

# **Configurar FastAPI**
app = FastAPI(
    title="Distrito de Riego API Gateway - Gestión de Usuario",
    description="API Gateway para gestión de usuarios, roles y permisos en el sistema de riego",
    version="1.0.0"
)

# **Configurar Middlewares**
setup_middlewares(app)

# **Configurar Manejadores de Excepciones**
setup_exception_handlers(app)

# **Registrar Rutas**
app.include_router(auth_router)  # Rutas de autenticación
app.include_router(roles_router)  # Rutas de gestión de roles
app.include_router(password_router)  # Cambio de contraseña

# **Crear tablas si no existen**
Base.metadata.create_all(bind=engine)

# **Endpoint de Salud**
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "message": "API funcionando correctamente"}
