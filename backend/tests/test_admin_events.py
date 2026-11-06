from app.core.security import hash_password
from app.models.user import User, UserRole
from fastapi.testclient import TestClient


def test_admin_events_summary(client: TestClient, db) -> None:
    admin = User(
        account="admin_events",
        password_hash=hash_password("Admin123"),
        role=UserRole.ADMIN,
        display_name="Admin",
    )
    db.add(admin)
    db.commit()

    login = client.post(
        "/api/v1/auth/login",
        json={"account": "admin_events", "password": "Admin123", "role": "admin"},
    )
    token = login.json()["data"]["tokens"]["access_token"]
    res = client.get(
        "/api/v1/admin/events/summary",
        headers={"Authorization": f"Bearer {token}"},
        params={"days": 7},
    )
    assert res.status_code == 200
    assert res.json()["code"] == 200
    assert "total_events" in res.json()["data"]
