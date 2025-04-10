import pytest
from sqlalchemy.orm import Session
from app.users.services import UserService
from app.users.models import Notification
from app.database import SessionLocal
from datetime import datetime
from unittest.mock import patch
from fastapi import HTTPException

# ✅ Fixture de sesión de base de datos que limpia solo las notificaciones creadas
@pytest.fixture
def db_session():
    db: Session = SessionLocal()
    created_notifications = []

    yield db, created_notifications

    for notification_id in created_notifications:
        notification = db.query(Notification).filter_by(id=notification_id).first()
        if notification:
            db.delete(notification)
    db.commit()
    db.close()

@pytest.mark.asyncio
async def test_get_unread_notification_count(db_session):
    db, created_notifications = db_session
    user_id = 1  # ID del administrador

    service = UserService(db)

    # Crear notificaciones no leídas para el administrador
    for i in range(2):
        notif = Notification(
            user_id=user_id,
            title=f"Notificación de prueba {i + 1}",
            message="Esta es una notificación de prueba.",
            type="test",
            read=False,
            created_at=datetime.utcnow()
        )
        db.add(notif)
        db.commit()
        created_notifications.append(notif.id)

    # Ejecutar servicio
    result = service.get_unread_notification_count(user_id=user_id)

    # Validaciones
    assert result["success"] is True
    assert isinstance(result["count"], int)
    assert result["count"] >= 2  # Debe incluir al menos las dos que se acaban de crear

@pytest.mark.asyncio
async def test_get_unread_notification_count_error(db_session):
    db, _ = db_session
    service = UserService(db)

    # Simulamos un error forzando que el query lance una excepción
    with patch.object(db, "query", side_effect=Exception("Simulated DB failure")):
        with pytest.raises(HTTPException) as exc_info:
            service.get_unread_notification_count(user_id=1)

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail["success"] is False
        assert "Error al obtener conteo de notificaciones" in exc_info.value.detail["data"]["title"]
        assert "Simulated DB failure" in exc_info.value.detail["data"]["message"]