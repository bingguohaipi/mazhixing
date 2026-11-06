"""Pet points and shop API tests."""

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.pet import PetSystemConfig, PointFirstAcGrant, StudentPointsAccount
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User
from app.services.pet_catalog_defaults import ensure_shop_catalog
from app.services.pet_points_service import PetPointsService
from tests.conftest import auth_header


def _ensure_pet_config(db: Session) -> None:
    ensure_shop_catalog(db)
    config = PetSystemConfig(id=1, points_launched_at=datetime.now(timezone.utc), points_per_first_ac=10)
    db.merge(config)
    db.commit()


def test_points_grant_and_shop(client: TestClient, db: Session, student: User, problem) -> None:
    _ensure_pet_config(db)
    headers = auth_header(client, "stu001", "123456", "student")

    submission = Submission(
        user_id=student.id,
        problem_id=problem.id,
        homework_id=None,
        code="print(1)",
        language="Python",
        status=SubmissionStatus.AC,
        is_late=False,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    PetPointsService(db).try_grant_first_ac(submission)

    points = client.get("/api/v1/students/me/points", headers=headers)
    assert points.status_code == 200
    assert points.json()["data"]["balance"] == 10

    PetPointsService(db).try_grant_first_ac(submission)
    points2 = client.get("/api/v1/students/me/points", headers=headers)
    assert points2.json()["data"]["balance"] == 10

    catalog = client.get("/api/v1/students/me/pet-shop/catalog", headers=headers)
    assert catalog.status_code == 200
    assert len(catalog.json()["data"]["items"]) >= 7

    buy = client.post(
        "/api/v1/students/me/pet-shop/orders",
        headers=headers,
        json={"sku": "food_basic", "quantity": 2},
    )
    assert buy.status_code == 200
    assert buy.json()["data"]["balance"] == 0

    buy_pet = client.post(
        "/api/v1/students/me/pet-shop/orders",
        headers=headers,
        json={"sku": "pet_cat_orange", "quantity": 1},
    )
    assert buy_pet.status_code == 400

    account = db.get(StudentPointsAccount, student.id)
    assert account is not None
    account.balance = 100
    db.commit()

    buy_pet_ok = client.post(
        "/api/v1/students/me/pet-shop/orders",
        headers=headers,
        json={"sku": "pet_cat_orange", "quantity": 1},
    )
    assert buy_pet_ok.status_code == 200

    active = client.get("/api/v1/students/me/pets/active", headers=headers)
    assert active.status_code == 200
    assert active.json()["data"]["catalog_sku"] == "pet_cat_orange"

    use = client.post(
        "/api/v1/students/me/inventory/use",
        headers=headers,
        json={"sku": "food_basic", "quantity": 1},
    )
    assert use.status_code == 200
    assert use.json()["data"]["pet"]["satiety"] >= 80


def test_teacher_cannot_access_points(client: TestClient, db: Session, teacher: User) -> None:
    _ensure_pet_config(db)
    headers = auth_header(client, "13800138000", "Teacher123", "teacher")
    response = client.get("/api/v1/students/me/points", headers=headers)
    assert response.status_code == 403


def test_submission_detail_points_field(
    client: TestClient, db: Session, student: User, problem, teaching_class
) -> None:
    _ensure_pet_config(db)
    headers = auth_header(client, "stu001", "123456", "student")

    submission = Submission(
        user_id=student.id,
        problem_id=problem.id,
        homework_id=None,
        code="print(1)",
        language="Python",
        status=SubmissionStatus.AC,
        is_late=False,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    PetPointsService(db).try_grant_first_ac(submission)

    detail = client.get(f"/api/v1/submissions/{submission.id}", headers=headers)
    assert detail.status_code == 200
    data = detail.json()["data"]
    assert data["points_awarded"] == 10
    assert data["points_balance"] is not None

    grant_count = db.query(PointFirstAcGrant).filter(PointFirstAcGrant.student_id == student.id).count()
    assert grant_count == 1
