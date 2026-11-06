from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.core.response import ApiResponse, success
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.arena_schema import (
    ArenaBoardResponse,
    ArenaGlobalLeaderboardResponse,
    ArenaNotificationListResponse,
    ArenaNotificationsReadRequest,
    ArenaOverviewResponse,
    ArenaProblemListResponse,
    ArenaSessionCreateRequest,
    ArenaSessionDetail,
    ArenaSessionMetricsPatch,
    ArenaSubmitRequest,
    ArenaSubmitResponse,
)
from app.services.arena_service import ArenaService

router = APIRouter(prefix="/practice/arena", tags=["擂台"])

StudentUser = Annotated[User, Depends(require_roles(UserRole.STUDENT))]


def get_arena_service(db: Annotated[Session, Depends(get_db)]) -> ArenaService:
    return ArenaService(db)


@router.get("/overview", response_model=ApiResponse[ArenaOverviewResponse])
def arena_overview(
    current_user: StudentUser,
    service: Annotated[ArenaService, Depends(get_arena_service)],
):
    return success(service.get_overview(current_user.id))


@router.get("/problems", response_model=ApiResponse[ArenaProblemListResponse])
def list_arena_problems(
    current_user: StudentUser,
    service: Annotated[ArenaService, Depends(get_arena_service)],
    language: Annotated[str | None, Query(description="可选：Python 或 C++，不传则全部题目")] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = Query(None, max_length=64),
    difficulty: str | None = Query(None, max_length=16),
):
    return success(
        service.list_arena_problems(
            current_user.id, page, page_size, keyword, difficulty, language
        )
    )


@router.get("/leaderboard", response_model=ApiResponse[ArenaGlobalLeaderboardResponse])
def get_arena_global_leaderboard(
    current_user: StudentUser,
    service: Annotated[ArenaService, Depends(get_arena_service)],
    language: Annotated[str, Query(description="Python 或 C++")],
    limit: int = Query(50, ge=1, le=100),
):
    return success(service.get_global_leaderboard(current_user.id, language, limit))


@router.get("/problems/{problem_id}/board", response_model=ApiResponse[ArenaBoardResponse])
def get_arena_board(
    problem_id: int,
    current_user: StudentUser,
    service: Annotated[ArenaService, Depends(get_arena_service)],
    language: Annotated[str, Query(description="Python 或 C++")],
    limit: int = Query(20, ge=1, le=50),
):
    return success(service.get_board(current_user.id, problem_id, language, limit))


@router.post("/sessions", response_model=ApiResponse[ArenaSessionDetail])
def create_arena_session(
    payload: ArenaSessionCreateRequest,
    current_user: StudentUser,
    service: Annotated[ArenaService, Depends(get_arena_service)],
):
    item = service.create_session(current_user.id, payload.problem_id, payload.language)
    return success(item, message="擂台已开始")


@router.get("/sessions/{session_id}", response_model=ApiResponse[ArenaSessionDetail])
def get_arena_session(
    session_id: int,
    current_user: StudentUser,
    service: Annotated[ArenaService, Depends(get_arena_service)],
):
    return success(service.get_session(current_user.id, session_id))


@router.post("/sessions/{session_id}/exit", response_model=ApiResponse[None])
def exit_arena_session(
    session_id: int,
    current_user: StudentUser,
    service: Annotated[ArenaService, Depends(get_arena_service)],
):
    service.exit_session(current_user.id, session_id)
    return success(message="已退出擂台")


@router.patch("/sessions/{session_id}/metrics", response_model=ApiResponse[None])
def patch_arena_metrics(
    session_id: int,
    payload: ArenaSessionMetricsPatch,
    current_user: StudentUser,
    service: Annotated[ArenaService, Depends(get_arena_service)],
):
    service.patch_metrics(current_user.id, session_id, payload)
    return success(message="ok")


@router.post("/sessions/{session_id}/submit", response_model=ApiResponse[ArenaSubmitResponse])
def submit_arena_session(
    session_id: int,
    payload: ArenaSubmitRequest,
    current_user: StudentUser,
    service: Annotated[ArenaService, Depends(get_arena_service)],
):
    detail, brief = service.submit_session(current_user.id, session_id, payload.code)
    return success(
        ArenaSubmitResponse(
            submission_id=detail.id,
            status=detail.status,
            arena_result=brief,
            points_awarded=detail.points_awarded,
            points_balance=detail.points_balance,
        )
    )


@router.post("/agreement", response_model=ApiResponse[None])
def accept_arena_agreement(
    current_user: StudentUser,
    service: Annotated[ArenaService, Depends(get_arena_service)],
):
    service.agree_terms(current_user.id)
    return success(message="已同意擂台规则")


@router.get("/notifications", response_model=ApiResponse[ArenaNotificationListResponse])
def list_arena_notifications(
    current_user: StudentUser,
    service: Annotated[ArenaService, Depends(get_arena_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return success(service.list_notifications(current_user.id, page, page_size))


@router.post("/notifications/read", response_model=ApiResponse[dict])
def read_arena_notifications(
    payload: ArenaNotificationsReadRequest,
    current_user: StudentUser,
    service: Annotated[ArenaService, Depends(get_arena_service)],
):
    count = service.mark_notifications_read(current_user.id, payload.ids, payload.all)
    return success({"marked": count})

