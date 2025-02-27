from sqlalchemy.orm import Session
from app.models import User

# Función para obtener un usuario por su nombre de usuario
def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.email == username).first()

# Función para crear un nuevo usuario
def create_user(db: Session, username: str, password: str):
    db_user = User(email=username, password=password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
