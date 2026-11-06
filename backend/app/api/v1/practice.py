from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.core.exceptions import AppException
from app.core.rate_limit_deps import rate_limit_by_user
from app.core.response import ApiResponse, success
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.leaderboard_schema import LeaderboardResponse
from app.schemas.practice_schema import (
    KnowledgePointDetailResponse,
    KnowledgePointListResponse,
    KnowledgePointOptionItem,
    PracticeProblemDetail,
    PracticeProblemListResponse,
    StudentHomeworkDetail,
)
from app.schemas.ai_schema import AiAnalysisResponse
from app.schemas.student_dashboard_schema import StudentDashboardOverview
from app.schemas.submission_schema import (
    SubmissionCreateRequest,
    SubmissionDetail,
    SubmissionListItem,
)
from app.schemas.wrong_book_schema import WrongBookClearRequest, WrongBookListResponse, WrongReviewStatus, WrongSortBy
from app.services.ai_service import AiService
from app.services.leaderboard_service import LeaderboardService
from app.services.practice_service import PracticeService
from app.services.student_dashboard_service import StudentDashboardService
from app.services.submission_service import SubmissionService
from app.services.wrong_book_service import WrongBookService

router = APIRouter(tags=["在线练习"])

StudentUser = Annotated[User, Depends(require_roles(UserRole.STUDENT))]
StudentOrTeacherUser = Annotated[User, Depends(require_roles(UserRole.STUDENT, UserRole.TEACHER))]
AiAnalysisUser = Annotated[
    User,
    Depends(require_roles(UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN)),
]
PracticeProblemViewer = Annotated[
    User,
    Depends(require_roles(UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN)),
]
ProblemAuthorUser = Annotated[
    User,
    Depends(require_roles(UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN)),
]


def get_practice_service(db: Annotated[Session, Depends(get_db)]) -> PracticeService:
    return PracticeService(db)


def get_submission_service(db: Annotated[Session, Depends(get_db)]) -> SubmissionService:
    return SubmissionService(db)


def get_ai_service(db: Annotated[Session, Depends(get_db)]) -> AiService:
    return AiService(db)


def get_wrong_book_service(db: Annotated[Session, Depends(get_db)]) -> WrongBookService:
    return WrongBookService(db)


def get_leaderboard_service(db: Annotated[Session, Depends(get_db)]) -> LeaderboardService:
    return LeaderboardService(db)


def get_student_dashboard_service(db: Annotated[Session, Depends(get_db)]) -> StudentDashboardService:
    return StudentDashboardService(db)


@router.get("/practice/dashboard", response_model=ApiResponse[StudentDashboardOverview])
def get_student_dashboard(
    current_user: StudentUser,
    service: Annotated[StudentDashboardService, Depends(get_student_dashboard_service)],
):
    data = service.get_overview(current_user.id)
    return success(data)


@router.get("/practice/wrong-book", response_model=ApiResponse[WrongBookListResponse])
def list_wrong_book(
    current_user: StudentUser,
    service: Annotated[WrongBookService, Depends(get_wrong_book_service)],
    review_status: WrongReviewStatus | None = Query(None),
    knowledge_point: str | None = Query(None, max_length=64),
    sort_by: WrongSortBy = Query("error_count"),
):
    data = service.list_wrong_book(
        current_user.id,
        review_status=review_status,
        knowledge_point=knowledge_point,
        sort_by=sort_by,
    )
    return success(data)


@router.post("/practice/wrong-book/clear", response_model=ApiResponse[dict])
def clear_wrong_book(
    payload: WrongBookClearRequest,
    current_user: StudentUser,
    service: Annotated[WrongBookService, Depends(get_wrong_book_service)],
):
    count = service.clear_wrong_book(current_user.id, payload.problem_id)
    return success({"cleared_count": count}, message="错题记录已清空")


@router.get("/practice/leaderboard", response_model=ApiResponse[LeaderboardResponse])
def get_leaderboard(
    current_user: StudentUser,
    service: Annotated[LeaderboardService, Depends(get_leaderboard_service)],
    class_id: int | None = Query(None),
):
    target_class_id = class_id or service.get_student_primary_class_id(current_user.id)
    if target_class_id is None:
        return success(
            LeaderboardResponse(
                class_id=0,
                class_name="",
                my_rank=None,
                my_score=None,
                entries=[],
            )
        )
    data = service.get_class_leaderboard(target_class_id, current_user.id, "student")
    return success(data)


