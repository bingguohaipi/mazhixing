from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.problem import (
    GespLevel,
    Problem,
    ProblemDifficulty,
    ProblemLanguage,
    ProblemScope,
    PublicPublishStatus,
)
from app.models.user import User
from tests.conftest import auth_header


def test_teacher_create_custom_problem_for_homework(client: TestClient, teacher: User) -> None:
    headers = auth_header(client, "13800138000", "Teacher123", "teacher")
    payload = {
        "title": "课堂小测题",
        "description": "输出 hello",
        "languages": ["Python"],
        "difficulty": "入门",
        "gesp_level": "GESP1",
        "knowledge_points": ["输入输出"],
        "time_limit_ms": 1000,
        "memory_limit_mb": 256,
        "test_cases": [{"input_data": "1", "expected_output": "hello\n", "is_sample": True, "sort_order": 0}],
    }
    create_resp = client.post("/api/v1/problems", headers=headers, json=payload)
    assert create_resp.status_code == 200, create_resp.text
    created = create_resp.json()["data"]
    problem_id = created["id"]
    assert created.get("private_no") is not None and created["private_no"] >= 1

    custom_list = client.get("/api/v1/problems/custom", headers=headers)
    assert custom_list.status_code == 200
    ids = [item["id"] for item in custom_list.json()["data"]["items"]]
    assert problem_id in ids

    private_no = created["private_no"]
    by_title = client.get("/api/v1/problems/custom", headers=headers, params={"keyword": "课堂小测"})
    assert by_title.status_code == 200
    assert any(item["id"] == problem_id for item in by_title.json()["data"]["items"])

    by_no = client.get(
        "/api/v1/problems/custom",
        headers=headers,
        params={"keyword": f"#{private_no}"},
    )
    assert by_no.status_code == 200
    assert any(item["id"] == problem_id for item in by_no.json()["data"]["items"])

    delete_resp = client.delete(f"/api/v1/problems/{problem_id}", headers=headers)
    assert delete_resp.status_code == 200, delete_resp.text

    after = client.get("/api/v1/problems/custom", headers=headers)
    assert problem_id not in [item["id"] for item in after.json()["data"]["items"]]


def test_teacher_cannot_mutate_public_problem(client: TestClient, db: Session, teacher: User) -> None:
    headers = auth_header(client, "13800138000", "Teacher123", "teacher")
    public = Problem(
        teacher_id=teacher.id,
        scope=ProblemScope.PUBLIC,
        publish_status=PublicPublishStatus.PUBLISHED,
        version=1,
        title="公共题不可改",
        description="desc",
        language=ProblemLanguage.PYTHON,
        difficulty=ProblemDifficulty.BEGINNER,
        gesp_level=GespLevel.GESP1,
        time_limit_ms=1000,
        memory_limit_mb=256,
        created_by=teacher.id,
        updated_by=teacher.id,
    )
    db.add(public)
    db.flush()
    public.public_group_id = public.id
    db.commit()
    db.refresh(public)

    update_resp = client.put(
        f"/api/v1/problems/{public.id}",
        headers=headers,
        json={"title": "试图修改"},
    )
    assert update_resp.status_code == 403

    delete_resp = client.delete(f"/api/v1/problems/{public.id}", headers=headers)
    assert delete_resp.status_code == 403


def test_teacher_create_problem_without_input(client: TestClient, teacher: User) -> None:
    headers = auth_header(client, "13800138000", "Teacher123", "teacher")
    payload = {
        "title": "Hello World 无输入",
        "description": "仅输出一行 Hello World",
        "languages": ["C++"],
        "difficulty": "入门",
        "gesp_level": "GESP1",
        "knowledge_points": ["输出"],
        "time_limit_ms": 1000,
        "memory_limit_mb": 256,
        "test_cases": [{"input_data": "", "expected_output": "Hello World", "is_sample": True, "sort_order": 0}],
    }
    create_resp = client.post("/api/v1/problems", headers=headers, json=payload)
    assert create_resp.status_code == 200, create_resp.text
    detail = create_resp.json()["data"]
    assert detail.get("private_no") is not None and detail["private_no"] >= 1
    assert detail["test_cases"][0]["input_data"] == ""
    assert detail["test_cases"][0]["expected_output"] == "Hello World"
