from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.class_model import TeachingClass
from app.models.problem import Problem
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User
from tests.conftest import auth_header


def _add_wrong_submission(db: Session, student: User, problem: Problem) -> None:
    db.add(
        Submission(
            user_id=student.id,
            problem_id=problem.id,
            code="int main(){}",
            language="cpp",
            status=SubmissionStatus.WA,
            is_late=False,
            created_at=datetime.now(timezone.utc),
        )
    )
    db.commit()


def test_class_wrong_summary(
    client: TestClient,
    db: Session,
    teacher: User,
    student: User,
    teaching_class: TeachingClass,
    problem: Problem,
) -> None:
    _add_wrong_submission(db, student, problem)
    headers = auth_header(client, "13800138000", "Teacher123", "teacher")
    response = client.get(
        f"/api/v1/analytics/class/{teaching_class.id}/wrong-summary",
        headers=headers,
        params={"period": "week"},
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["total_wrong_submissions"] == 1
    assert data["problem_count"] == 1
    assert data["problems"][0]["problem_id"] == problem.id
    assert data["problems"][0]["affected_student_count"] == 1
    assert data["problems"][0]["students"][0]["real_name"] == "测试学生"


def test_wrong_summary_excludes_eventual_ac(
    client: TestClient,
    db: Session,
    teacher: User,
    student: User,
    teaching_class: TeachingClass,
    problem: Problem,
) -> None:
    _add_wrong_submission(db, student, problem)
    db.add(
        Submission(
            user_id=student.id,
            problem_id=problem.id,
            code="print(3)",
            language="Python",
            status=SubmissionStatus.AC,
            is_late=False,
            created_at=datetime.now(timezone.utc),
        )
    )
    db.commit()
    headers = auth_header(client, "13800138000", "Teacher123", "teacher")
    response = client.get(
        f"/api/v1/analytics/class/{teaching_class.id}/wrong-summary",
        headers=headers,
        params={"period": "week"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total_wrong_submissions"] == 0
    assert data["problem_count"] == 0


def test_class_problem_wrong_codes(
    client: TestClient,
    db: Session,
    teaching_class: TeachingClass,
    student: User,
    problem: Problem,
) -> None:
    _add_wrong_submission(db, student, problem)
    headers = auth_header(client, "13800138000", "Teacher123", "teacher")
    response = client.get(
        f"/api/v1/analytics/class/{teaching_class.id}/problems/{problem.id}/wrong-codes",
        headers=headers,
        params={"period": "week"},
    )
    assert response.status_code == 200, response.text
    items = response.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["student_id"] == student.id
    assert "main" in items[0]["code"]


def test_export_wrong_summary_csv(
    client: TestClient,
    db: Session,
    teaching_class: TeachingClass,
    student: User,
    problem: Problem,
) -> None:
    _add_wrong_submission(db, student, problem)
    headers = auth_header(client, "13800138000", "Teacher123", "teacher")
    response = client.get(
        f"/api/v1/analytics/class/{teaching_class.id}/wrong-summary/export",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    assert "错题提交总数" in response.text
    assert problem.title in response.text
