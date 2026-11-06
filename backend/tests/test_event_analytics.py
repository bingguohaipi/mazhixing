from datetime import datetime, timezone

from app.models.event_log import EventLog
from app.models.user import User, UserRole
from app.services.event_analytics_service import EventAnalyticsService


def test_event_summary_counts(db, teacher: User) -> None:
    db.add_all(
        [
            EventLog(user_id=teacher.id, user_role=UserRole.TEACHER.value, event_name="code_submit"),
            EventLog(user_id=teacher.id, user_role=UserRole.TEACHER.value, event_name="code_submit"),
            EventLog(
                user_id=teacher.id,
                user_role=UserRole.TEACHER.value,
                event_name="code_submit_fail",
                created_at=datetime.now(timezone.utc),
            ),
        ]
    )
    db.commit()

    summary = EventAnalyticsService(db).get_summary(days=7)
    assert summary.total_events == 3
    assert summary.error_events == 1
    assert summary.judge_success_rate == 66.7
