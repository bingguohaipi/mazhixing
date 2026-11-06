from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.core.response import ApiResponse, success
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.role_profile_schema import NicknameUpdateRequest, ParentProfileResponse
from app.services.parent_profile_service import ParentProfileService

router = APIRouter(prefix="/parents/me", tags=["家长个人中心"])

ParentUser = Annotated[User, Depends(require_roles(UserRole.PARENT))]


def get_service(db: Annotated[Session, Depends(get_db)]) -> ParentProfileService:
    return ParentProfileService(db)


@router.get("/profile", response_model=ApiResponse[ParentProfileResponse])
def get_my_profile(
    current_user: ParentUser,
    service: Annotated[ParentProfileService, Depends(get_service)],
):
    return success(service.get_profile(current_user.id))


@router.patch("/nickname", response_model=ApiResponse[ParentProfileResponse])
def update_my_nickname(
    payload: NicknameUpdateRequest,
    current_user: ParentUser,
    service: Annotated[ParentProfileService, Depends(get_service)],
):
    return success(service.update_nickname(current_user.id, payload), message="昵称已更新")
