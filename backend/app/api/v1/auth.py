from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.deps import get_client_ip, get_current_user
from app.core.rate_limit import check_rate_limit
from app.core.rate_limit_deps import rate_limit_by_ip
from app.core.response import ApiResponse, success
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.verification_code import VerificationPurpose
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SendCodeRequest,
    TokenPair,
    UserInfo,
)
from app.services.auth_service import AuthService
from app.utils.user_info import build_user_info

router = APIRouter(prefix="/auth", tags=["认证"])


def get_auth_service(db: Annotated[Session, Depends(get_db)]) -> AuthService:
    """构造认证领域服务（绑定当前数据库会话）。"""
    return AuthService(db)


@router.post("/send-code", response_model=ApiResponse[dict])
def send_code(
    payload: SendCodeRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
    _: Annotated[None, Depends(rate_limit_by_ip("auth:send-code", 10, 60))],
):
    """发送短信验证码（注册/重置密码）；生产环境不返回 dev_code。"""
    check_rate_limit(f"auth:send-code:phone:{payload.phone}", 5, 300)
    purpose = VerificationPurpose(payload.purpose)
    role = UserRole(payload.role) if payload.role else None
    code = service.send_verification_code(payload.phone, purpose, role)
    data: dict = {"sent": True}
    if service.settings.debug:
        data["dev_code"] = code
    return success(data, message="验证码已发送")


@router.post("/register", response_model=ApiResponse[UserInfo])
def register(
    payload: RegisterRequest,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
    _: Annotated[None, Depends(rate_limit_by_ip("auth:register", 5, 60))],
):
    """校验验证码后创建用户并返回基本信息。"""
    ip = get_client_ip(
        request.headers.get("x-forwarded-for"),
        request.headers.get("x-real-ip") or (request.client.host if request.client else None),
    )
    user = service.register(payload, ip)
    return success(user, message="注册成功")


@router.post("/login", response_model=ApiResponse[LoginResponse])
def login(
    payload: LoginRequest,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
    _: Annotated[None, Depends(rate_limit_by_ip("auth:login", 20, 60))],
):
    """账号密码登录，签发 access/refresh 令牌。"""
    ip = request.client.host if request.client else None
    result = service.login(payload, ip)
    return success(result, message="登录成功")


@router.post("/refresh", response_model=ApiResponse[TokenPair])
def refresh_token(
    payload: RefreshTokenRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    """使用 refresh 令牌换取新的 access/refresh 对（前端 axios 拦截器调用）。"""
    tokens = service.refresh(payload.refresh_token)
    return success(tokens)


@router.get("/me", response_model=ApiResponse[UserInfo])
def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """返回当前登录用户的展示信息与角色。"""
    return success(build_user_info(current_user, db))


@router.post("/change-password", response_model=ApiResponse[None])
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    """已登录用户修改密码（成功后需重新登录）。"""
    ip = request.client.host if request.client else None
    service.change_password(current_user, payload, ip)
    return success(message="密码修改成功，请重新登录")


@router.post("/reset-password", response_model=ApiResponse[None])
def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
    _: Annotated[None, Depends(rate_limit_by_ip("auth:reset-password", 5, 60))],
):
    """通过手机验证码重置密码（未登录可用）。"""
    ip = request.client.host if request.client else None
    service.reset_password(payload, ip)
    return success(message="密码重置成功")
