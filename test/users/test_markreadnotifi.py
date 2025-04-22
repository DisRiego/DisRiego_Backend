import pytest
from datetime import datetime
from app.users.models import Notification
from app.users.services import UserService
from app.users.schemas import NotificationCreate
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

@pytest.fixture
def db_session():
    from app.database import SessionLocal
    db: Session = SessionLocal()
    created_notifications = []
    yield db, created_notifications
    for notif_id in created_notifications:
        notif = db.query(Notification).filter_by(id=notif_id).first()
        if notif:
            db.delete(notif)
    db.commit()
    db.close()

def test_mark_notifications_as_read_successfully(db_session):
    db, created_notifications = db_session
    service = UserService(db)

    # Creamos una notificación no leída
    notification_data = NotificationCreate(
        user_id=1,
        title="Prueba lectura",
        message="Esta es una prueba",
        type="test"
    )
    result = service.create_notification(notification_data)
    notif_id = result["data"]["id"]
    created_notifications.append(notif_id)

    # Validar que esté sin leer
    assert db.query(Notification).filter_by(id=notif_id, read=False).first() is not None

    # Marcar como leída
    mark_result = service.mark_notifications_as_read(user_id=1, notification_ids=[notif_id])

    assert mark_result["success"] is True
    assert "leídas" in mark_result["message"]

    # Verificar que esté leída
    updated = db.query(Notification).filter_by(id=notif_id).first()
    assert updated.read is True
def test_mark_notifications_as_read_error_500(db_session):
    db, _ = db_session
    service = UserService(db)

    with patch.object(db, "query", side_effect=Exception("fallo simulado")):
        with pytest.raises(HTTPException) as exc:
            service.mark_notifications_as_read(user_id=1, notification_ids=[999])
        
        assert exc.value.status_code == 500
        assert "Error al marcar notificaciones como leídas" in str(exc.value.detail)