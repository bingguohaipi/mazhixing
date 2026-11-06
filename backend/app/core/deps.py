"""FastAPI 依赖：JWT 鉴权、角色校验、客户端 IP。"""

from typing import Annotated

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.audit import log_access_denied
from app.core.exceptions import AppException
from app.core.security import safe_decode_token
from app.db.session import get_db
from app.models.user import User, UserRole

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """解析 Bearer access 令牌并加载用户（含单设备 token_version 校验）。"""
    if credentials is None or not credentials.credentials:
        raise AppException(401, "未认证，请先登录", status_code=401)

    payload = safe_decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise AppException(401, "登录已过期，请重新登录", status_code=401)

    user_id = payload.get("sub")
    if user_id is None:
        raise AppException(401, "无效的认证令牌", status_code=401)

    user = db.get(User, int(user_id))
    if user is None or user.deleted_at is not None or not user.is_active:
        raise AppException(401, "用户不存在或已被禁用", status_code=401)

    token_role = payload.get("role")
    if token_role and token_role != user.role.value:
        raise AppException(401, "角色信息不匹配，请重新登录", status_code=401)

    token_version = payload.get("tv")
    if token_version is not None and int(token_version) != user.token_version:
        raise AppException(401, "账号已在其他设备登录，请重新登录", status_code=401)

    return user


def require_roles(*roles: UserRole):
    """生成「仅允许指定角色」的路由依赖，越权时写审计并返回 403。"""

    def checker(
        current_user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
        client_ip: Annotated[str | None, Depends(get_client_ip)] = None,
    ) -> User:
        if current_user.role not in roles:
            role_names = ",".join(role.value for role in roles)
            log_access_denied(
                db,
                current_user.id,
                client_ip,
                f"required_roles={role_names}, actual={current_user.role.value}",
            )
            raise AppException(403, "暂无权限访问该页面", status_code=403)
        return current_user

    return checker


def get_client_ip(
    x_forwarded_for: Annotated[str | None, Header()] = None,
    x_real_ip: Annotated[str | None, Header()] = None,
) -> str | None:
    """从 X-Forwarded-For / X-Real-IP 提取客户端 IP（Nginx 反代后使用）。"""
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return x_real_ip


def get_optional_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User | None:
    """可选登录：无令牌或无效时返回 None，不抛 401（用于埋点等）。"""
    if credentials is None or not credentials.credentials:
        return None

    payload = safe_decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    user = db.get(User, int(user_id))
    if user is None or user.deleted_at is not None or not user.is_active:
        return None

    token_role = payload.get("role")
    if token_role and token_role != user.role.value:
        return None

    token_version = payload.get("tv")
    if token_version is not None and int(token_version) != user.token_version:
        return None

    return user
