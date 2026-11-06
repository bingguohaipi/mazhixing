from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.core.response import ApiResponse, success
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.parent_schema import (
    ParentChildBrief,
    ParentPeriod,
    ParentStudentOverview,
    ParentWrongBookListResponse,
)
from app.schemas.wrong_book_schema import WrongReviewStatus, WrongSortBy
from app.services.parent_service import ParentService

router = APIRouter(prefix="/parent", tags=["家长学情"])

ParentUser = Annotated[User, Depends(require_roles(UserRole.PARENT))]


def get_parent_service(db: Annotated[Session, Depends(get_db)]) -> ParentService:
    return ParentService(db)


@router.get("/children", response_model=ApiResponse[list[ParentChildBrief]])
def list_children(
    current_user: ParentUser,
    service: Annotated[ParentService, Depends(get_parent_service)],
):
    items = service.list_children(current_user.id)
    return success(items)


@router.get("/children/{student_id}/overview", response_model=ApiResponse[ParentStudentOverview])
def get_student_overview(
    student_id: int,
    current_user: ParentUser,
    service: Annotated[ParentService, Depends(get_parent_service)],
    period: ParentPeriod = Query("7"),
):
    data = service.get_student_overview(current_user.id, student_id, period)
    return success(data)


@router.get(
    "/children/{student_id}/wrong-book",
    response_model=ApiResponse[ParentWrongBookListResponse],
)
def get_student_wrong_book(
    student_id: int,
    current_user: ParentUser,
    service: Annotated[ParentService, Depends(get_parent_service)],
    review_status: WrongReviewStatus | None = Query(None),
    knowledge_point: str | None = Query(None),
    sort_by: WrongSortBy = Query("error_count"),
):
    data = service.get_student_wrong_book(
        current_user.id,
        student_id,
        review_status=review_status,
        knowledge_point=knowledge_point,
        sort_by=sort_by,
    )
    return success(data)
