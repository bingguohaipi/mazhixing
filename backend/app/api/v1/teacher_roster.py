from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.core.response import ApiResponse, success
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.roster_schema import (
    RosterBatchCreateRequest,
    RosterBatchCreateResponse,
    RosterListResponse,
    RosterStudentItem,
    RosterStudentUpdateRequest,
)
from app.services.teacher_roster_service import TeacherRosterService

router = APIRouter(prefix="/teacher/roster", tags=["学生名单"])

TeacherUser = Annotated[User, Depends(require_roles(UserRole.TEACHER))]


def get_roster_service(db: Annotated[Session, Depends(get_db)]) -> TeacherRosterService:
    return TeacherRosterService(db)


@router.get("", response_model=ApiResponse[RosterListResponse])
def list_roster(
    current_user: TeacherUser,
    service: Annotated[TeacherRosterService, Depends(get_roster_service)],
    keyword: str | None = Query(None, max_length=64),
    class_id: int | None = Query(None),
):
    data = service.list_roster(current_user.id, keyword, class_id)
    return success(data)


@router.put("/{student_id}", response_model=ApiResponse[RosterStudentItem])
def update_roster_student(
    student_id: int,
    payload: RosterStudentUpdateRequest,
    current_user: TeacherUser,
    service: Annotated[TeacherRosterService, Depends(get_roster_service)],
):
    data = service.update_student(current_user.id, student_id, payload)
    return success(data, message="学生信息已更新")


@router.post("/batch", response_model=ApiResponse[RosterBatchCreateResponse])
def batch_create(
    payload: RosterBatchCreateRequest,
    current_user: TeacherUser,
    service: Annotated[TeacherRosterService, Depends(get_roster_service)],
):
    data = service.batch_create(current_user.id, payload.names, payload.year)
    return success(data, message="学生已批量创建")
