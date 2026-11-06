"""Admin user list relation_summary."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.class_model import TeachingClass
from app.models.user import User, UserRole
from tests.conftest import auth_header


def _admin_headers(client: TestClient, db: Session):
    admin = User(
        account="adminrel",
        password_hash=hash_password("Admin123"),
        role=UserRole.ADMIN,
        display_name="管理员",
    )
    db.add(admin)
    db.commit()
    return auth_header(client, "adminrel", "Admin123", "admin")


def test_list_users_includes_relation_summary(
    client: TestClient,
    db: Session,
    teacher: User,
    student: User,
    teaching_class: TeachingClass,
) -> None:
    headers = _admin_headers(client, db)
    res = client.get("/api/v1/admin/users", headers=headers, params={"role": "student", "page_size": 50})
    assert res.status_code == 200, res.text
    items = res.json()["data"]["items"]
    row = next(i for i in items if i["id"] == student.id)
    assert row["relation_summary"]
    assert any("测试班" in line or teacher.display_name in line for line in row["relation_summary"])

    teacher_res = client.get(
        "/api/v1/admin/users",
        headers=headers,
        params={"role": "teacher", "page_size": 50},
    )
    trow = next(i for i in teacher_res.json()["data"]["items"] if i["id"] == teacher.id)
    assert "测试班" in trow["relation_summary"]
