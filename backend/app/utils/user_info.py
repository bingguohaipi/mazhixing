from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.schemas.auth import UserInfo
from app.utils.student_coding_language import resolve_student_default_coding_language
from app.utils.user_display import public_display_name
from app.utils.user_media import avatar_public_url


def build_user_info(user: User, db: Session | None = None) -> UserInfo:
    default_coding_language = None
    if db is not None and user.role == UserRole.STUDENT:
        default_coding_language = resolve_student_default_coding_language(db, user.id)
    return UserInfo(
        id=user.id,
        account=user.account,
        role=user.role.value,
        display_name=public_display_name(user),
        real_name=user.display_name,
        nickname=user.nickname,
        phone=user.phone,
        avatar_url=avatar_public_url(user.avatar_path),
        default_coding_language=default_coding_language,
    )
