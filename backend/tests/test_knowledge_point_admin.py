"""Admin knowledge point CRUD tests."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User, UserRole
from tests.conftest import auth_header


def _admin_headers(client: TestClient, db: Session) -> dict[str, str]:
    admin = User(
        account="adminkp",
        password_hash=hash_password("Admin123"),
        role=UserRole.ADMIN,
        display_name="管理员",
    )
    db.add(admin)
    db.commit()
    return auth_header(client, "adminkp", "Admin123", "admin")


def test_admin_knowledge_point_crud(client: TestClient, db: Session, teacher: User) -> None:
    headers = _admin_headers(client, db)

    listed = client.get("/api/v1/admin/knowledge-points", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()["data"]["items"]) >= 1

    created = client.post(
        "/api/v1/admin/knowledge-points",
        headers=headers,
        json={
            "name": "测试知识点",
            "summary": "用于单元测试",
            "content_markdown": "## 描述\n测试内容",
            "sort_order": 50,
        },
    )
    assert created.status_code == 200
    point_id = created.json()["data"]["id"]

    updated = client.patch(
        f"/api/v1/admin/knowledge-points/{point_id}",
        headers=headers,
        json={"summary": "已更新摘要"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["summary"] == "已更新摘要"

    options = client.get(
        "/api/v1/practice/knowledge-point-options",
        headers=auth_header(client, "13800138000", "Teacher123", "teacher"),
    )
    assert options.status_code == 200
    names = {item["name"] for item in options.json()["data"]}
    assert "测试知识点" in names

    deleted = client.delete(f"/api/v1/admin/knowledge-points/{point_id}", headers=headers)
    assert deleted.status_code == 200
