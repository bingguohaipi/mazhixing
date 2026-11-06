"""Shared submission statistics helpers (PRD: late submissions excluded from regular stats)."""

from __future__ import annotations

from sqlalchemy.orm import Query, Session

from app.models.submission import Submission, SubmissionStatus

VALID_SUBMISSION_STATUSES = {
    SubmissionStatus.AC,
    SubmissionStatus.WA,
    SubmissionStatus.TLE,
    SubmissionStatus.RE,
}

WRONG_SUBMISSION_STATUSES = {
    SubmissionStatus.WA,
    SubmissionStatus.TLE,
    SubmissionStatus.RE,
}


def apply_regular_submission_filters(query: Query) -> Query:
    """Exclude late submissions and invalid (CE/PENDING) statuses."""
    return query.filter(
        Submission.is_late.is_(False),
        Submission.status.in_(VALID_SUBMISSION_STATUSES),
    )


def count_student_regular_submissions(db: Session, student_id: int) -> int:
    return (
        apply_regular_submission_filters(db.query(Submission))
        .filter(Submission.user_id == student_id)
        .count()
    )


def count_student_ac_submissions(db: Session, student_id: int) -> int:
    return (
        apply_regular_submission_filters(db.query(Submission))
        .filter(Submission.user_id == student_id, Submission.status == SubmissionStatus.AC)
        .count()
    )


def student_regular_accuracy(db: Session, student_id: int) -> float:
    total = count_student_regular_submissions(db, student_id)
    if total == 0:
        return 0.0
    ac = count_student_ac_submissions(db, student_id)
    return round(ac / total * 100, 1)


def count_student_completed_problems(db: Session, student_id: int) -> int:
    """Distinct problems with at least one regular AC submission."""
    rows = (
        apply_regular_submission_filters(db.query(Submission.problem_id))
        .filter(Submission.user_id == student_id, Submission.status == SubmissionStatus.AC)
        .distinct()
        .all()
    )
    return len(rows)
