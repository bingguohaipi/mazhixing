from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User, UserRole
from tests.conftest import auth_header


def test_admin_create_student_auto_account(client: TestClient, db: Session) -> None:
    admin = User(
        account="adminstu",
        password_hash=hash_password("Admin123"),
        role=UserRole.ADMIN,
        display_name="管理员",
    )
    db.add(admin)
    db.commit()
    headers = auth_header(client, "adminstu", "Admin123", "admin")

    response = client.post(
        "/api/v1/admin/users",
        headers=headers,
        json={"role": "student", "display_name": "测试新生"},
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["role"] == "student"
    assert data["display_name"] == "测试新生"
    assert data["account"].startswith("stu")
    assert data["student_no"]
