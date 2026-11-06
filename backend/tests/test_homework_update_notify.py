from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.class_model import TeachingClass
from app.models.notice import Notice
from app.models.problem import GespLevel, Problem, ProblemDifficulty, ProblemLanguage
from app.models.problem import TestCase as ProblemTestCase
from app.models.user import User
from tests.conftest import auth_header


def _create_problem(db: Session, teacher: User, title: str) -> Problem:
    item = Problem(
        teacher_id=teacher.id,
        title=title,
        description="desc",
        language=ProblemLanguage.PYTHON,
        difficulty=ProblemDifficulty.EASY,
        gesp_level=GespLevel.GESP1,
        knowledge_point="测试",
        time_limit_ms=1000,
        memory_limit_mb=256,
        created_by=teacher.id,
        updated_by=teacher.id,
    )
    db.add(item)
    db.flush()
    db.add(
        ProblemTestCase(
            problem_id=item.id,
            input_data="1\n",
            expected_output="1\n",
            is_sample=True,
            sort_order=0,
        )
    )
    db.commit()
    db.refresh(item)
    return item


def test_in_progress_homework_update_notifies_students(
    client: TestClient,
    db: Session,
    teacher: User,
    student: User,
    teaching_class: TeachingClass,
    problem: Problem,
) -> None:
    problem2 = _create_problem(db, teacher, "第二题")
    teacher_headers = auth_header(client, "13800138000", "Teacher123", "teacher")
    now = datetime.now(timezone.utc)
    create_resp = client.post(
        "/api/v1/homework",
        headers=teacher_headers,
        json={
            "title": "可修改作业",
            "start_time": now.isoformat(),
            "end_time": (now + timedelta(days=3)).isoformat(),
            "allow_late_submission": False,
            "class_ids": [teaching_class.id],
            "problem_ids": [problem.id],
        },
    )
    homework_id = create_resp.json()["data"]["id"]

    update_resp = client.put(
        f"/api/v1/homework/{homework_id}",
        headers=teacher_headers,
        json={
            "title": "可修改作业",
            "problem_ids": [problem.id, problem2.id],
            "end_time": (now + timedelta(days=5)).isoformat(),
        },
    )
    assert update_resp.status_code == 200, update_resp.text
    assert "通知" in update_resp.json()["message"]

    notice_count = db.query(Notice).filter(Notice.title.contains("已更新")).count()
    assert notice_count == 1

    student_headers = auth_header(client, "stu001", "123456", "student")
    list_resp = client.get("/api/v1/homework/my", headers=student_headers)
    items = list_resp.json()["data"]
    target = next(item for item in items if item["id"] == homework_id)
    assert target["has_unread_update"] is True

    ack_resp = client.post(f"/api/v1/homework/my/{homework_id}/ack-update", headers=student_headers)
    assert ack_resp.status_code == 200

    list_resp2 = client.get("/api/v1/homework/my", headers=student_headers)
    items2 = list_resp2.json()["data"]
    target2 = next(item for item in items2 if item["id"] == homework_id)
    assert target2["has_unread_update"] is False
