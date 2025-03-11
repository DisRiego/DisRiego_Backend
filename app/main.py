from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from app.database import Base, engine
from app.roles.routes import router as roles_router
from app.users.routes import router as users_router
from app.auth.routes import router as auth_router
from app.property_routes.routes import router as property_lot_router
from app.middlewares import setup_middlewares
from app.exceptions import setup_exception_handlers
from app.websockets import notification_manager
from sqlalchemy.orm import Session
from app.database import get_db
from app.users.models import User
import json

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
app.include_router(users_router)
app.include_router(auth_router)
app.include_router(property_lot_router)

# **Crear tablas si no existen**
Base.metadata.create_all(bind=engine)

# **Endpoint de Salud**
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "message": "API funcionando correctamente"}

# **WebSocket para notificaciones**
@app.websocket("/ws/notifications/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: Session = Depends(get_db)):
    # Verificar si el usuario existe
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        await websocket.close(code=1008)  # Policy Violation
        return
    
    # Aceptar la conexión
    await notification_manager.connect(websocket, user_id)
    
    try:
        # Enviar mensaje de bienvenida
        await websocket.send_json({
            "type": "connection_established",
            "message": "Conexión establecida correctamente"
        })
        
        # Escuchar mensajes del cliente
        while True:
            data = await websocket.receive_text()
            # Procesar comandos del cliente (por ejemplo, marcar como leída una notificación)
            try:
                message = json.loads(data)
                if message.get("action") == "mark_as_read" and "notification_id" in message:
                    # Aquí podrías implementar la lógica para marcar como leída
                    # Usando el servicio apropiado
                    pass
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        notification_manager.disconnect(websocket)
