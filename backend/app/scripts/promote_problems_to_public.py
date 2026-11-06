"""One-time / idempotent: move legacy private problems into the public catalog."""

from sqlalchemy.orm import Session

from app.models.problem import Problem, ProblemScope, PublicPublishStatus


def promote_private_problems_to_public(db: Session) -> int:
    """Manual one-off: promote legacy private rows without private_no (pre–自有题库)."""
    rows = (
        db.query(Problem)
        .filter(
            Problem.deleted_at.is_(None),
            Problem.scope == ProblemScope.PRIVATE,
            Problem.private_no.is_(None),
        )
        .all()
    )
    if not rows:
        return 0

    for problem in rows:
        problem.scope = ProblemScope.PUBLIC
        if problem.publish_status == PublicPublishStatus.DRAFT:
            problem.publish_status = PublicPublishStatus.PUBLISHED
        if problem.public_group_id is None:
            problem.public_group_id = problem.id
        if problem.version is None or problem.version < 1:
            problem.version = 1

    db.commit()
    return len(rows)
