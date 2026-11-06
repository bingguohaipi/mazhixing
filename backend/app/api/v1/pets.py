from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.core.response import ApiResponse, success
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.pet_points_schema import PointLedgerListResponse, StudentPointsSummary
from app.schemas.pet_schema import (
    InventoryUseRequest,
    InventoryUseResponse,
    PetPlayResponse,
    PetSyncRequest,
    StudentInventoryResponse,
    StudentPetActiveResponse,
    StudentPetListResponse,
    StudentPetSettingsPatchRequest,
    StudentPetSettingsResponse,
)
from app.schemas.pet_shop_schema import (
    PetShopCatalogResponse,
    PetShopOrderCreateRequest,
    PetShopOrderResponse,
)
from app.services.pet_points_service import PetPointsService
from app.services.pet_service import PetService

router = APIRouter(prefix="/students/me", tags=["学生宠物与积分"])

StudentUser = Annotated[User, Depends(require_roles(UserRole.STUDENT))]


def get_points_service(db: Annotated[Session, Depends(get_db)]) -> PetPointsService:
    return PetPointsService(db)


def get_pet_service(db: Annotated[Session, Depends(get_db)]) -> PetService:
    return PetService(db)


@router.get("/points", response_model=ApiResponse[StudentPointsSummary])
def get_my_points(
    current_user: StudentUser,
    service: Annotated[PetPointsService, Depends(get_points_service)],
):
    return success(service.get_summary(current_user.id))


@router.get("/points/ledger", response_model=ApiResponse[PointLedgerListResponse])
def get_my_point_ledger(
    current_user: StudentUser,
    service: Annotated[PetPointsService, Depends(get_points_service)],
    type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
):
    return success(service.list_ledger(current_user.id, type, page, page_size))


@router.get("/pet-shop/catalog", response_model=ApiResponse[PetShopCatalogResponse])
def get_pet_shop_catalog(
    current_user: StudentUser,
    service: Annotated[PetService, Depends(get_pet_service)],
    category: str | None = Query(default=None),
):
    return success(service.get_catalog(current_user.id, category))


@router.post("/pet-shop/orders", response_model=ApiResponse[PetShopOrderResponse])
def create_pet_shop_order(
    payload: PetShopOrderCreateRequest,
    current_user: StudentUser,
    service: Annotated[PetService, Depends(get_pet_service)],
):
    return success(service.create_order(current_user.id, payload.sku, payload.quantity))


@router.get("/pets", response_model=ApiResponse[StudentPetListResponse])
def list_my_pets(
    current_user: StudentUser,
    service: Annotated[PetService, Depends(get_pet_service)],
):
    return success(service.list_pets(current_user.id))


@router.get("/pets/active", response_model=ApiResponse[StudentPetActiveResponse | None])
def get_active_pet(
    current_user: StudentUser,
    service: Annotated[PetService, Depends(get_pet_service)],
):
    return success(service.get_active_pet(current_user.id))


@router.post("/pets/sync", response_model=ApiResponse[StudentPetActiveResponse | None])
def sync_active_pet(
    current_user: StudentUser,
    service: Annotated[PetService, Depends(get_pet_service)],
    payload: PetSyncRequest | None = None,
):
    _ = payload
    return success(service.sync_active_pet(current_user.id))


@router.post("/pets/active/play", response_model=ApiResponse[PetPlayResponse])
def play_with_active_pet(
    current_user: StudentUser,
    service: Annotated[PetService, Depends(get_pet_service)],
):
    data = service.play_with_active_pet(current_user.id)
    return success(data, message="小伙伴很开心")


@router.post("/pets/{pet_id}/activate", response_model=ApiResponse[StudentPetActiveResponse])
def activate_pet(
    pet_id: int,
    current_user: StudentUser,
    service: Annotated[PetService, Depends(get_pet_service)],
):
    return success(service.activate_pet(current_user.id, pet_id))


@router.get("/inventory", response_model=ApiResponse[StudentInventoryResponse])
def get_inventory(
    current_user: StudentUser,
    service: Annotated[PetService, Depends(get_pet_service)],
):
    return success(service.list_inventory(current_user.id))


@router.post("/inventory/use", response_model=ApiResponse[InventoryUseResponse])
def use_inventory_item(
    payload: InventoryUseRequest,
    current_user: StudentUser,
    service: Annotated[PetService, Depends(get_pet_service)],
):
    return success(service.use_inventory(current_user.id, payload.sku, payload.quantity))


@router.get("/pet-settings", response_model=ApiResponse[StudentPetSettingsResponse])
def get_pet_settings(
    current_user: StudentUser,
    service: Annotated[PetService, Depends(get_pet_service)],
):
    return success(service.get_settings(current_user.id))


@router.patch("/pet-settings", response_model=ApiResponse[StudentPetSettingsResponse])
def patch_pet_settings(
    payload: StudentPetSettingsPatchRequest,
    current_user: StudentUser,
    service: Annotated[PetService, Depends(get_pet_service)],
):
    return success(
        service.patch_settings(
            current_user.id,
            payload.desktop_pet_enabled,
            payload.silent_while_coding,
        )
    )
