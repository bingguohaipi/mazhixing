from fastapi.testclient import TestClient

from app.models.user import User
from tests.conftest import auth_header


def test_teacher_cannot_import_problems(client: TestClient, teacher: User) -> None:
    headers = auth_header(client, "13800138000", "Teacher123", "teacher")
    payload = {
        "problems": [
            {
                "title": "批量题1",
                "description": "输出 1",
                "languages": ["Python"],
                "difficulty": "入门",
                "gesp_level": "GESP1",
                "knowledge_points": ["输出"],
                "time_limit_ms": 1000,
                "memory_limit_mb": 256,
                "test_cases": [{"input_data": "1", "expected_output": "1\n", "is_sample": True}],
            },
        ]
    }
    response = client.post("/api/v1/problems/import", headers=headers, json=payload)
    assert response.status_code == 403, response.text


def test_teacher_cannot_export_lesson_pack(client: TestClient, teacher: User) -> None:
    headers = auth_header(client, "13800138000", "Teacher123", "teacher")
    response = client.get(
        "/api/v1/problems/lesson-pack/export",
        headers=headers,
        params={"ids": [1]},
    )
    assert response.status_code == 403, response.text
