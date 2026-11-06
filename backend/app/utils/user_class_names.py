"""Resolve class names by user role."""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.audit import ParentStudentBinding
from app.models.class_model import ClassEnrollment, TeachingClass
from app.models.user import User, UserRole


def student_class_names(db: Session, student_id: int) -> list[str]:
    rows = (
        db.query(TeachingClass.name)
        .join(ClassEnrollment, ClassEnrollment.class_id == TeachingClass.id)
        .filter(
            ClassEnrollment.student_id == student_id,
            ClassEnrollment.deleted_at.is_(None),
            TeachingClass.deleted_at.is_(None),
        )
        .order_by(TeachingClass.name.asc())
        .all()
    )
    return [name for (name,) in rows]


def teacher_class_names(db: Session, teacher_id: int) -> list[str]:
    rows = (
        db.query(TeachingClass.name)
        .filter(
            TeachingClass.teacher_id == teacher_id,
            TeachingClass.deleted_at.is_(None),
        )
        .order_by(TeachingClass.name.asc())
        .all()
    )
    return [name for (name,) in rows]


def parent_class_names(db: Session, parent_id: int) -> list[str]:
    student_ids = [
        row[0]
        for row in db.query(ParentStudentBinding.student_id)
        .filter(ParentStudentBinding.parent_id == parent_id)
        .all()
    ]
    if not student_ids:
        return []
    names: set[str] = set()
    rows = (
        db.query(TeachingClass.name)
        .join(ClassEnrollment, ClassEnrollment.class_id == TeachingClass.id)
        .filter(
            ClassEnrollment.student_id.in_(student_ids),
            ClassEnrollment.deleted_at.is_(None),
            TeachingClass.deleted_at.is_(None),
        )
        .all()
    )
    for (name,) in rows:
        names.add(name)
    return sorted(names)


def class_names_for_users(db: Session, users: list[User]) -> dict[int, list[str]]:
    if not users:
        return {}
    by_role: dict[UserRole, list[int]] = defaultdict(list)
    for user in users:
        by_role[user.role].append(user.id)

    result: dict[int, list[str]] = {}

    student_ids = by_role.get(UserRole.STUDENT, [])
    if student_ids:
        rows = (
            db.query(ClassEnrollment.student_id, TeachingClass.name)
            .join(TeachingClass, TeachingClass.id == ClassEnrollment.class_id)
            .filter(
                ClassEnrollment.student_id.in_(student_ids),
                ClassEnrollment.deleted_at.is_(None),
                TeachingClass.deleted_at.is_(None),
            )
            .all()
        )
        buckets: dict[int, set[str]] = defaultdict(set)
        for sid, cname in rows:
            buckets[sid].add(cname)
        for sid in student_ids:
            result[sid] = sorted(buckets.get(sid, set()))

    teacher_ids = by_role.get(UserRole.TEACHER, [])
    if teacher_ids:
        rows = (
            db.query(TeachingClass.teacher_id, TeachingClass.name)
            .filter(
                TeachingClass.teacher_id.in_(teacher_ids),
                TeachingClass.deleted_at.is_(None),
            )
            .all()
        )
        buckets = defaultdict(set)
        for tid, cname in rows:
            buckets[tid].add(cname)
        for tid in teacher_ids:
            result[tid] = sorted(buckets.get(tid, set()))

    parent_ids = by_role.get(UserRole.PARENT, [])
    if parent_ids:
        bind_rows = (
            db.query(ParentStudentBinding.parent_id, ParentStudentBinding.student_id)
            .filter(ParentStudentBinding.parent_id.in_(parent_ids))
            .all()
        )
        parent_to_students: dict[int, list[int]] = defaultdict(list)
        all_student_ids: set[int] = set()
        for pid, sid in bind_rows:
            parent_to_students[pid].append(sid)
            all_student_ids.add(sid)
        student_classes: dict[int, set[str]] = defaultdict(set)
        if all_student_ids:
            en_rows = (
                db.query(ClassEnrollment.student_id, TeachingClass.name)
                .join(TeachingClass, TeachingClass.id == ClassEnrollment.class_id)
                .filter(
                    ClassEnrollment.student_id.in_(list(all_student_ids)),
                    ClassEnrollment.deleted_at.is_(None),
                    TeachingClass.deleted_at.is_(None),
                )
                .all()
            )
            for sid, cname in en_rows:
                student_classes[sid].add(cname)
        for pid in parent_ids:
            names: set[str] = set()
            for sid in parent_to_students.get(pid, []):
                names.update(student_classes.get(sid, set()))
            result[pid] = sorted(names)

    return result
