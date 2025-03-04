from sqlalchemy.orm import Session
from app.models import User, PasswordReset

# Función para obtener un usuario por su nombre de usuario
def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.email == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

# Función para crear un nuevo usuario
def create_user(db: Session, username: str, password: str):
    db_user = User(email=username, password=password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Obtener token de reestablecimiento
def get_reset_token(db: Session, token: str):
    return db.query(PasswordReset).filter(PasswordReset.token == token).first()
