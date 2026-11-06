from sqlalchemy.orm import Session

from app.models.audit import OperationLog


def log_access_denied(
    db: Session,
    user_id: int | None,
    ip: str | None,
    detail: str,
    *,
    commit: bool = True,
) -> None:
    db.add(
        OperationLog(
            user_id=user_id,
            action="access_denied",
            resource="auth",
            detail=detail,
            ip_address=ip,
        )
    )
    if commit:
        db.commit()
