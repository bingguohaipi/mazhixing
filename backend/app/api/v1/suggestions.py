import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.core.exceptions import AppException
from app.core.response import ApiResponse, success
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.suggestion_schema import (
    SuggestionCreateRequest,
    SuggestionItem,
    SuggestionListResponse,
    SuggestionRecipient,
    SuggestionRatingRequest,
    SuggestionReplyCreateRequest,
    SuggestionReplyItem,
    SuggestionStatusUpdateRequest,
)
from app.services.suggestion_service import SuggestionService

router = APIRouter(prefix="/suggestions", tags=["建议反馈"])

AuthenticatedUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_roles(UserRole.ADMIN))]

UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads" / "suggestions"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_suggestion_service(db: Annotated[Session, Depends(get_db)]) -> SuggestionService:
    return SuggestionService(db)


@router.get("/recipients", response_model=ApiResponse[list[SuggestionRecipient]])
def list_recipients(
    current_user: AuthenticatedUser,
    service: Annotated[SuggestionService, Depends(get_suggestion_service)],
    context_type: str | None = Query(None),
    context_id: int | None = Query(None),
):
    data = service.list_recipients(current_user, context_type, context_id)
    return success(data)


@router.post("", response_model=ApiResponse[SuggestionItem])
def create_suggestion(
    payload: SuggestionCreateRequest,
    current_user: AuthenticatedUser,
    service: Annotated[SuggestionService, Depends(get_suggestion_service)],
):
    data = service.create(current_user, payload)
    return success(data, message="建议已发送")


@router.get("/inbox", response_model=ApiResponse[SuggestionListResponse])
def list_inbox(
    current_user: AuthenticatedUser,
    service: Annotated[SuggestionService, Depends(get_suggestion_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sender: str | None = Query(None, max_length=64),
    processed: bool | None = Query(None),
):
    data = service.list_inbox(current_user, page, page_size, sender, processed)
    return success(data)


@router.get("/sent", response_model=ApiResponse[SuggestionListResponse])
def list_sent(
    current_user: AuthenticatedUser,
    service: Annotated[SuggestionService, Depends(get_suggestion_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sender: str | None = Query(None, max_length=64),
    processed: bool | None = Query(None),
):
    data = service.list_sent(current_user, page, page_size, sender, processed)
    return success(data)


@router.get("/unread-count", response_model=ApiResponse[dict])
def unread_count(
    current_user: AuthenticatedUser,
    service: Annotated[SuggestionService, Depends(get_suggestion_service)],
):
    count = service.unread_count(current_user.id)
    return success({"count": count})


@router.get("/{suggestion_id}", response_model=ApiResponse[SuggestionItem])
def get_suggestion(
    suggestion_id: int,
    current_user: AuthenticatedUser,
    service: Annotated[SuggestionService, Depends(get_suggestion_service)],
):
    data = service.get_detail(current_user, suggestion_id)
    return success(data)


@router.post("/{suggestion_id}/replies", response_model=ApiResponse[SuggestionReplyItem])
def create_reply(
    suggestion_id: int,
    payload: SuggestionReplyCreateRequest,
    current_user: AuthenticatedUser,
    service: Annotated[SuggestionService, Depends(get_suggestion_service)],
):
    data = service.add_reply(current_user, suggestion_id, payload)
    return success(data, message="回复已发送")


@router.post("/{suggestion_id}/rating", response_model=ApiResponse[SuggestionItem])
def rate_suggestion(
    suggestion_id: int,
    payload: SuggestionRatingRequest,
    current_user: AuthenticatedUser,
    service: Annotated[SuggestionService, Depends(get_suggestion_service)],
):
    data = service.rate_satisfaction(current_user, suggestion_id, payload)
    return success(data, message="评分已提交")


@router.patch("/{suggestion_id}/status", response_model=ApiResponse[SuggestionItem])
def update_status(
    suggestion_id: int,
    payload: SuggestionStatusUpdateRequest,
    current_user: AuthenticatedUser,
    service: Annotated[SuggestionService, Depends(get_suggestion_service)],
):
    data = service.update_status(current_user, suggestion_id, payload)
    return success(data, message="状态已更新")


@router.get("/admin/all", response_model=ApiResponse[SuggestionListResponse])
def admin_list_suggestions(
    current_user: AdminUser,
    service: Annotated[SuggestionService, Depends(get_suggestion_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    sender: str | None = Query(None, max_length=64),
    processed: bool | None = Query(None),
):
    data = service.admin_list(page, page_size, status, sender, processed)
    return success(data)


@router.post("/upload-image", response_model=ApiResponse[dict])
async def upload_image(
    current_user: AuthenticatedUser,
    file: UploadFile = File(...),
):
    if file.content_type not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
        raise AppException(400, "仅支持 JPG/PNG/WebP/GIF 图片")
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:
        raise AppException(400, "图片不能超过 2MB")
    suffix = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }[file.content_type]
    filename = f"{uuid.uuid4().hex}{suffix}"
    target = UPLOAD_DIR / filename
    target.write_bytes(content)
    url = f"/api/v1/media/suggestions/{filename}"
    return success({"url": url})
