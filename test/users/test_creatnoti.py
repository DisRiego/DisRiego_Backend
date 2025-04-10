import pytest
from datetime import datetime
from app.users.services import UserService
from app.users.schemas import NotificationCreate
from app.users.models import Notification
from app.database import SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException


# ✅ Fixture de sesión de base de datos que limpia solo lo creado
@pytest.fixture
def db_session():
    db: Session = SessionLocal()
    created_notifications = []

    yield db, created_notifications

    # Limpiar solo las notificaciones creadas por esta prueba
    for notification_id in created_notifications:
        notification = db.query(Notification).filter_by(id=notification_id).first()
        if notification:
            db.delete(notification)
    db.commit()
    db.close()


# ✅ Prueba para crear una notificación correctamente
def test_create_notification_successfully(db_session):
    db, created_notifications = db_session
    service = UserService(db)

    test_notification = NotificationCreate(
        user_id=1,
        title="Notificación de prueba",
        message="Este es un mensaje de prueba para verificar la creación",
        type="test"
    )

    result = service.create_notification(test_notification)

    assert result["success"] is True
    assert "data" in result
    assert "id" in result["data"]
    assert isinstance(result["data"]["id"], int)

    created_notifications.append(result["data"]["id"])

    stored = db.query(Notification).filter_by(id=result["data"]["id"]).first()
    assert stored is not None
    assert stored.title == test_notification.title
    assert stored.message == test_notification.message
    assert stored.type == test_notification.type
    assert stored.user_id == test_notification.user_id
    assert stored.read is False
    assert isinstance(stored.created_at, datetime)


# ⚠️ Prueba que fuerza un error 500 simulando fallo interno
def test_create_notification_internal_error(monkeypatch, db_session):
    db, _ = db_session
    service = UserService(db)

    test_notification = NotificationCreate(
        user_id=1,
        title="Debe fallar",
        message="Esta notificación debería fallar",
        type="test"
    )

    # Forzamos que la llamada a db.add lance una excepción
    def raise_error(*args, **kwargs):
        raise SQLAlchemyError("Error simulado en db.add")

    monkeypatch.setattr(db, "add", raise_error)

    with pytest.raises(HTTPException) as exc_info:
        service.create_notification(test_notification)

    exc = exc_info.value
    assert exc.status_code == 500
    assert "Error al crear notificación" in str(exc.detail)
