import json

from sqlalchemy.orm import Session

from app.models.arena import UserNotification


class UserNotificationService:
    def __init__(self, db: Session):
        self.db = db

    def push(
        self,
        user_id: int,
        event_key: str,
        title: str,
        body: str,
        payload: dict | None = None,
    ) -> UserNotification:
        row = UserNotification(
            user_id=user_id,
            event_key=event_key,
            title=title,
            body=body,
            payload_json=json.dumps(payload, ensure_ascii=False) if payload else None,
        )
        self.db.add(row)
        return row

    def list_for_user(
        self,
        user_id: int,
        page: int,
        page_size: int,
        event_key: str | None = None,
        unread_only: bool = False,
    ) -> tuple[list[UserNotification], int]:
        query = self.db.query(UserNotification).filter(UserNotification.user_id == user_id)
        if event_key:
            query = query.filter(UserNotification.event_key == event_key)
        if unread_only:
            query = query.filter(UserNotification.is_read.is_(False))
        total = query.count()
        rows = (
            query.order_by(UserNotification.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return rows, total

    def mark_read(self, user_id: int, ids: list[int] | None, mark_all: bool) -> int:
        from datetime import datetime, timezone

        query = self.db.query(UserNotification).filter(
            UserNotification.user_id == user_id,
            UserNotification.is_read.is_(False),
        )
        if not mark_all:
            if not ids:
                return 0
            query = query.filter(UserNotification.id.in_(ids))
        rows = query.all()
        now = datetime.now(timezone.utc)
        for row in rows:
            row.is_read = True
            row.read_at = now
        if rows:
            self.db.commit()
        return len(rows)
