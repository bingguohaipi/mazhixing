"""班级课程类型与学生默认编程语言。"""

from fastapi.testclient import TestClient

from app.models.user import User
from tests.conftest import auth_header


def test_create_class_rejects_invalid_course_type(client: TestClient, teacher: User) -> None:
    headers = auth_header(client, teacher.account, "Teacher123", "teacher")
    res = client.post(
        "/api/v1/classes",
        headers=headers,
        json={
            "name": "测试班",
            "course_type": "Scratch创意",
            "schedule": "周六 10:00",
        },
    )
    assert res.status_code == 422


def test_create_class_rejects_duplicate_name(
    client: TestClient,
    teacher: User,
    teaching_class,
) -> None:
    headers = auth_header(client, teacher.account, "Teacher123", "teacher")
    res = client.post(
        "/api/v1/classes",
        headers=headers,
        json={
            "name": teaching_class.name,
            "course_type": "Python",
            "schedule": "周日 10:00",
        },
    )
    assert res.status_code == 400
    assert res.json()["message"] == "班级名称已存在"


def test_create_class_accepts_python(client: TestClient, teacher: User) -> None:
    headers = auth_header(client, teacher.account, "Teacher123", "teacher")
    res = client.post(
        "/api/v1/classes",
        headers=headers,
        json={
            "name": "Python班",
            "course_type": "Python",
            "schedule": "周六 10:00",
        },
    )
    assert res.status_code == 200
    assert res.json()["data"]["course_type"] == "Python"


def test_student_me_includes_default_coding_language(
    client: TestClient,
    student: User,
    teaching_class,  # noqa: ARG001 — enrolls student in C++ class
) -> None:
    headers = auth_header(client, "stu001", "123456", "student")
    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["data"]["default_coding_language"] == "C++"
