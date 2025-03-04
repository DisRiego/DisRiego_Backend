from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.auth.auth_service import AuthService
from app.models import User

class PasswordChangeService:
    """Servicio para gestionar el cambio de contraseña"""

    def __init__(self, db: Session):
        self.db = db
        self.auth_service = AuthService()

    def change_password(self, user_id: int, old_password: str, new_password: str, confirm_password: str):
        """Lógica para cambiar la contraseña de un usuario"""

        # Obtener el usuario
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Verificar si la contraseña actual es correcta
        if not self.auth_service.verify_password(old_password, user.password):
            raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")

        # Validar que las contraseñas coincidan
        if new_password != confirm_password:
            raise HTTPException(status_code=400, detail="Las contraseñas no coinciden")

        # Validar que la nueva contraseña cumple con los requisitos
        if len(new_password) < 12 or not any(c.isupper() for c in new_password) or not any(c.islower() for c in new_password) or not any(c.isdigit() for c in new_password):
            raise HTTPException(status_code=400, detail="La nueva contraseña debe incluir al menos 12 caracteres con mayúsculas, minúsculas y números")

        # Hashear la nueva contraseña y guardarla
        user.password = self.auth_service.get_password_hash(new_password)
        self.db.commit()

        return {"message": "Contraseña actualizada correctamente"}
