from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.core.exceptions import AppException
from app.core.response import ApiResponse, success
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.problem_schema import (
    ProblemAcSolverListResponse,
    ProblemCreateRequest,
    ProblemDetail,
    ProblemImportRequest,
    ProblemImportResult,
    ProblemListResponse,
    ProblemUpdateRequest,
)
from app.services.submission_service import SubmissionService
from app.services.admin_service import AdminPublicProblemService
from app.services.problem_service import ProblemService

router = APIRouter(prefix="/problems", tags=["题库管理"])

TeacherUser = Annotated[User, Depends(require_roles(UserRole.TEACHER))]

TEACHER_READONLY_MSG = "该操作不可用，请使用「自行出题」创建作业专用题目"


def get_problem_service(db: Annotated[Session, Depends(get_db)]) -> ProblemService:
    return ProblemService(db)


def get_public_catalog_service(db: Annotated[Session, Depends(get_db)]) -> AdminPublicProblemService:
    return AdminPublicProblemService(db)


@router.get("", response_model=ApiResponse[ProblemListResponse])
def list_problems(
    current_user: TeacherUser,
    service: Annotated[AdminPublicProblemService, Depends(get_public_catalog_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = Query(None, max_length=64),
    language: str | None = Query(None),
    difficulty: str | None = Query(None),
    gesp_level: str | None = Query(None),
    knowledge_point: str | None = Query(None),
    my_passed: bool = Query(False, description="仅显示当前教师已 AC 的题目"),
):
    result = service.list_published_catalog(
        page,
        page_size,
        keyword,
        difficulty,
        language=language,
        gesp_level=gesp_level,
        knowledge_point=knowledge_point,
        viewer_id=current_user.id,
        my_passed=my_passed,
    )
    return success(result)


@router.get("/public/catalog", response_model=ApiResponse[ProblemListResponse])
def list_public_catalog(
    current_user: TeacherUser,
    service: Annotated[AdminPublicProblemService, Depends(get_public_catalog_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=100),
    keyword: str | None = Query(None, max_length=64),
    difficulty: str | None = Query(None),
    language: str | None = Query(None),
    gesp_level: str | None = Query(None),
    knowledge_point: str | None = Query(None),
    sort_by: str = Query("id", pattern="^(id|difficulty)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    my_passed: bool = Query(False, description="仅显示当前教师已 AC 的题目"),
):
    result = service.list_published_catalog(
        page,
        page_size,
        keyword,
        difficulty,
        language=language,
        gesp_level=gesp_level,
        knowledge_point=knowledge_point,
        sort_by=sort_by,
        sort_order=sort_order,
        viewer_id=current_user.id,
        my_passed=my_passed,
    )
    return success(result)


@router.get("/public/{problem_id}", response_model=ApiResponse[ProblemDetail])
def get_public_catalog_item(
    problem_id: int,
    current_user: TeacherUser,
    service: Annotated[AdminPublicProblemService, Depends(get_public_catalog_service)],
):
    item = service.get_published_catalog_item(problem_id)
    return success(item)


@router.get("/public/{problem_id}/ac-solvers", response_model=ApiResponse[ProblemAcSolverListResponse])
def list_public_problem_ac_solvers(
    problem_id: int,
    current_user: TeacherUser,
    db: Annotated[Session, Depends(get_db)],
    public_service: Annotated[AdminPublicProblemService, Depends(get_public_catalog_service)],
):
    public_service.get_published_catalog_item(problem_id)
    items = SubmissionService.list_ac_solvers(db, problem_id)
    return success(ProblemAcSolverListResponse(items=items, total=len(items)))


@router.get("/{problem_id}/ac-solvers", response_model=ApiResponse[ProblemAcSolverListResponse])
def list_problem_ac_solvers(
    problem_id: int,
    current_user: TeacherUser,
    db: Annotated[Session, Depends(get_db)],
    public_service: Annotated[AdminPublicProblemService, Depends(get_public_catalog_service)],
    problem_service: Annotated[ProblemService, Depends(get_problem_service)],
):
    try:
        public_service.get_published_catalog_item(problem_id)
    except AppException:
        problem_service.get_problem(problem_id, current_user.id)
    items = SubmissionService.list_ac_solvers(db, problem_id)
    return success(ProblemAcSolverListResponse(items=items, total=len(items)))


@router.get("/custom", response_model=ApiResponse[ProblemListResponse])
def list_custom_problems(
    current_user: TeacherUser,
    service: Annotated[ProblemService, Depends(get_problem_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=100),
    keyword: str | None = Query(None, max_length=64),
    language: str | None = Query(None),
    difficulty: str | None = Query(None),
    gesp_level: str | None = Query(None),
    knowledge_point: str | None = Query(None),
    sort_by: str = Query("id", pattern="^(id|difficulty)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    my_passed: bool = Query(False, description="仅显示当前教师已 AC 的题目"),
):
    result = service.list_problems(
        current_user.id,
        page=page,
        page_size=page_size,
        keyword=keyword,
        language=language,
        difficulty=difficulty,
        gesp_level=gesp_level,
        knowledge_point=knowledge_point,
        sort_by=sort_by,
        sort_order=sort_order,
        my_passed=my_passed,
    )
    return success(result)


@router.post("", response_model=ApiResponse[ProblemDetail])
def create_problem(
    payload: ProblemCreateRequest,
    current_user: TeacherUser,
    service: Annotated[ProblemService, Depends(get_problem_service)],
):
    item = service.create_problem(current_user.id, payload)
    return success(item, message="题目创建成功")


@router.post("/import", response_model=ApiResponse[ProblemImportResult])
def import_problems(
    payload: ProblemImportRequest,
    current_user: TeacherUser,
    service: Annotated[ProblemService, Depends(get_problem_service)],
):
    raise AppException(403, TEACHER_READONLY_MSG, status_code=403)


@router.get("/lesson-pack/export")
def export_lesson_pack(
    current_user: TeacherUser,
    service: Annotated[ProblemService, Depends(get_problem_service)],
    ids: list[int] = Query(..., min_length=1, max_length=50),
):
    raise AppException(403, TEACHER_READONLY_MSG, status_code=403)


@router.get("/{problem_id}", response_model=ApiResponse[ProblemDetail])
def get_problem(
    problem_id: int,
    current_user: TeacherUser,
    public_service: Annotated[AdminPublicProblemService, Depends(get_public_catalog_service)],
    problem_service: Annotated[ProblemService, Depends(get_problem_service)],
):
    try:
        item = public_service.get_published_catalog_item(problem_id)
    except AppException:
        item = problem_service.get_problem(problem_id, current_user.id)
    return success(item)


@router.put("/{problem_id}", response_model=ApiResponse[ProblemDetail])
def update_problem(
    problem_id: int,
    payload: ProblemUpdateRequest,
    current_user: TeacherUser,
    service: Annotated[ProblemService, Depends(get_problem_service)],
):
    item = service.update_problem(problem_id, current_user.id, payload)
    return success(item, message="题目更新成功")


@router.delete("/{problem_id}", response_model=ApiResponse[None])
def delete_problem(
    problem_id: int,
    current_user: TeacherUser,
    service: Annotated[ProblemService, Depends(get_problem_service)],
):
    service.delete_problem(problem_id, current_user.id)
    return success(message="题目已删除")
