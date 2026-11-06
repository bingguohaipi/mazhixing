from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.class_model import TeachingClass
from app.models.user import User
from tests.conftest import auth_header


def test_roster_batch_and_enroll(client: TestClient, db: Session, teacher: User, teaching_class: TeachingClass) -> None:
    headers = auth_header(client, "13800138000", "Teacher123", "teacher")

    batch_res = client.post(
        "/api/v1/teacher/roster/batch",
        headers=headers,
        json={"names": [" roster甲 ", "roster乙"], "year": 2026},
    )
    assert batch_res.status_code == 200, batch_res.text
    created = batch_res.json()["data"]["created"]
    assert len(created) == 2
    assert created[0]["account"].startswith("stu2026")
    assert len(created[0]["account"]) == len("stu2026") + 3

    list_res = client.get("/api/v1/teacher/roster", headers=headers)
    assert list_res.status_code == 200
    assert list_res.json()["data"]["total"] >= 2

    student_ids = [item["student_id"] for item in created]
    enroll_res = client.post(
        f"/api/v1/classes/{teaching_class.id}/students/enroll",
        headers=headers,
        json={"student_ids": student_ids},
    )
    assert enroll_res.status_code == 200, enroll_res.text
    assert len(enroll_res.json()["data"]) == 2

    student_id = created[0]["student_id"]
    list_res2 = client.get("/api/v1/teacher/roster", headers=headers)
    item = next(i for i in list_res2.json()["data"]["items"] if i["id"] == student_id)
    assert "real_name" in item
    assert "nickname" in item
    assert "student_no" not in item

    update_res = client.put(
        f"/api/v1/teacher/roster/{student_id}",
        headers=headers,
        json={"display_name": "名册更新名"},
    )
    assert update_res.status_code == 403, update_res.text


def test_remove_student_then_re_enroll(
    client: TestClient,
    teacher: User,
    teaching_class: TeachingClass,
    student: User,
) -> None:
    headers = auth_header(client, "13800138000", "Teacher123", "teacher")
    student_id = student.id

    remove_res = client.delete(
        f"/api/v1/classes/{teaching_class.id}/students/{student_id}",
        headers=headers,
    )
    assert remove_res.status_code == 200, remove_res.text

    list_after = client.get(f"/api/v1/classes/{teaching_class.id}/students", headers=headers)
    assert list_after.status_code == 200
    assert student_id not in [s["id"] for s in list_after.json()["data"]]

    enroll_res = client.post(
        f"/api/v1/classes/{teaching_class.id}/students/enroll",
        headers=headers,
        json={"student_ids": [student_id]},
    )
    assert enroll_res.status_code == 200, enroll_res.text
    assert len(enroll_res.json()["data"]) == 1
    assert enroll_res.json()["data"][0]["id"] == student_id

    list_again = client.get(f"/api/v1/classes/{teaching_class.id}/students", headers=headers)
    assert student_id in [s["id"] for s in list_again.json()["data"]]
