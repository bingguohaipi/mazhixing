from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.deps import require_roles
from app.core.response import ApiResponse, success
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.student_profile_schema import StudentNicknameUpdateRequest, StudentProfileResponse
from app.services.student_profile_service import StudentProfileService
from sqlalchemy.orm import Session

router = APIRouter(prefix="/students/me", tags=["学生个人中心"])

StudentUser = Annotated[User, Depends(require_roles(UserRole.STUDENT))]


def get_service(db: Annotated[Session, Depends(get_db)]) -> StudentProfileService:
    return StudentProfileService(db)


@router.get("/profile", response_model=ApiResponse[StudentProfileResponse])
def get_my_profile(
    current_user: StudentUser,
    service: Annotated[StudentProfileService, Depends(get_service)],
):
    return success(service.get_profile(current_user.id))


@router.patch("/nickname", response_model=ApiResponse[StudentProfileResponse])
def update_my_nickname(
    payload: StudentNicknameUpdateRequest,
    current_user: StudentUser,
    service: Annotated[StudentProfileService, Depends(get_service)],
):
    return success(service.update_nickname(current_user.id, payload), message="昵称已更新")


@router.post("/avatar", response_model=ApiResponse[StudentProfileResponse])
async def upload_my_avatar(
    current_user: StudentUser,
    service: Annotated[StudentProfileService, Depends(get_service)],
    file: UploadFile = File(...),
):
    content_type = file.content_type or ""
    content = await file.read()
    profile = await service.update_avatar(current_user.id, content_type, content)
    return success(profile, message="头像已更新")
