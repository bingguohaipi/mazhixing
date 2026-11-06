"""Auto-generate student login accounts (stu{year}{seq})."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.user import User, UserRole

DEFAULT_STUDENT_PASSWORD = "123456"


def _max_seq_for_prefix(db: Session, prefix: str) -> int:
    rows = (
        db.query(User.account)
        .filter(
            User.role == UserRole.STUDENT,
            User.account.like(f"{prefix}%"),
            User.deleted_at.is_(None),
        )
        .all()
    )
    max_seq = 0
    for (account,) in rows:
        suffix = account[len(prefix) :]
        if suffix.isdigit() and len(suffix) == 3:
            max_seq = max(max_seq, int(suffix))
    return max_seq


def _account_taken(db: Session, account: str) -> bool:
    return (
        db.query(User.id)
        .filter(User.account == account, User.role == UserRole.STUDENT, User.deleted_at.is_(None))
        .first()
        is not None
    )


def allocate_student_account(db: Session, year: int | None = None) -> tuple[str, str]:
    """Return (account, student_no) for a new student."""
    year = year or datetime.now(timezone.utc).year
    prefix = f"stu{year}"
    seq = _max_seq_for_prefix(db, prefix) + 1
    account = f"{prefix}{seq:03d}"
    while _account_taken(db, account):
        seq += 1
        account = f"{prefix}{seq:03d}"
    student_no = f"{year}{seq:03d}"
    return account, student_no