@router.get("/practice/knowledge-point-options", response_model=ApiResponse[list[KnowledgePointOptionItem]])
def list_knowledge_point_options(
    _: ProblemAuthorUser,
    db: Annotated[Session, Depends(get_db)],
    search: str | None = Query(None, max_length=64),
):
    from app.services.knowledge_point_service import KnowledgePointService

    service = KnowledgePointService(db)
    return success(service.list_form_options(search))


@router.get("/practice/knowledge-points", response_model=ApiResponse[KnowledgePointListResponse])
def list_knowledge_points(
    current_user: StudentUser,
    service: Annotated[PracticeService, Depends(get_practice_service)],
):
    data = service.list_knowledge_points(current_user.id)
    return success(data)


@router.get(
    "/practice/knowledge-points/{knowledge_point}",
    response_model=ApiResponse[KnowledgePointDetailResponse],
)
def get_knowledge_point_detail(
    knowledge_point: str,
    current_user: StudentUser,
    service: Annotated[PracticeService, Depends(get_practice_service)],
):
    data = service.get_knowledge_point_detail(current_user.id, knowledge_point)
    return success(data)


@router.get("/practice/problems", response_model=ApiResponse[PracticeProblemListResponse])
def list_practice_problems(
    current_user: StudentUser,
    service: Annotated[PracticeService, Depends(get_practice_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = Query(None, max_length=64),
    difficulty: str | None = Query(None),
    knowledge_point: str | None = Query(None, max_length=64),
    language: str | None = Query(None, max_length=16),
    sort_by: str = Query("id", pattern="^(id|difficulty)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
):
    result = service.list_problems(
        current_user.id,
        page=page,
        page_size=page_size,
        keyword=keyword,
        difficulty=difficulty,
        knowledge_point=knowledge_point,
        language=language,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return success(result)


@router.get("/practice/problems/{problem_id}", response_model=ApiResponse[PracticeProblemDetail])
def get_practice_problem(
    problem_id: int,
    current_user: PracticeProblemViewer,
    service: Annotated[PracticeService, Depends(get_practice_service)],
):
    if current_user.role == UserRole.TEACHER:
        item = service.get_problem_for_teacher(current_user.id, problem_id)
    elif current_user.role == UserRole.ADMIN:
        item = service.get_problem_for_admin(current_user.id, problem_id)
    else:
        item = service.get_problem(current_user.id, problem_id)
    return success(item)


@router.get("/homework/my/{homework_id}", response_model=ApiResponse[StudentHomeworkDetail])
def get_my_homework_detail(
    homework_id: int,
    current_user: StudentUser,
    service: Annotated[PracticeService, Depends(get_practice_service)],
):
    item = service.get_student_homework(current_user.id, homework_id)
    return success(item)


@router.post("/submissions", response_model=ApiResponse[SubmissionDetail])
def create_submission(
    payload: SubmissionCreateRequest,
    current_user: StudentOrTeacherUser,
    service: Annotated[SubmissionService, Depends(get_submission_service)],
    _: Annotated[None, Depends(rate_limit_by_user("practice:submit", 30, 60))],
):
    if current_user.role == UserRole.TEACHER and payload.homework_id is not None:
        raise AppException(400, "教师预览模式下不可提交作业代码", status_code=400)
    item = service.create_submission(current_user.id, payload)
    return success(item, message="提交成功")


@router.get("/submissions", response_model=ApiResponse[list[SubmissionListItem]])
def list_submissions(
    current_user: StudentOrTeacherUser,
    service: Annotated[SubmissionService, Depends(get_submission_service)],
    problem_id: int = Query(..., ge=1),
    homework_id: int | None = Query(None),
    limit: int = Query(20, ge=1, le=50),
):
    items = service.list_submissions(current_user.id, problem_id, homework_id, limit)
    return success(items)


@router.get("/submissions/{submission_id}", response_model=ApiResponse[SubmissionDetail])
def get_submission(
    submission_id: int,
    current_user: StudentOrTeacherUser,
    service: Annotated[SubmissionService, Depends(get_submission_service)],
):
    item = service.get_submission(submission_id, current_user.id)
    return success(item)


@router.post("/submissions/{submission_id}/ai-analysis", response_model=ApiResponse[AiAnalysisResponse])
def analyze_submission(
    submission_id: int,
    current_user: AiAnalysisUser,
    service: Annotated[AiService, Depends(get_ai_service)],
):
    content, remaining, highlight_lines = service.analyze_submission(current_user.id, submission_id)
    return success(
        AiAnalysisResponse(
            content=content,
            remaining_today=remaining,
            highlight_lines=highlight_lines,
        ),
        message="AI 解析完成",
    )
