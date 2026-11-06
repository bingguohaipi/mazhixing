from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.core.response import ApiResponse, success
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.analytics_schema import (
    AnalyticsPeriod,
    ClassAnalytics,
    ClassProblemWrongCodesResponse,
    ClassWrongSummary,
    SubmissionTrendRange,
    SubmissionTrendResponse,
    TeacherDashboardOverview,
)
from app.schemas.leaderboard_schema import LeaderboardResponse
from app.services.analytics_service import AnalyticsService
from app.services.leaderboard_service import LeaderboardService

router = APIRouter(prefix="/analytics", tags=["学情分析"])

TeacherUser = Annotated[User, Depends(require_roles(UserRole.TEACHER))]


def get_analytics_service(db: Annotated[Session, Depends(get_db)]) -> AnalyticsService:
    return AnalyticsService(db)


def get_leaderboard_service(db: Annotated[Session, Depends(get_db)]) -> LeaderboardService:
    return LeaderboardService(db)


@router.get("/dashboard", response_model=ApiResponse[TeacherDashboardOverview])
def get_dashboard(
    current_user: TeacherUser,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
):
    data = service.get_dashboard(current_user.id)
    return success(data)


@router.get("/class/{class_id}", response_model=ApiResponse[ClassAnalytics])
def get_class_analytics(
    class_id: int,
    current_user: TeacherUser,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    period: AnalyticsPeriod = Query("week"),
    homework_id: int | None = Query(None),
):
    data = service.get_class_analytics(current_user.id, class_id, period, homework_id)
    return success(data)


@router.get(
    "/class/{class_id}/submission-trend",
    response_model=ApiResponse[SubmissionTrendResponse],
)
def get_class_submission_trend(
    class_id: int,
    current_user: TeacherUser,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    trend_range: SubmissionTrendRange = Query("7d"),
    homework_id: int | None = Query(None),
):
    data = service.get_submission_trend(
        current_user.id,
        class_id,
        trend_range,
        homework_id,
    )
    return success(data)


@router.get("/class/{class_id}/leaderboard", response_model=ApiResponse[LeaderboardResponse])
def get_class_leaderboard(
    class_id: int,
    current_user: TeacherUser,
    service: Annotated[LeaderboardService, Depends(get_leaderboard_service)],
):
    data = service.get_class_leaderboard(
        class_id,
        current_user.id,
        "teacher",
        teacher_id=current_user.id,
    )
    return success(data)


@router.get("/class/{class_id}/wrong-summary", response_model=ApiResponse[ClassWrongSummary])
def get_class_wrong_summary(
    class_id: int,
    current_user: TeacherUser,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    period: AnalyticsPeriod = Query("week"),
    homework_id: int | None = Query(None),
    knowledge_point: str | None = Query(None),
):
    data = service.get_class_wrong_summary(
        current_user.id,
        class_id,
        period,
        homework_id,
        knowledge_point,
    )
    return success(data)


@router.get(
    "/class/{class_id}/problems/{problem_id}/wrong-codes",
    response_model=ApiResponse[ClassProblemWrongCodesResponse],
)
def get_class_problem_wrong_codes(
    class_id: int,
    problem_id: int,
    current_user: TeacherUser,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    period: AnalyticsPeriod = Query("week"),
    homework_id: int | None = Query(None),
):
    data = service.get_class_problem_wrong_codes(
        current_user.id,
        class_id,
        problem_id,
        period,
        homework_id,
    )
    return success(data)


@router.get("/class/{class_id}/wrong-summary/export")
def export_wrong_summary(
    class_id: int,
    current_user: TeacherUser,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    period: AnalyticsPeriod = Query("week"),
    homework_id: int | None = Query(None),
    knowledge_point: str | None = Query(None),
):
    content = service.export_wrong_summary_csv(
        current_user.id,
        class_id,
        period,
        homework_id,
        knowledge_point,
    )
    return PlainTextResponse(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=wrong_summary.csv"},
    )


@router.get("/export")
def export_analytics(
    current_user: TeacherUser,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    class_id: int | None = Query(None),
    period: AnalyticsPeriod = Query("week"),
    homework_id: int | None = Query(None),
):
    content = service.export_csv(current_user.id, class_id, period, homework_id)
    return PlainTextResponse(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=analytics_report.csv"},
    )
