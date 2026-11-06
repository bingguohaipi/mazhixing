"""Pet satiety decay unit and integration tests."""

from datetime import datetime, timedelta, timezone

from app.services.pet_decay import (
    MAX_DECAY_INTERVALS_PER_SYNC,
    MOOD_DECAY_NORMAL,
    MOOD_DECAY_WHEN_STARVING,
    SATIETY_DECAY_AMOUNT,
    SATIETY_DECAY_INTERVAL_MINUTES,
    compute_decay,
)


def test_compute_decay_no_elapsed() -> None:
    now = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)
    sat, mood, last = compute_decay(80, 70, now, now + timedelta(minutes=10))
    assert sat == 80
    assert mood == 70
    assert last == now


def test_compute_decay_45_minutes() -> None:
    start = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)
    end = start + timedelta(minutes=45)
    sat, mood, _ = compute_decay(80, 70, start, end)
    assert sat == 80 - SATIETY_DECAY_AMOUNT
    assert mood == 70 - MOOD_DECAY_NORMAL


def test_compute_decay_90_minutes() -> None:
    start = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)
    end = start + timedelta(minutes=89)
    sat, mood, _ = compute_decay(80, 70, start, end)
    assert sat == 80 - SATIETY_DECAY_AMOUNT * 2
    assert mood == 70 - MOOD_DECAY_NORMAL * 2


def test_compute_decay_starving_reduces_mood() -> None:
    start = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)
    end = start + timedelta(minutes=60)
    sat, mood, _ = compute_decay(3, 50, start, end)
    assert sat == 0
    assert mood == 50 - MOOD_DECAY_NORMAL * 2 - MOOD_DECAY_WHEN_STARVING * 2


def test_compute_decay_caps_intervals() -> None:
    start = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)
    end = start + timedelta(days=30)
    sat, _, _ = compute_decay(100, 80, start, end)
    assert sat == max(0, 100 - SATIETY_DECAY_AMOUNT * MAX_DECAY_INTERVALS_PER_SYNC)


def test_active_pet_sync_decay_integration(client, db, student) -> None:
    from app.models.pet import StudentPet
    from app.services.pet_catalog_defaults import ensure_shop_catalog
    from tests.conftest import auth_header

    ensure_shop_catalog(db)
    pet = StudentPet(
        student_id=student.id,
        catalog_sku="pet_cat_orange",
        is_active=True,
        satiety=80,
        mood=70,
        last_decay_at=datetime.now(timezone.utc) - timedelta(minutes=45),
    )
    db.add(pet)
    db.commit()

    headers = auth_header(client, "stu001", "123456", "student")
    res = client.post("/api/v1/students/me/pets/sync", headers=headers, json={})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["satiety"] == 80 - SATIETY_DECAY_AMOUNT


def test_play_with_pet_increases_mood(client, db, student) -> None:
    from app.models.pet import StudentPet
    from app.services.pet_catalog_defaults import ensure_shop_catalog
    from tests.conftest import auth_header

    ensure_shop_catalog(db)
    pet = StudentPet(
        student_id=student.id,
        catalog_sku="pet_cat_orange",
        is_active=True,
        satiety=60,
        mood=40,
        last_decay_at=datetime.now(timezone.utc),
    )
    db.add(pet)
    db.commit()

    headers = auth_header(client, "stu001", "123456", "student")
    res = client.post("/api/v1/students/me/pets/active/play", headers=headers)
    assert res.status_code == 200
    body = res.json()["data"]
    assert body["mood_delta"] >= 4
    assert body["reaction"] in ("jump", "happy", "wiggle")
    assert body["pet"]["mood"] == 40 + body["mood_delta"]
