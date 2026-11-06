from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.class_model import TeachingClass
from app.models.problem import Problem
from app.models.user import User
from tests.conftest import auth_header


def test_create_homework(client: TestClient, teacher: User, teaching_class: TeachingClass, problem: Problem) -> None:
    headers = auth_header(client, "13800138000", "Teacher123", "teacher")
    now = datetime.now(timezone.utc)
    response = client.post(
        "/api/v1/homework",
        headers=headers,
        json={
            "title": "第一次作业",
            "description": "练习 A+B",
            "start_time": now.isoformat(),
            "end_time": (now + timedelta(days=7)).isoformat(),
            "allow_late_submission": False,
            "class_ids": [teaching_class.id],
            "problem_ids": [problem.id],
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["title"] == "第一次作业"
    assert data["status"] == "进行中"


def test_homework_rejects_problem_without_test_cases(
    client: TestClient,
    db: Session,
    teacher: User,
    teaching_class: TeachingClass,
) -> None:
    from app.models.problem import GespLevel, ProblemDifficulty, ProblemLanguage

    empty_problem = Problem(
        teacher_id=teacher.id,
        title="无测试用例",
        description="test",
        language=ProblemLanguage.PYTHON,
        difficulty=ProblemDifficulty.EASY,
        gesp_level=GespLevel.GESP1,
        knowledge_point="测试",
        time_limit_ms=1000,
        memory_limit_mb=256,
        created_by=teacher.id,
        updated_by=teacher.id,
    )
    db.add(empty_problem)
    db.commit()
    db.refresh(empty_problem)

    headers = auth_header(client, "13800138000", "Teacher123", "teacher")
    now = datetime.now(timezone.utc)
    response = client.post(
        "/api/v1/homework",
        headers=headers,
        json={
            "title": "无效作业",
            "start_time": now.isoformat(),
            "end_time": (now + timedelta(days=1)).isoformat(),
            "allow_late_submission": False,
            "class_ids": [teaching_class.id],
            "problem_ids": [empty_problem.id],
        },
    )
    assert response.status_code == 400


def test_student_sees_assigned_homework(
    client: TestClient,
    teacher: User,
    teaching_class: TeachingClass,
    problem: Problem,
) -> None:
    teacher_headers = auth_header(client, "13800138000", "Teacher123", "teacher")
    now = datetime.now(timezone.utc)
    client.post(
        "/api/v1/homework",
        headers=teacher_headers,
        json={
            "title": "学生可见作业",
            "start_time": now.isoformat(),
            "end_time": (now + timedelta(days=3)).isoformat(),
            "allow_late_submission": False,
            "class_ids": [teaching_class.id],
            "problem_ids": [problem.id],
        },
    )

    student_headers = auth_header(client, "stu001", "123456", "student")
    response = client.get("/api/v1/homework/my", headers=student_headers)
    assert response.status_code == 200
    items = response.json()["data"]
    assert len(items) == 1
    assert items[0]["title"] == "学生可见作业"


def test_homework_stats_require_all_problems_ac(
    client: TestClient,
    db: Session,
    teacher: User,
    student: User,
    teaching_class: TeachingClass,
    problem: Problem,
) -> None:
    from app.models.problem import GespLevel, ProblemDifficulty, ProblemLanguage
    from app.models.submission import Submission, SubmissionStatus

    problem_two = Problem(
        teacher_id=teacher.id,
        title="第二题",
        description="输出 2",
        language=ProblemLanguage.PYTHON,
        difficulty=ProblemDifficulty.EASY,
        gesp_level=GespLevel.GESP1,
        knowledge_point="输出",
        time_limit_ms=1000,
        memory_limit_mb=256,
        created_by=teacher.id,
        updated_by=teacher.id,
    )
    db.add(problem_two)
    db.flush()
    from app.models.problem import TestCase

    db.add(
        TestCase(
            problem_id=problem_two.id,
            input_data="",
            expected_output="2",
            is_sample=True,
            sort_order=0,
        )
    )
    db.commit()
    db.refresh(problem_two)

    headers = auth_header(client, "13800138000", "Teacher123", "teacher")
    now = datetime.now(timezone.utc)
    create_resp = client.post(
        "/api/v1/homework",
        headers=headers,
        json={
            "title": "两题作业",
            "start_time": now.isoformat(),
            "end_time": (now + timedelta(days=2)).isoformat(),
            "allow_late_submission": False,
            "class_ids": [teaching_class.id],
            "problem_ids": [problem.id, problem_two.id],
        },
    )
    assert create_resp.status_code == 200, create_resp.text
    homework_id = create_resp.json()["data"]["id"]

    db.add(
        Submission(
            user_id=student.id,
            problem_id=problem.id,
            homework_id=homework_id,
            language=ProblemLanguage.PYTHON,
            code="print(1)",
            status=SubmissionStatus.AC,
            is_late=False,
        )
    )
    db.commit()

    list_resp = client.get("/api/v1/homework", headers=headers)
    assert list_resp.status_code == 200
    item = next(row for row in list_resp.json()["data"] if row["id"] == homework_id)
    assert item["problem_count"] == 2
    assert item["submitted_count"] == 0
    assert item["correct_count"] == 0
    assert item["wrong_count"] == 0
    assert item["progress_done"] == 1
    assert item["progress_total"] == 2

    report_resp = client.get(f"/api/v1/homework/{homework_id}/submission-report", headers=headers)
    assert report_resp.status_code == 200, report_resp.text
    report = report_resp.json()["data"]
    assert report["problem_count"] == 2
    assert report["all_ac_students"] == []
    student_row = next(row for row in report["students"] if row["student_id"] == student.id)
    assert student_row["ac_count"] == 1
    assert student_row["all_ac"] is False
    assert student_row["problems"][0]["status"] == "AC"
    assert student_row["problems"][1]["status"] is None

    sub_id = student_row["problems"][0]["submission_id"]
    assert sub_id is not None
    code_resp = client.get(
        f"/api/v1/homework/{homework_id}/submissions/{sub_id}",
        headers=headers,
    )
    assert code_resp.status_code == 200
    assert "print(1)" in code_resp.json()["data"]["code"]

    db.add(
        Submission(
            user_id=student.id,
            problem_id=problem_two.id,
            homework_id=homework_id,
            language=ProblemLanguage.PYTHON,
            code="print(2)",
            status=SubmissionStatus.WA,
            is_late=False,
        )
    )
    db.commit()

    list_after = client.get("/api/v1/homework", headers=headers)
    item_after = next(row for row in list_after.json()["data"] if row["id"] == homework_id)
    assert item_after["submitted_count"] == 1
    assert item_after["correct_count"] == 0
    assert item_after["wrong_count"] == 1
