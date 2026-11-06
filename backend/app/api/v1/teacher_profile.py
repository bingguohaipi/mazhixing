from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.core.response import ApiResponse, success
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.role_profile_schema import NicknameUpdateRequest, TeacherProfileResponse
from app.services.teacher_profile_service import TeacherProfileService

router = APIRouter(prefix="/teachers/me", tags=["教师个人中心"])

TeacherUser = Annotated[User, Depends(require_roles(UserRole.TEACHER))]


def get_service(db: Annotated[Session, Depends(get_db)]) -> TeacherProfileService:
    return TeacherProfileService(db)


@router.get("/profile", response_model=ApiResponse[TeacherProfileResponse])
def get_my_profile(
    current_user: TeacherUser,
    service: Annotated[TeacherProfileService, Depends(get_service)],
):
    return success(service.get_profile(current_user.id))


@router.patch("/nickname", response_model=ApiResponse[TeacherProfileResponse])
def update_my_nickname(
    payload: NicknameUpdateRequest,
    current_user: TeacherUser,
    service: Annotated[TeacherProfileService, Depends(get_service)],
):
    return success(service.update_nickname(current_user.id, payload), message="昵称已更新")
