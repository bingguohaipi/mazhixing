from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.class_model import TeachingClass
from app.models.user import User
from tests.conftest import auth_header


def test_teacher_publishes_notice(
    client: TestClient,
    teacher: User,
    teaching_class: TeachingClass,
) -> None:
    headers = auth_header(client, "13800138000", "Teacher123", "teacher")
    response = client.post(
        "/api/v1/notices",
        headers=headers,
        json={
            "title": "下周调课通知",
            "content": "下周六课程改为周日进行，请知悉。",
            "class_ids": [teaching_class.id],
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["title"] == "下周调课通知"
    assert teaching_class.name in data["class_names"][0] or data["class_names"]


def test_student_sees_notice_feed(
    client: TestClient,
    teacher: User,
    student: User,
    teaching_class: TeachingClass,
) -> None:
    teacher_headers = auth_header(client, "13800138000", "Teacher123", "teacher")
    client.post(
        "/api/v1/notices",
        headers=teacher_headers,
        json={
            "title": "作业提醒",
            "content": "请按时完成本周作业。",
            "class_ids": [teaching_class.id],
        },
    )

    student_headers = auth_header(client, "stu001", "123456", "student")
    response = client.get("/api/v1/notices/feed", headers=student_headers)
    assert response.status_code == 200
    items = response.json()["data"]
    assert len(items) == 1
    assert items[0]["title"] == "作业提醒"
    assert items[0]["is_read"] is False


def test_student_marks_notice_read(
    client: TestClient,
    teacher: User,
    student: User,
    teaching_class: TeachingClass,
) -> None:
    teacher_headers = auth_header(client, "13800138000", "Teacher123", "teacher")
    create = client.post(
        "/api/v1/notices",
        headers=teacher_headers,
        json={
            "title": "阅读测试",
            "content": "请点击确认已读。",
            "class_ids": [teaching_class.id],
        },
    )
    notice_id = create.json()["data"]["id"]

    student_headers = auth_header(client, "stu001", "123456", "student")
    read_resp = client.post(
        "/api/v1/notices/read",
        headers=student_headers,
        json={"notice_id": notice_id},
    )
    assert read_resp.status_code == 200, read_resp.text

    feed = client.get("/api/v1/notices/feed", headers=student_headers)
    item = next(row for row in feed.json()["data"] if row["id"] == notice_id)
    assert item["is_read"] is True


def test_teacher_cannot_use_other_teacher_class(
    client: TestClient,
    db: Session,
    teacher: User,
) -> None:
    from app.models.class_model import TeachingClass
    from app.core.security import hash_password
    from app.models.user import UserRole

    other = User(
        account="13900139001",
        phone="13900139001",
        password_hash=hash_password("Teacher123"),
        role=UserRole.TEACHER,
        display_name="其他教师",
    )
    db.add(other)
    db.flush()
    other_class = TeachingClass(
        teacher_id=other.id,
        name="他人班级",
        course_type="Python",
        schedule="周日",
        created_by=other.id,
        updated_by=other.id,
    )
    db.add(other_class)
    db.commit()

    headers = auth_header(client, "13800138000", "Teacher123", "teacher")
    response = client.post(
        "/api/v1/notices",
        headers=headers,
        json={
            "title": "越权测试",
            "content": "不应成功",
            "class_ids": [other_class.id],
        },
    )
    assert response.status_code == 400
