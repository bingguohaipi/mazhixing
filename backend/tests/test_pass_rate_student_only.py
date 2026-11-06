"""通过率仅统计学生提交."""

from app.models.submission import Submission, SubmissionStatus
from app.models.user import UserRole
from app.services.submission_service import SubmissionService


def test_pass_rate_ignores_teacher_submissions(db, teacher, student, problem) -> None:
    db.add(
        Submission(
            user_id=teacher.id,
            problem_id=problem.id,
            code="print(1)",
            language="Python",
            status=SubmissionStatus.AC,
        )
    )
    db.add(
        Submission(
            user_id=student.id,
            problem_id=problem.id,
            code="print(2)",
            language="Python",
            status=SubmissionStatus.WA,
        )
    )
    db.commit()

    pass_rate, count = SubmissionService.compute_pass_rate(db, problem.id)
    assert count == 1
    assert pass_rate == 0.0
