from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models import User
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os
from typing import Optional

class AuthService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
        self.secret_key = os.getenv("SECRET_KEY", "defaultsecretkey")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=self.access_token_expire_minutes))
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def get_user(self, db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.email == username).first()
