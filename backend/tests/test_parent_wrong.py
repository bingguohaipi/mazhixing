from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.audit import ParentStudentBinding
from app.models.problem import Problem
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User, UserRole
from tests.conftest import auth_header


def _setup_parent(db: Session, student: User) -> User:
    parent = User(
        account="13900139000",
        phone="13900139000",
        password_hash=hash_password("Parent123"),
        role=UserRole.PARENT,
        display_name="测试家长",
    )
    db.add(parent)
    db.flush()
    db.add(ParentStudentBinding(parent_id=parent.id, student_id=student.id))
    db.commit()
    db.refresh(parent)
    return parent


def _add_wrong_submission(db: Session, student: User, problem: Problem) -> None:
    db.add(
        Submission(
            user_id=student.id,
            problem_id=problem.id,
            code="print(1)",
            language="python",
            status=SubmissionStatus.WA,
            is_late=False,
            ai_analysis="检查输入输出格式",
            created_at=datetime.now(timezone.utc),
        )
    )
    db.commit()


def test_parent_wrong_book(
    client: TestClient,
    db: Session,
    student: User,
    problem: Problem,
) -> None:
    _setup_parent(db, student)
    _add_wrong_submission(db, student, problem)
    headers = auth_header(client, "13900139000", "Parent123", "parent")
    response = client.get(
        f"/api/v1/parent/children/{student.id}/wrong-book",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["summary"]["pending_count"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["problem_id"] == problem.id
    assert data["items"][0]["ai_analysis"] == "检查输入输出格式"
    assert "last_code" not in data["items"][0]


def test_parent_cannot_access_unbound_student(
    client: TestClient,
    db: Session,
    student: User,
) -> None:
    _setup_parent(db, student)
    other = User(
        account="stu002",
        password_hash=hash_password("123456"),
        role=UserRole.STUDENT,
        display_name="其他学生",
        student_no="002",
    )
    db.add(other)
    db.commit()
    db.refresh(other)

    headers = auth_header(client, "13900139000", "Parent123", "parent")
    response = client.get(
        f"/api/v1/parent/children/{other.id}/wrong-book",
        headers=headers,
    )
    assert response.status_code == 403
