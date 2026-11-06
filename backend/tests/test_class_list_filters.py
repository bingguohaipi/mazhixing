"""班级列表筛选。"""

from fastapi.testclient import TestClient

from app.models.class_model import TeachingClass
from app.models.user import User
from tests.conftest import auth_header


def test_list_classes_filter_by_weekday_course_and_time(
    client: TestClient,
    db,
    teacher: User,
) -> None:
    for name, course, schedule in [
        ("Python周六班", "Python", "周六 14:00-16:00"),
        ("Cpp周日班", "C++", "周日 10:00-12:00"),
    ]:
        db.add(
            TeachingClass(
                teacher_id=teacher.id,
                name=name,
                course_type=course,
                schedule=schedule,
                created_by=teacher.id,
                updated_by=teacher.id,
            )
        )
    db.commit()

    headers = auth_header(client, teacher.account, "Teacher123", "teacher")
    res = client.get(
        "/api/v1/classes",
        headers=headers,
        params={"weekday": "周六", "course_type": "Python"},
    )
    assert res.status_code == 200
    names = [item["name"] for item in res.json()["data"]]
    assert names == ["Python周六班"]
