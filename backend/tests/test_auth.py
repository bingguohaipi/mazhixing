from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User, UserRole
from tests.conftest import auth_header


def test_login_success(client: TestClient, teacher: User) -> None:
    headers = auth_header(client, "13800138000", "Teacher123", "teacher")
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["role"] == "teacher"


def test_login_role_mismatch_hints_parent(client: TestClient, db: Session) -> None:
    parent = User(
        account="13900139000",
        phone="13900139000",
        password_hash=hash_password("Parent123"),
        role=UserRole.PARENT,
        display_name="测试家长",
    )
    db.add(parent)
    db.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"account": "13900139000", "password": "Parent123", "role": "teacher"},
    )
    assert response.status_code == 401
    assert "家长" in response.json()["message"]
    assert "返回选择身份" in response.json()["message"]


def test_login_wrong_password(client: TestClient, teacher: User) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"account": "13800138000", "password": "wrong", "role": "teacher"},
    )
    assert response.status_code == 401


def test_single_session_kicks_old_token(client: TestClient, teacher: User) -> None:
    first = auth_header(client, "13800138000", "Teacher123", "teacher")
    second = auth_header(client, "13800138000", "Teacher123", "teacher")

    stale = client.get("/api/v1/auth/me", headers=first)
    assert stale.status_code == 401

    fresh = client.get("/api/v1/auth/me", headers=second)
    assert fresh.status_code == 200


def test_student_cannot_access_teacher_classes(client: TestClient, student: User) -> None:
    headers = auth_header(client, "stu001", "123456", "student")
    response = client.get("/api/v1/classes", headers=headers)
    assert response.status_code == 403
