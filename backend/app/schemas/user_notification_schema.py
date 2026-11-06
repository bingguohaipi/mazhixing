from datetime import datetime

from pydantic import BaseModel


class UserNotificationItem(BaseModel):
    id: int
    event_key: str
    title: str
    body: str
    is_read: bool
    created_at: datetime
    payload_json: str | None = None


class UserNotificationListResponse(BaseModel):
    items: list[UserNotificationItem]
    total: int
    page: int
    page_size: int


class UserNotificationsReadRequest(BaseModel):
    ids: list[int] | None = None
    all: bool = False
