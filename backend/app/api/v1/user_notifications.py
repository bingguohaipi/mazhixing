from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.response import ApiResponse, success
from app.db.session import get_db
from app.models.user import User
from app.schemas.user_notification_schema import (
    UserNotificationItem,
    UserNotificationListResponse,
    UserNotificationsReadRequest,
)
from app.services.user_notification_service import UserNotificationService

router = APIRouter(prefix="/user-notifications", tags=["用户通知"])

AuthenticatedUser = Annotated[User, Depends(get_current_user)]


def get_service(db: Annotated[Session, Depends(get_db)]) -> UserNotificationService:
    return UserNotificationService(db)


@router.get("", response_model=ApiResponse[UserNotificationListResponse])
def list_user_notifications(
    current_user: AuthenticatedUser,
    service: Annotated[UserNotificationService, Depends(get_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    event_key: str | None = Query(None, max_length=64),
    unread_only: bool = Query(False),
):
    rows, total = service.list_for_user(
        current_user.id,
        page,
        page_size,
        event_key=event_key,
        unread_only=unread_only,
    )
    return success(
        UserNotificationListResponse(
            items=[
                UserNotificationItem(
                    id=row.id,
                    event_key=row.event_key,
                    title=row.title,
                    body=row.body,
                    is_read=row.is_read,
                    created_at=row.created_at,
                    payload_json=row.payload_json,
                )
                for row in rows
            ],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.post("/read", response_model=ApiResponse[dict])
def mark_notifications_read(
    payload: UserNotificationsReadRequest,
    current_user: AuthenticatedUser,
    service: Annotated[UserNotificationService, Depends(get_service)],
):
    count = service.mark_read(current_user.id, payload.ids, payload.all)
    return success({"marked": count})
