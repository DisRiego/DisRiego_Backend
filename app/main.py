from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models import Token  # Importa el modelo Token (Pydantic)
from app.schemas import UserBase, UserResponse  # Usamos el modelo Pydantic UserBase para la entrada
from app.auth import AuthService
from app.database import SessionLocal  # Importa la sesión de la base de datos
from datetime import datetime, timedelta

app = FastAPI()

# Inicializa el servicio de autenticación
auth_service = AuthService()

# Crear una sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Ruta de autenticación y emisión de token JWT
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: UserBase, db: Session = Depends(get_db)):
    """Autenticación y emisión de token JWT"""
    user = auth_service.get_user(db, form_data.username)
    print(user.password)
    
    if not user or form_data.password != user.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth_service.access_token_expire_minutes)
    access_token = auth_service.create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: str = Depends(login_for_access_token), db: Session = Depends(get_db)):
    """Ruta protegida para obtener datos del usuario actual"""
    
    # Obtén el usuario de la base de datos usando el servicio de autenticación
    user = auth_service.get_user(db, current_user)

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Devuelve un objeto que se ajusta al modelo Pydantic `UserResponse`
    return UserResponse(id=user.id, username=user.username)