from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.core.response import ApiResponse, success
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.admin_schema import (
    AdminParentBindingItem,
    AdminParentRebindRequest,
    AdminParentStudentBindRequest,
    AdminStudentTeacherBindRequest,
    AdminUserCreateRequest,
    AdminUserListItem,
    AdminUserListResponse,
    AdminUserRelationsResponse,
    AdminUserUpdateRequest,
    PublicProblemListResponse,
)
from app.schemas.event_schema import EventSummaryResponse
from app.schemas.problem_schema import (
    ProblemCreateRequest,
    ProblemDetail,
    ProblemImportRequest,
    ProblemImportResult,
    ProblemUpdateRequest,
)
from app.schemas.arena_schema import AdminArenaEnabledPatch
from app.services.admin_service import AdminPublicProblemService, AdminUserService
from app.services.arena_service import ArenaService
from app.services.event_analytics_service import EventAnalyticsService
from app.schemas.pet_admin_schema import (
    AdminPetPointsConfigResponse,
    AdminShopItemCreateRequest,
    AdminShopItemListItem,
    AdminShopItemListResponse,
    AdminShopItemPatchRequest,
)
from app.services.pet_admin_service import PetAdminService
from app.schemas.knowledge_point_schema import (
    AdminKnowledgePointCreateRequest,
    AdminKnowledgePointListItem,
    AdminKnowledgePointListResponse,
    AdminKnowledgePointUpdateRequest,
)
from app.services.knowledge_point_service import KnowledgePointService

router = APIRouter(prefix="/admin", tags=["管理后台"])

AdminUser = Annotated[User, Depends(require_roles(UserRole.ADMIN))]


def get_user_service(db: Annotated[Session, Depends(get_db)]) -> AdminUserService:
    return AdminUserService(db)


def get_public_problem_service(db: Annotated[Session, Depends(get_db)]) -> AdminPublicProblemService:
    return AdminPublicProblemService(db)


def get_event_analytics_service(db: Annotated[Session, Depends(get_db)]) -> EventAnalyticsService:
    return EventAnalyticsService(db)


def get_arena_service(db: Annotated[Session, Depends(get_db)]) -> ArenaService:
    return ArenaService(db)


def get_pet_admin_service(db: Annotated[Session, Depends(get_db)]) -> PetAdminService:
    return PetAdminService(db)


def get_knowledge_point_service(db: Annotated[Session, Depends(get_db)]) -> KnowledgePointService:
    return KnowledgePointService(db)


