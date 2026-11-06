from sqlalchemy.orm import Session

from app.models.problem import Problem, ProblemScope, PublicPublishStatus
from app.models.user import User
from app.scripts.promote_problems_to_public import promote_private_problems_to_public


def test_promote_private_problems_to_public(db: Session, teacher: User) -> None:
    private = Problem(
        teacher_id=teacher.id,
        scope=ProblemScope.PRIVATE,
        publish_status=PublicPublishStatus.PUBLISHED,
        title="旧私有题",
        description="desc",
        language="Python",
        difficulty="入门",
        gesp_level="GESP1",
        time_limit_ms=1000,
        memory_limit_mb=256,
        created_by=teacher.id,
        updated_by=teacher.id,
    )
    db.add(private)
    db.commit()
    db.refresh(private)

    count = promote_private_problems_to_public(db)
    assert count == 1

    db.refresh(private)
    assert private.scope == ProblemScope.PUBLIC
    assert private.public_group_id == private.id
    assert private.publish_status == PublicPublishStatus.PUBLISHED


def test_promote_skips_teacher_custom_with_private_no(db: Session, teacher: User) -> None:
    custom = Problem(
        teacher_id=teacher.id,
        scope=ProblemScope.PRIVATE,
        private_no=1,
        publish_status=PublicPublishStatus.PUBLISHED,
        title="教师自有题",
        description="desc",
        language="Python",
        difficulty="入门",
        gesp_level="GESP1",
        time_limit_ms=1000,
        memory_limit_mb=256,
        created_by=teacher.id,
        updated_by=teacher.id,
    )
    db.add(custom)
    db.commit()

    count = promote_private_problems_to_public(db)
    assert count == 0

    db.refresh(custom)
    assert custom.scope == ProblemScope.PRIVATE
