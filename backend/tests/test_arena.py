"""Arena (擂台) API tests."""

from fastapi.testclient import TestClient

from app.models.problem import Problem
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User
from app.services.submission_service import SubmissionService
from tests.conftest import auth_header


def _patch_ac_judge(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.submission_service.acquire_judge_lock",
        lambda *args, **kwargs: None,
    )

    def fake_run_judge(self, submission_id: int) -> None:
        submission = self.db.query(Submission).filter(Submission.id == submission_id).first()
        if submission is None:
            return
        submission.status = SubmissionStatus.AC
        submission.runtime_ms = 10
        self.db.commit()
        if submission.arena_session_id is not None:
            from app.services.arena_service import ArenaService

            ArenaService(self.db).process_after_judge(submission_id)

    monkeypatch.setattr(SubmissionService, "run_judge", fake_run_judge)


def use_python_problem(db, problem: Problem) -> None:
    from app.models.problem import ProblemLanguage

    problem.language = ProblemLanguage.PYTHON
    problem.languages = ["Python", "C++"]
    db.commit()


def test_arena_problem_list_optional_language_filter(
    client: TestClient,
    db,
    student: User,
    problem: Problem,
) -> None:
    headers = auth_header(client, "stu001", "123456", "student")
    all_langs = client.get("/api/v1/practice/arena/problems", headers=headers, params={"page": 1, "page_size": 50})
    assert all_langs.status_code == 200
    assert problem.id in [item["id"] for item in all_langs.json()["data"]["items"]]

    cpp = client.get(
        "/api/v1/practice/arena/problems",
        headers=headers,
        params={"page": 1, "page_size": 50, "language": "C++"},
    )
    assert cpp.status_code == 200
    cpp_ids = [item["id"] for item in cpp.json()["data"]["items"]]
    assert problem.id in cpp_ids
    assert all("C++" in item.get("languages", [item["language"]]) for item in cpp.json()["data"]["items"])

    python = client.get(
        "/api/v1/practice/arena/problems",
        headers=headers,
        params={"page": 1, "page_size": 50, "language": "Python"},
    )
    assert python.status_code == 200
    python_ids = [item["id"] for item in python.json()["data"]["items"]]
    assert problem.id not in python_ids

    use_python_problem(db, problem)
    python2 = client.get(
        "/api/v1/practice/arena/problems",
        headers=headers,
        params={"page": 1, "page_size": 50, "language": "Python"},
    )
    assert problem.id in [item["id"] for item in python2.json()["data"]["items"]]


def test_arena_session_submit_and_board(
    client: TestClient,
    db,
    student: User,
    problem: Problem,
    monkeypatch,
) -> None:
    _patch_ac_judge(monkeypatch)
    use_python_problem(db, problem)
    headers = auth_header(client, "stu001", "123456", "student")

    agree = client.post("/api/v1/practice/arena/agreement", headers=headers)
    assert agree.status_code == 200

    create = client.post(
        "/api/v1/practice/arena/sessions",
        headers=headers,
        json={"problem_id": problem.id, "language": "Python"},
    )
    assert create.status_code == 200, create.text
    session_id = create.json()["data"]["id"]

    submit = client.post(
        f"/api/v1/practice/arena/sessions/{session_id}/submit",
        headers=headers,
        json={"code": "a, b = map(int, input().split())\nprint(a + b)\n"},
    )
    assert submit.status_code == 200, submit.text
    assert submit.json()["data"]["status"] == "AC"

    board = client.get(
        f"/api/v1/practice/arena/problems/{problem.id}/board",
        headers=headers,
        params={"language": "Python"},
    )
    assert board.status_code == 200
    data = board.json()["data"]
    assert data["my_status"] == "on_board"
    assert len(data["entries"]) >= 1
    assert data["entries"][0]["display_name"] == "测试学生"

    global_board = client.get(
        "/api/v1/practice/arena/leaderboard",
        headers=headers,
        params={"language": "Python"},
    )
    assert global_board.status_code == 200
    gdata = global_board.json()["data"]
    assert gdata["total_participants"] >= 1
    assert gdata["my_entry"] is not None
    assert gdata["my_entry"]["problems_passed"] == 1
    assert gdata["my_entry"]["attempt_count"] == 1


def test_arena_single_submit_only(
    client: TestClient,
    db,
    student: User,
    problem: Problem,
    monkeypatch,
) -> None:
    _patch_ac_judge(monkeypatch)
    use_python_problem(db, problem)
    headers = auth_header(client, "stu001", "123456", "student")
    client.post("/api/v1/practice/arena/agreement", headers=headers)

    session_id = client.post(
        "/api/v1/practice/arena/sessions",
        headers=headers,
        json={"problem_id": problem.id, "language": "Python"},
    ).json()["data"]["id"]

    code = "print(1)\n"
    first = client.post(
        f"/api/v1/practice/arena/sessions/{session_id}/submit",
        headers=headers,
        json={"code": code},
    )
    assert first.status_code == 200

    second = client.post(
        f"/api/v1/practice/arena/sessions/{session_id}/submit",
        headers=headers,
        json={"code": code},
    )
    assert second.status_code == 400


def test_global_leaderboard_composite_includes_passed_weight() -> None:
    from app.services.arena_service import ArenaService

    max_passed = 2
    more_passed = ArenaService._global_composite_score(2, max_passed, 0.5, 0.5)
    less_passed = ArenaService._global_composite_score(1, max_passed, 0.5, 0.5)
    assert more_passed > less_passed

    tied_pass_a = ArenaService._global_composite_score(2, max_passed, 0.5, 0.8)
    tied_pass_b = ArenaService._global_composite_score(2, max_passed, 0.9, 0.2)
    assert tied_pass_b > tied_pass_a
