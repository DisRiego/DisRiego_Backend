<<<<<<< HEAD
import time
import logging
from fastapi import Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from app.database import get_db
from app.authentication.models import RevokedToken
from jose import jwt, JWTError
from app.auth import AuthService

# **Middleware de Logging para registrar peticiones**
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Generar un ID único por cada petición
        request_id = request.headers.get("X-Request-ID", str(time.time()))
        logging.info(f"Request [{request_id}]: {request.method} {request.url}")

        # Procesar la solicitud
        response = await call_next(request)

        process_time = time.time() - start_time
        logging.info(f"Response [{request_id}]: {response.status_code} ({process_time:.2f}s)")

        return response
class TokenRevocationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        db: Session = next(get_db())
        auth_service = AuthService()
        
        token = request.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            token = token.split(" ")[1]  # Extraer el token real
            
            try:
                payload = jwt.decode(token, auth_service.secret_key, algorithms=["HS256"])
                revoked = db.query(RevokedToken).filter(RevokedToken.token == token).first()

                if revoked and not revoked.has_expired():
                    raise HTTPException(status_code=401, detail="Token revocado. Inicia sesión nuevamente.")
            except JWTError:
                pass  # Si el token es inválido, simplemente deja que el endpoint lo maneje.

        return await call_next(request)

# Función para agregar todos los middlewares
def setup_middlewares(app):
    """Agrega los middlewares a la aplicación FastAPI."""

    # Protección contra Host Header Attacks
    # app.add_middleware(TrustedHostMiddleware, allowed_hosts=["example.com", "*.example.com", "localhost", "127.0.0.1"])

    # Configuración CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Cambiar a dominios específicos en producción
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )


    # Middleware de Logging
    app.add_middleware(LoggingMiddleware)
=======
import time
import logging
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# **Middleware de Logging para registrar peticiones**
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Generar un ID único por cada petición
        request_id = request.headers.get("X-Request-ID", str(time.time()))
        logging.info(f"Request [{request_id}]: {request.method} {request.url}")

        # Procesar la solicitud
        response = await call_next(request)

        process_time = time.time() - start_time
        logging.info(f"Response [{request_id}]: {response.status_code} ({process_time:.2f}s)")

        return response

# Función para agregar todos los middlewares
def setup_middlewares(app):
    """Agrega los middlewares a la aplicación FastAPI."""

    # Protección contra Host Header Attacks
    # app.add_middleware(TrustedHostMiddleware, allowed_hosts=["example.com", "*.example.com", "localhost", "127.0.0.1"])

    # Configuración CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Cambiar a dominios específicos en producción
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )

    # Middleware de Logging
    app.add_middleware(LoggingMiddleware)
>>>>>>> 85ba576672a43d67308c7a717e47036c7f936755
