"""提交趋势时间范围。"""

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.models.submission import Submission, SubmissionStatus
from app.models.user import User
from tests.conftest import auth_header


def test_submission_trend_7d_daily_bars(
    client: TestClient,
    db,
    teacher: User,
    student: User,
    teaching_class,
    problem,
) -> None:
    now = datetime.now(timezone.utc)
    db.add(
        Submission(
            user_id=student.id,
            problem_id=problem.id,
            homework_id=None,
            language="Python",
            code="print(1)",
            status=SubmissionStatus.AC,
            created_at=now,
        )
    )
    db.commit()

    headers = auth_header(client, teacher.account, "Teacher123", "teacher")
    res = client.get(
        f"/api/v1/analytics/class/{teaching_class.id}/submission-trend",
        headers=headers,
        params={"trend_range": "7d"},
    )
    assert res.status_code == 200
    body = res.json()["data"]
    assert body["granularity"] == "day"
    assert body["chart_type"] == "bar"
    assert len(body["items"]) == 7
    assert sum(item["count"] for item in body["items"]) == 1


def test_submission_trend_2y_monthly_includes_current_month(
    client: TestClient,
    db,
    teacher: User,
    student: User,
    teaching_class,
    problem,
) -> None:
    now = datetime.now(timezone.utc)
    db.add(
        Submission(
            user_id=student.id,
            problem_id=problem.id,
            homework_id=None,
            language="Python",
            code="print(1)",
            status=SubmissionStatus.AC,
            created_at=now,
        )
    )
    db.commit()

    headers = auth_header(client, teacher.account, "Teacher123", "teacher")
    res = client.get(
        f"/api/v1/analytics/class/{teaching_class.id}/submission-trend",
        headers=headers,
        params={"trend_range": "2y"},
    )
    assert res.status_code == 200
    body = res.json()["data"]
    assert body["granularity"] == "month"
    assert body["chart_type"] == "bar"
    assert body["items"][-1]["count"] >= 1
