from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.class_model import TeachingClass
from app.models.homework import Homework
from app.models.notice import Notice
from app.models.problem import Problem
from app.models.user import User
from tests.conftest import auth_header


def test_delete_homework_notifies_and_hides_from_teacher_list(
    client: TestClient,
    db: Session,
    teacher: User,
    teaching_class: TeachingClass,
    problem: Problem,
) -> None:
    headers = auth_header(client, "13800138000", "Teacher123", "teacher")
    now = datetime.now(timezone.utc)
    create_resp = client.post(
        "/api/v1/homework",
        headers=headers,
        json={
            "title": "待删除作业",
            "start_time": (now + timedelta(hours=1)).isoformat(),
            "end_time": (now + timedelta(days=2)).isoformat(),
            "allow_late_submission": False,
            "class_ids": [teaching_class.id],
            "problem_ids": [problem.id],
        },
    )
    homework_id = create_resp.json()["data"]["id"]

    delete_resp = client.delete(f"/api/v1/homework/{homework_id}", headers=headers)
    assert delete_resp.status_code == 200
    assert "通知" in delete_resp.json()["message"]

    hw = db.get(Homework, homework_id)
    assert hw is not None
    assert hw.deleted_at is not None

    list_resp = client.get("/api/v1/homework", headers=headers)
    ids = [item["id"] for item in list_resp.json()["data"]]
    assert homework_id not in ids

    assert db.query(Notice).filter(Notice.title.contains("已删除")).count() >= 1
