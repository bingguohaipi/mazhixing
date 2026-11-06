"""学生默认编程语言（由所在班级课程类型决定）。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.class_model import ClassEnrollment, TeachingClass
from app.utils.class_course_type import course_type_to_coding_language


def resolve_student_default_coding_language(db: Session, student_id: int) -> str | None:
    """取最近加入的有效班级的课程语言；无班级或无法解析时返回 None。"""
    row = (
        db.query(TeachingClass.course_type)
        .join(ClassEnrollment, ClassEnrollment.class_id == TeachingClass.id)
        .filter(
            ClassEnrollment.student_id == student_id,
            ClassEnrollment.deleted_at.is_(None),
            TeachingClass.deleted_at.is_(None),
        )
        .order_by(ClassEnrollment.id.desc())
        .first()
    )
    if row is None:
        return None
    return course_type_to_coding_language(row[0])
