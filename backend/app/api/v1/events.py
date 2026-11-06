from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.deps import get_client_ip, get_optional_current_user
from app.core.rate_limit import check_rate_limit
from app.core.rate_limit_deps import rate_limit_by_ip
from app.core.response import ApiResponse, success
from app.db.session import get_db
from app.models.user import User
from app.schemas.event_schema import EventTrackRequest
from app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["埋点"])


def get_event_service(db: Annotated[Session, Depends(get_db)]) -> EventService:
    return EventService(db)


@router.post("/track", response_model=ApiResponse[dict])
def track_events(
    payload: EventTrackRequest,
    request: Request,
    service: Annotated[EventService, Depends(get_event_service)],
    _: Annotated[None, Depends(rate_limit_by_ip("events:track", 120, 60))],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
):
    """接收前端批量埋点（可匿名）；按 IP 限流防刷库。"""
    ip = get_client_ip(
        request.headers.get("x-forwarded-for"),
        request.headers.get("x-real-ip") or (request.client.host if request.client else None),
    )
    if ip:
        check_rate_limit(f"events:track:ip:{ip}:burst", 30, 10)
    count = service.track_events(current_user, payload.events, ip)
    return success({"tracked": count})
