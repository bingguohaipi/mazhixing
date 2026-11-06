"""Admin pet shop API tests."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.pet_catalog_defaults import ensure_shop_catalog
from tests.conftest import auth_header


def test_admin_patch_pet_shop_price(client: TestClient, db: Session) -> None:
    ensure_shop_catalog(db)
    from app.models.user import UserRole
    from app.core.security import hash_password

    admin = User(
        account="adminpet",
        password_hash=hash_password("Admin123"),
        role=UserRole.ADMIN,
        display_name="管理员",
    )
    db.add(admin)
    db.commit()

    headers = auth_header(client, "adminpet", "Admin123", "admin")
    res = client.patch(
        "/api/v1/admin/pet-shop/items/food_basic",
        headers=headers,
        json={"price": 6},
    )
    assert res.status_code == 200
    assert res.json()["data"]["price"] == 6

    cfg = client.get("/api/v1/admin/pet-points/config", headers=headers)
    assert cfg.status_code == 200
    assert cfg.json()["data"]["points_per_first_ac"] == 10


def test_admin_pet_shop_search_and_category_label(client: TestClient, db: Session) -> None:
    ensure_shop_catalog(db)
    from app.models.user import UserRole
    from app.core.security import hash_password

    admin = User(
        account="adminpet2",
        password_hash=hash_password("Admin123"),
        role=UserRole.ADMIN,
        display_name="管理员2",
    )
    db.add(admin)
    db.commit()

    headers = auth_header(client, "adminpet2", "Admin123", "admin")
    all_items = client.get("/api/v1/admin/pet-shop/items", headers=headers)
    assert all_items.status_code == 200
    first = all_items.json()["data"]["items"][0]
    assert first["category_label"] in ("宠物", "食物", "饮料")

    search = client.get("/api/v1/admin/pet-shop/items", headers=headers, params={"keyword": "橘"})
    assert search.status_code == 200
    assert len(search.json()["data"]["items"]) >= 1

    by_type = client.get("/api/v1/admin/pet-shop/items", headers=headers, params={"keyword": "食物"})
    assert by_type.status_code == 200
    assert all(item["category"] == "food" for item in by_type.json()["data"]["items"])

    create = client.post(
        "/api/v1/admin/pet-shop/items",
        headers=headers,
        json={
            "sku": "food_test_snack",
            "category": "food",
            "name": "测试零食",
            "description": "单元测试",
            "price": 9,
            "asset_key": "food_test_snack",
            "effect_exp": 10,
            "effect_satiety": 10,
        },
    )
    assert create.status_code == 200, create.text

    delete_ok = client.delete("/api/v1/admin/pet-shop/items/food_test_snack", headers=headers)
    assert delete_ok.status_code == 200
