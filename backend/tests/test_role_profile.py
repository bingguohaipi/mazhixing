"""Teacher and parent profile API tests."""

from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.models.audit import ParentStudentBinding
from app.models.user import User, UserRole
from tests.conftest import auth_header


def test_teacher_profile(client: TestClient, teacher: User, teaching_class) -> None:
    headers = auth_header(client, "13800138000", "Teacher123", "teacher")
    res = client.get("/api/v1/teachers/me/profile", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["account"] == "13800138000"
    assert data["real_name"] == "测试教师"
    assert "测试班" in data["class_names"]

    patch = client.patch(
        "/api/v1/teachers/me/nickname",
        headers=headers,
        json={"nickname": "王老师"},
    )
    assert patch.status_code == 200
    assert patch.json()["data"]["nickname"] == "王老师"


def test_parent_profile(client: TestClient, db, student: User, teaching_class) -> None:
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

    headers = auth_header(client, "13900139000", "Parent123", "parent")
    res = client.get("/api/v1/parents/me/profile", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["real_name"] == "测试家长"
    assert len(data["children"]) == 1
    assert data["children"][0]["account"] == "stu001"
    assert "测试班" in data["class_names"]
