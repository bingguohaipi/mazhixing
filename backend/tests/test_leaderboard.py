from sqlalchemy.orm import Session

from app.models.class_model import TeachingClass
from app.models.user import User
from app.services.leaderboard_service import LeaderboardService


def test_leaderboard_snapshot_refresh(db: Session, teacher: User, teaching_class: TeachingClass) -> None:
    service = LeaderboardService(db)
    count = service.refresh_class_snapshot(teaching_class.id)
    assert count >= 0

    response = service.get_class_leaderboard(
        teaching_class.id,
        viewer_id=teacher.id,
        viewer_role="teacher",
        teacher_id=teacher.id,
    )
    if count > 0:
        assert response.source == "snapshot"
        assert response.snapshot_date is not None
        assert response.refreshed_at is not None
    for entry in response.entries:
        assert entry.completed_problems > 0


def test_leaderboard_excludes_students_without_ac(
    db: Session,
    student: User,
    teaching_class: TeachingClass,
) -> None:
    service = LeaderboardService(db)
    service.refresh_class_snapshot(teaching_class.id)
    response = service.get_class_leaderboard(
        teaching_class.id,
        viewer_id=student.id,
        viewer_role="student",
    )
    assert all(e.completed_problems > 0 for e in response.entries)
    if not any(e.student_id == student.id for e in response.entries):
        assert response.my_rank is None