@router.get("/users", response_model=ApiResponse[AdminUserListResponse])
def list_users(
    current_user: AdminUser,
    service: Annotated[AdminUserService, Depends(get_user_service)],
    role: str | None = Query(None),
    keyword: str | None = Query(None, max_length=64),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    role_enum = UserRole(role) if role else None
    data = service.list_users(role_enum, keyword, page, page_size)
    return success(data)


@router.post("/users", response_model=ApiResponse[AdminUserListItem])
def create_user(
    payload: AdminUserCreateRequest,
    current_user: AdminUser,
    service: Annotated[AdminUserService, Depends(get_user_service)],
):
    data = service.create_user(current_user.id, payload)
    return success(data, message="用户已创建")


@router.patch("/users/{user_id}", response_model=ApiResponse[AdminUserListItem])
def update_user(
    user_id: int,
    payload: AdminUserUpdateRequest,
    current_user: AdminUser,
    service: Annotated[AdminUserService, Depends(get_user_service)],
):
    data = service.update_user(current_user.id, user_id, payload)
    return success(data, message="用户已更新")


@router.get("/users/{user_id}/relations", response_model=ApiResponse[AdminUserRelationsResponse])
def get_user_relations(
    user_id: int,
    current_user: AdminUser,
    service: Annotated[AdminUserService, Depends(get_user_service)],
):
    data = service.get_user_relations(user_id)
    return success(data)


@router.post("/bindings/parent-student", response_model=ApiResponse[AdminParentBindingItem])
def bind_parent_student(
    payload: AdminParentStudentBindRequest,
    current_user: AdminUser,
    service: Annotated[AdminUserService, Depends(get_user_service)],
):
    data = service.bind_parent_student(current_user.id, payload)
    return success(data, message="绑定成功")


@router.delete("/bindings/parent-student/{binding_id}", response_model=ApiResponse[None])
def unbind_parent_student(
    binding_id: int,
    current_user: AdminUser,
    service: Annotated[AdminUserService, Depends(get_user_service)],
):
    service.unbind_parent_student(current_user.id, binding_id)
    return success(message="已解绑")


@router.put("/bindings/parent-student/{binding_id}/rebind", response_model=ApiResponse[AdminParentBindingItem])
def rebind_parent_student(
    binding_id: int,
    payload: AdminParentRebindRequest,
    current_user: AdminUser,
    service: Annotated[AdminUserService, Depends(get_user_service)],
):
    data = service.rebind_parent_student(current_user.id, binding_id, payload)
    return success(data, message="换绑成功")


@router.put("/users/{student_id}/teacher", response_model=ApiResponse[AdminUserRelationsResponse])
def set_student_teacher(
    student_id: int,
    payload: AdminStudentTeacherBindRequest,
    current_user: AdminUser,
    service: Annotated[AdminUserService, Depends(get_user_service)],
):
    data = service.set_student_teacher(current_user.id, student_id, payload)
    return success(data, message="负责教师已更新")


@router.get("/public-problems", response_model=ApiResponse[PublicProblemListResponse])
def list_public_problems(
    current_user: AdminUser,
    service: Annotated[AdminPublicProblemService, Depends(get_public_problem_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    keyword: str | None = Query(None, max_length=64),
    difficulty: str | None = Query(None, max_length=16),
):
    data = service.list_problems(page, page_size, status, keyword, difficulty)
    return success(data)


@router.post("/public-problems", response_model=ApiResponse[ProblemDetail])
def create_public_problem(
    payload: ProblemCreateRequest,
    current_user: AdminUser,
    service: Annotated[AdminPublicProblemService, Depends(get_public_problem_service)],
):
    data = service.create_problem(current_user.id, payload)
    return success(data, message="公共题目已创建")


@router.post("/public-problems/import", response_model=ApiResponse[ProblemImportResult])
def import_public_problems(
    payload: ProblemImportRequest,
    current_user: AdminUser,
    service: Annotated[AdminPublicProblemService, Depends(get_public_problem_service)],
):
    data = service.import_problems(current_user.id, payload.problems)
    return success(data, message="批量导入完成")


@router.get("/public-problems/{problem_id}", response_model=ApiResponse[ProblemDetail])
def get_public_problem(
    problem_id: int,
    current_user: AdminUser,
    service: Annotated[AdminPublicProblemService, Depends(get_public_problem_service)],
):
    data = service.get_problem(current_user.id, problem_id)
    return success(data)


@router.put("/public-problems/{problem_id}", response_model=ApiResponse[ProblemDetail])
def update_public_problem(
    problem_id: int,
    payload: ProblemUpdateRequest,
    current_user: AdminUser,
    service: Annotated[AdminPublicProblemService, Depends(get_public_problem_service)],
):
    data = service.update_problem(current_user.id, problem_id, payload)
    return success(data, message="公共题目已更新")


@router.post("/public-problems/{problem_id}/publish", response_model=ApiResponse[ProblemDetail])
def publish_public_problem(
    problem_id: int,
    current_user: AdminUser,
    service: Annotated[AdminPublicProblemService, Depends(get_public_problem_service)],
):
    data = service.publish(current_user.id, problem_id)
    return success(data, message="已上架")


@router.post("/public-problems/{problem_id}/archive", response_model=ApiResponse[ProblemDetail])
def archive_public_problem(
    problem_id: int,
    current_user: AdminUser,
    service: Annotated[AdminPublicProblemService, Depends(get_public_problem_service)],
):
    data = service.archive(current_user.id, problem_id)
    return success(data, message="已下架")


@router.post("/public-problems/{problem_id}/new-version", response_model=ApiResponse[ProblemDetail])
def new_version_public_problem(
    problem_id: int,
    current_user: AdminUser,
    service: Annotated[AdminPublicProblemService, Depends(get_public_problem_service)],
):
    data = service.create_new_version(current_user.id, problem_id)
    return success(data, message="新版本已创建")


@router.post("/public-problems/{problem_id}/delete", response_model=ApiResponse[None])
def delete_public_problem_version_post(
    problem_id: int,
    current_user: AdminUser,
    service: Annotated[AdminPublicProblemService, Depends(get_public_problem_service)],
):
    service.delete_problem_version(current_user.id, problem_id)
    return success(None, message="旧版本已删除")


@router.delete("/public-problems/{problem_id}", response_model=ApiResponse[None])
def delete_public_problem_version(
    problem_id: int,
    current_user: AdminUser,
    service: Annotated[AdminPublicProblemService, Depends(get_public_problem_service)],
):
    service.delete_problem_version(current_user.id, problem_id)
    return success(None, message="旧版本已删除")


@router.get("/events/summary", response_model=ApiResponse[EventSummaryResponse])
def get_events_summary(
    current_user: AdminUser,
    service: Annotated[EventAnalyticsService, Depends(get_event_analytics_service)],
    days: int = Query(7, ge=1, le=90),
):
    data = service.get_summary(days)
    return success(data)


@router.patch("/public-problems/{problem_id}/arena", response_model=ApiResponse[None])
def set_public_problem_arena(
    problem_id: int,
    payload: AdminArenaEnabledPatch,
    current_user: AdminUser,
    service: Annotated[ArenaService, Depends(get_arena_service)],
):
    service.admin_set_arena_enabled(problem_id, payload.arena_enabled)
    return success(message="擂台开关已更新")


@router.get("/pet-shop/items", response_model=ApiResponse[AdminShopItemListResponse])
def admin_list_pet_shop_items(
    current_user: AdminUser,
    service: Annotated[PetAdminService, Depends(get_pet_admin_service)],
    keyword: str | None = Query(None, max_length=64),
):
    return success(service.list_shop_items(keyword))


@router.post("/pet-shop/items", response_model=ApiResponse[AdminShopItemListItem])
def admin_create_pet_shop_item(
    payload: AdminShopItemCreateRequest,
    current_user: AdminUser,
    service: Annotated[PetAdminService, Depends(get_pet_admin_service)],
):
    data = service.create_shop_item(payload)
    return success(data, message="商品已创建")


@router.delete("/pet-shop/items/{sku}", response_model=ApiResponse[None])
def admin_delete_pet_shop_item(
    sku: str,
    current_user: AdminUser,
    service: Annotated[PetAdminService, Depends(get_pet_admin_service)],
):
    service.delete_shop_item(sku)
    return success(None, message="商品已删除")


@router.patch("/pet-shop/items/{sku}", response_model=ApiResponse[AdminShopItemListItem])
def admin_patch_pet_shop_item(
    sku: str,
    payload: AdminShopItemPatchRequest,
    current_user: AdminUser,
    service: Annotated[PetAdminService, Depends(get_pet_admin_service)],
):
    return success(service.patch_shop_item(sku, payload))


@router.post("/pet-shop/items/{sku}/preview-image", response_model=ApiResponse[AdminShopItemListItem])
async def admin_upload_pet_shop_preview(
    sku: str,
    current_user: AdminUser,
    service: Annotated[PetAdminService, Depends(get_pet_admin_service)],
    file: UploadFile = File(...),
):
    content = await file.read()
    data = await service.upload_preview_image(sku, file.content_type or "", content)
    return success(data, message="图片已更新")


@router.get("/pet-points/config", response_model=ApiResponse[AdminPetPointsConfigResponse])
def admin_get_pet_points_config(
    current_user: AdminUser,
    service: Annotated[PetAdminService, Depends(get_pet_admin_service)],
):
    return success(service.get_points_config())


@router.get("/knowledge-points", response_model=ApiResponse[AdminKnowledgePointListResponse])
def admin_list_knowledge_points(
    current_user: AdminUser,
    service: Annotated[KnowledgePointService, Depends(get_knowledge_point_service)],
    keyword: str | None = Query(None, max_length=64),
    sort_by: str = Query("sort_order", pattern="^(sort_order|problem_count)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
):
    return success(service.list_for_admin(keyword, sort_by, sort_order))


@router.post("/knowledge-points", response_model=ApiResponse[AdminKnowledgePointListItem])
def admin_create_knowledge_point(
    payload: AdminKnowledgePointCreateRequest,
    current_user: AdminUser,
    service: Annotated[KnowledgePointService, Depends(get_knowledge_point_service)],
):
    data = service.create(current_user.id, payload)
    return success(data, message="知识点已创建")


@router.patch("/knowledge-points/{point_id}", response_model=ApiResponse[AdminKnowledgePointListItem])
def admin_update_knowledge_point(
    point_id: int,
    payload: AdminKnowledgePointUpdateRequest,
    current_user: AdminUser,
    service: Annotated[KnowledgePointService, Depends(get_knowledge_point_service)],
):
    data = service.update(current_user.id, point_id, payload)
    return success(data, message="知识点已更新")


@router.delete("/knowledge-points/{point_id}", response_model=ApiResponse[None])
def admin_delete_knowledge_point(
    point_id: int,
    current_user: AdminUser,
    service: Annotated[KnowledgePointService, Depends(get_knowledge_point_service)],
):
    service.delete(current_user.id, point_id)
    return success(None, message="知识点已删除")
