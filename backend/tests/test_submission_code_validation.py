from fastapi.testclient import TestClient

from app.models.problem import Problem
from app.models.user import User
from tests.conftest import auth_header


def test_submission_rejects_invalid_code(
    client: TestClient,
    student: User,
    problem: Problem,
) -> None:
    headers = auth_header(client, "stu001", "123456", "student")
    res = client.post(
        "/api/v1/submissions",
        json={
            "problem_id": problem.id,
            "code": "import os\nos.system('x')\nprint('hello world test')",
            "language": "Python",
        },
        headers=headers,
    )
    assert res.status_code == 400
    assert "不允许" in res.json()["message"]
