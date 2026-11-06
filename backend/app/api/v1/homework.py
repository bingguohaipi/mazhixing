from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.core.response import ApiResponse, success
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.homework_schema import (
    HomeworkAllowLateRequest,
    HomeworkCreateRequest,
    HomeworkDetail,
    HomeworkListItem,
    HomeworkSubmissionReport,
    HomeworkUpdateRequest,
    StudentHomeworkItem,
)
from app.schemas.submission_schema import TeacherSubmissionDetail
from app.services.homework_service import HomeworkService
from app.services.submission_service import SubmissionService

router = APIRouter(prefix="/homework", tags=["作业管理"])

TeacherUser = Annotated[User, Depends(require_roles(UserRole.TEACHER))]
StudentUser = Annotated[User, Depends(require_roles(UserRole.STUDENT))]


def get_homework_service(db: Annotated[Session, Depends(get_db)]) -> HomeworkService:
    return HomeworkService(db)


@router.get("", response_model=ApiResponse[list[HomeworkListItem]])
def list_homework(
    current_user: TeacherUser,
    service: Annotated[HomeworkService, Depends(get_homework_service)],
    status: str | None = Query(None, description="all|未开始|进行中|已截止|已撤回"),
):
    items = service.list_homework(current_user.id, status)
    return success(items)


@router.post("", response_model=ApiResponse[HomeworkDetail])
def create_homework(
    payload: HomeworkCreateRequest,
    current_user: TeacherUser,
    service: Annotated[HomeworkService, Depends(get_homework_service)],
):
    item = service.create_homework(current_user.id, payload)
    return success(item, message="作业布置成功，已通知相关班级学生")


@router.get("/my", response_model=ApiResponse[list[StudentHomeworkItem]])
def list_my_homework(
    current_user: StudentUser,
    service: Annotated[HomeworkService, Depends(get_homework_service)],
):
    items = service.list_student_homework(current_user.id)
    return success(items)


@router.get("/{homework_id}/submission-report", response_model=ApiResponse[HomeworkSubmissionReport])
def get_homework_submission_report(
    homework_id: int,
    current_user: TeacherUser,
    service: Annotated[HomeworkService, Depends(get_homework_service)],
):
    report = service.get_submission_report(homework_id, current_user.id)
    return success(report)


@router.get(
    "/{homework_id}/submissions/{submission_id}",
    response_model=ApiResponse[TeacherSubmissionDetail],
)
def get_homework_submission_for_teacher(
    homework_id: int,
    submission_id: int,
    current_user: TeacherUser,
    db: Annotated[Session, Depends(get_db)],
):
    detail = SubmissionService(db).get_submission_for_teacher(
        current_user.id,
        homework_id,
        submission_id,
    )
    return success(detail)


@router.get("/{homework_id}", response_model=ApiResponse[HomeworkDetail])
def get_homework(
    homework_id: int,
    current_user: TeacherUser,
    service: Annotated[HomeworkService, Depends(get_homework_service)],
):
    item = service.get_homework(homework_id, current_user.id)
    return success(item)


@router.put("/{homework_id}", response_model=ApiResponse[HomeworkDetail])
def update_homework(
    homework_id: int,
    payload: HomeworkUpdateRequest,
    current_user: TeacherUser,
    service: Annotated[HomeworkService, Depends(get_homework_service)],
):
    item, students_notified = service.update_homework(homework_id, current_user.id, payload)
    message = "作业更新成功，已通知相关学生" if students_notified else "作业更新成功"
    return success(item, message=message)


@router.post("/my/{homework_id}/ack-update", response_model=ApiResponse[None])
def acknowledge_homework_update(
    homework_id: int,
    current_user: StudentUser,
    service: Annotated[HomeworkService, Depends(get_homework_service)],
):
    service.acknowledge_homework_update(current_user.id, homework_id)
    return success(message="已确认作业更新")


@router.post("/{homework_id}/withdraw", response_model=ApiResponse[HomeworkDetail])
def withdraw_homework(
    homework_id: int,
    current_user: TeacherUser,
    service: Annotated[HomeworkService, Depends(get_homework_service)],
):
    item = service.withdraw_homework(homework_id, current_user.id)
    return success(item, message="作业已撤回，已通知相关班级学生")


@router.delete("/{homework_id}", response_model=ApiResponse[None])
def delete_homework(
    homework_id: int,
    current_user: TeacherUser,
    service: Annotated[HomeworkService, Depends(get_homework_service)],
):
    service.delete_homework(homework_id, current_user.id)
    return success(message="作业已删除，已通知相关班级学生")


@router.patch("/{homework_id}/allow-late", response_model=ApiResponse[HomeworkDetail])
def set_allow_late(
    homework_id: int,
    payload: HomeworkAllowLateRequest,
    current_user: TeacherUser,
    service: Annotated[HomeworkService, Depends(get_homework_service)],
):
    item, notified = service.set_allow_late(homework_id, current_user.id, payload)
    message = "补交设置已更新，已通知相关班级学生" if notified else "补交设置已更新"
    return success(item, message=message)
