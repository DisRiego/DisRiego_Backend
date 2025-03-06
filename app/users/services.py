from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.users.models import User  # Asegúrate de que el modelo User esté correctamente importado
from app.database import Base
from fastapi import HTTPException

class UserService:
    """Clase para gestionar la creación y obtención de usuarios"""

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_username(self, username: str):
        """Obtener un usuario por su nombre de usuario (email)"""
        try:
            user = self.db.query(User).filter(User.email == username).first()
            if not user:
                raise HTTPException(status_code=404, detail={
                    "success": False,
                    "data": "Usuario no encontrado."
                })
            return user
        except Exception as e:
            raise HTTPException(status_code=500, detail={
                "success": False,
                "data": f"Error al obtener el usuario: {str(e)}"
            })

    def create_user(
        self, 
        email: str, 
        password: str, 
        name: str, 
        email_status: Optional[bool] = None,
        type_document_id: Optional[int] = None,
        document_number: Optional[int] = None,
        date_issuance_document: Optional[datetime] = None,
        type_person_id: Optional[int] = None,
        birthday: Optional[datetime] = None,
        gender_id: Optional[int] = None,
        status_id: Optional[int] = None,
        first_last_name: Optional[str] = None,
        second_last_name: Optional[str] = None,
        address: Optional[str] = None,
        profile_picture: Optional[str] = None,
        phone: Optional[str] = None
    ):
        """Crear un nuevo usuario con todos los campos"""
        try:
            db_user = User(
                email=email,
                password=password,
                name=name,
                email_status=email_status,
                type_document_id=type_document_id,
                document_number=document_number,
                date_issuance_document=date_issuance_document,
                type_person_id=type_person_id,
                birthday=birthday,
                gender_id=gender_id,
                status_id=status_id,
                first_last_name=first_last_name,
                second_last_name=second_last_name,
                address=address,
                profile_picture=profile_picture,
                phone=phone
            )
            
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            return {
                "success": True,
                "data": "Usuario creado correctamente"
            }
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail={
                "success": False,
                "data": f"Error al crear el usuario: {str(e)}"
            })
        
    def update_user(self, user_id, new_address:Optional[str] , new_profile_picture:Optional[str] , new_phone:Optional[str]):
        try:
            db_user = self.db.query(User).filter(User.id == user_id).first()
            if not db_user:
                raise HTTPException(status_code=404, detail={
                     "success": False,
                     "data": "Usuario no encontrando"
                })
                
            if new_address is not None:
                db_user.address = new_address
            if new_profile_picture is not None:
                db_user.profile_picture=new_profile_picture
            if new_phone is not None:
                db_user.phone = new_phone               
                
            self.db.commit()

            self.db.refresh(db_user)
            return{
                "success":True,
                "data": "Usuario Actualizado correctamente"
            }
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail={
                "success": False,
                "data": f"Error al actualizar el usuario: {str(e)}"
            })
