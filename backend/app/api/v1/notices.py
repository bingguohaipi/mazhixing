from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.core.response import ApiResponse, success
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.notice_schema import NoticeCreateRequest, NoticeFeedItem, NoticeListItem, NoticeMarkReadRequest
from app.services.notice_service import NoticeService

router = APIRouter(prefix="/notices", tags=["通知公告"])

TeacherUser = Annotated[User, Depends(require_roles(UserRole.TEACHER))]
StudentUser = Annotated[User, Depends(require_roles(UserRole.STUDENT))]
ParentUser = Annotated[User, Depends(require_roles(UserRole.PARENT))]


def get_notice_service(db: Annotated[Session, Depends(get_db)]) -> NoticeService:
    return NoticeService(db)


@router.get("", response_model=ApiResponse[list[NoticeListItem]])
def list_teacher_notices(
    current_user: TeacherUser,
    service: Annotated[NoticeService, Depends(get_notice_service)],
):
    items = service.list_teacher_notices(current_user.id)
    return success(items)


@router.post("", response_model=ApiResponse[NoticeListItem])
def create_notice(
    payload: NoticeCreateRequest,
    current_user: TeacherUser,
    service: Annotated[NoticeService, Depends(get_notice_service)],
):
    item = service.create_notice(current_user.id, payload)
    return success(item, message="通知发布成功")


@router.delete("/{notice_id}", response_model=ApiResponse[None])
def delete_notice(
    notice_id: int,
    current_user: TeacherUser,
    service: Annotated[NoticeService, Depends(get_notice_service)],
):
    service.delete_notice(notice_id, current_user.id)
    return success(message="通知已删除")


@router.get("/feed", response_model=ApiResponse[list[NoticeFeedItem]])
def list_notice_feed(
    current_user: Annotated[User, Depends(require_roles(UserRole.STUDENT, UserRole.PARENT))],
    service: Annotated[NoticeService, Depends(get_notice_service)],
):
    if current_user.role == UserRole.STUDENT:
        items = service.list_feed_for_student(current_user.id)
    else:
        items = service.list_feed_for_parent(current_user.id)
    return success(items)


@router.post("/read", response_model=ApiResponse[None])
def mark_notice_read(
    payload: NoticeMarkReadRequest,
    current_user: Annotated[User, Depends(require_roles(UserRole.STUDENT, UserRole.PARENT))],
    service: Annotated[NoticeService, Depends(get_notice_service)],
):
    service.mark_notice_read(current_user.id, payload.notice_id)
    return success(message="已标记为已读")
