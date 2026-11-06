"""Student profile API tests."""

from fastapi.testclient import TestClient

from app.models.user import User
from tests.conftest import auth_header


def test_student_profile_and_nickname(client: TestClient, student: User) -> None:
    headers = auth_header(client, "stu001", "123456", "student")

    profile = client.get("/api/v1/students/me/profile", headers=headers)
    assert profile.status_code == 200
    data = profile.json()["data"]
    assert data["account"] == "stu001"
    assert data["real_name"] == "测试学生"
    assert "class_names" in data
    assert "teachers" in data
    assert "parents" in data

    bad = client.patch(
        "/api/v1/students/me/nickname",
        headers=headers,
        json={"nickname": "傻"},
    )
    assert bad.status_code == 422

    profanity = client.patch(
        "/api/v1/students/me/nickname",
        headers=headers,
        json={"nickname": "大傻逼"},
    )
    assert profanity.status_code == 422

    ok = client.patch(
        "/api/v1/students/me/nickname",
        headers=headers,
        json={"nickname": "小明同学"},
    )
    assert ok.status_code == 200
    assert ok.json()["data"]["nickname"] == "小明同学"

    me = client.get("/api/v1/auth/me", headers=headers)
    body = me.json()["data"]
    assert body["nickname"] == "小明同学"
    assert body["display_name"] == "小明同学"
    assert body["real_name"] == "测试学生"


def test_student_nickname_must_be_unique(client: TestClient, db, teacher: User, student: User) -> None:
    teacher.nickname = "CoolCat"
    db.commit()

    headers = auth_header(client, "stu001", "123456", "student")
    dup = client.patch(
        "/api/v1/students/me/nickname",
        headers=headers,
        json={"nickname": "coolcat"},
    )
    assert dup.status_code == 400
    assert "昵称" in dup.json()["message"]

    own = client.patch(
        "/api/v1/students/me/nickname",
        headers=headers,
        json={"nickname": "星宝二号"},
    )
    assert own.status_code == 200


def test_teacher_cannot_access_student_profile(client: TestClient, teacher: User) -> None:
    headers = auth_header(client, "13800138000", "Teacher123", "teacher")
    response = client.get("/api/v1/students/me/profile", headers=headers)
    assert response.status_code == 403
