"""AI 解析按角色日限额."""

from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.services.ai_service import AiService


def test_teacher_daily_limit_is_higher_than_student(db: Session, teacher: User, student: User) -> None:
    service = AiService(db)
    assert service._daily_limit(teacher.id) == 10
    assert service._daily_limit(student.id) == 5
    assert service._remaining_today(teacher.id) == 10
    assert service._remaining_today(student.id) == 5
