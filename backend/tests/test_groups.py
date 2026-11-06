from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.class_model import TeachingClass
from app.models.user import User
from tests.conftest import auth_header


def test_create_and_assign_student_group(
    client: TestClient,
    db: Session,
    teacher: User,
    teaching_class: TeachingClass,
) -> None:
    headers = auth_header(client, "13800138000", "Teacher123", "teacher")

    create_res = client.post(
        f"/api/v1/classes/{teaching_class.id}/groups",
        headers=headers,
        json={"name": "A组"},
    )
    assert create_res.status_code == 200, create_res.text
    group_id = create_res.json()["data"]["id"]

    students_res = client.get(f"/api/v1/classes/{teaching_class.id}/students", headers=headers)
    student_id = students_res.json()["data"][0]["id"]

    assign_res = client.put(
        f"/api/v1/classes/{teaching_class.id}/students/{student_id}/group",
        headers=headers,
        json={"group_id": group_id},
    )
    assert assign_res.status_code == 200, assign_res.text
    assert assign_res.json()["data"]["group_name"] == "A组"
