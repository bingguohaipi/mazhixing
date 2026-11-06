from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_token(subject: str, token_type: str, expires_delta: timedelta, extra: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_access_token(user_id: int, role: str, token_version: int) -> str:
    settings = get_settings()
    return create_token(
        str(user_id),
        "access",
        timedelta(minutes=settings.access_token_expire_minutes),
        {"role": role, "tv": token_version},
    )


def create_refresh_token(user_id: int, role: str, token_version: int) -> str:
    settings = get_settings()
    return create_token(
        str(user_id),
        "refresh",
        timedelta(days=settings.refresh_token_expire_days),
        {"role": role, "tv": token_version},
    )


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])


def safe_decode_token(token: str) -> dict[str, Any] | None:
    try:
        return decode_token(token)
    except JWTError:
        return None
