from app.core.security import hash_password
from app.models.problem import GespLevel, Problem, ProblemDifficulty, ProblemLanguage
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User, UserRole
from app.services.ai_service import AiService


def test_fallback_includes_highlight_from_error_message(db) -> None:
    teacher = User(account="t1", password_hash=hash_password("x"), role=UserRole.TEACHER)
    db.add(teacher)
    db.flush()
    problem = Problem(
        teacher_id=teacher.id,
        title="P",
        description="d",
        language=ProblemLanguage.PYTHON,
        difficulty=ProblemDifficulty.EASY,
        gesp_level=GespLevel.GESP1,
        created_by=teacher.id,
        updated_by=teacher.id,
    )
    db.add(problem)
    db.flush()
    submission = Submission(
        user_id=teacher.id,
        problem_id=problem.id,
        code="print(1)",
        language="Python",
        status=SubmissionStatus.RE,
        error_message="IndexError on line 12",
    )
    db.add(submission)
    db.commit()

    service = AiService(db)
    text, lines = service._fallback_analysis(problem, submission, [])
    assert "错误分析" in text
    assert 12 in lines
