"""Seed demo users and classes for local development."""

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.audit import ParentStudentBinding
from app.models.class_model import ClassEnrollment, TeachingClass
from app.models.user import User, UserRole
def seed_demo_data() -> None:
    db: Session = SessionLocal()
    try:
        if db.query(User).count() > 0:
            _ensure_admin_user(db)
            _ensure_demo_parent_binding(db)
            _seed_classes_if_empty(db)
            _seed_problems_if_empty(db)
            _seed_public_problems_if_empty(db)
            _seed_homework_if_empty(db)
            _seed_public_gesp_batch()
            return

        teacher = User(
            account="13800138000",
            phone="13800138000",
            password_hash=hash_password("Teacher123"),
            role=UserRole.TEACHER,
            display_name="演示教师",
        )
        student = User(
            account="stu2024001",
            phone=None,
            password_hash=hash_password("123456"),
            role=UserRole.STUDENT,
            display_name="张小明",
            student_no="2024001",
            created_by_teacher_id=None,
        )
        parent = User(
            account="13900139000",
            phone="13900139000",
            password_hash=hash_password("Parent123"),
            role=UserRole.PARENT,
            display_name="张家长",
        )
        db.add_all([teacher, student, parent])
        db.flush()

        admin = User(
            account="admin",
            phone=None,
            password_hash=hash_password("Admin123"),
            role=UserRole.ADMIN,
            display_name="平台管理员",
            created_by=None,
            updated_by=None,
        )
        db.add(admin)

        student.created_by_teacher_id = teacher.id

        db.add(ParentStudentBinding(parent_id=parent.id, student_id=student.id))
        db.commit()

        _seed_classes_if_empty(db)
        _seed_problems_if_empty(db)
        _seed_public_problems_if_empty(db)
        _seed_homework_if_empty(db)
        _seed_public_gesp_batch()
    finally:
        db.close()


def _seed_public_gesp_batch() -> None:
    from app.scripts.seed_public_gesp_batch import seed_public_gesp_batch

    seed_public_gesp_batch()


def _ensure_demo_parent_binding(db: Session) -> None:
    parent = (
        db.query(User)
        .filter(User.account == "13900139000", User.role == UserRole.PARENT, User.deleted_at.is_(None))
        .first()
    )
    student = (
        db.query(User)
        .filter(User.account == "stu2024001", User.role == UserRole.STUDENT, User.deleted_at.is_(None))
        .first()
    )
    if parent is None or student is None:
        return
    exists = (
        db.query(ParentStudentBinding)
        .filter(
            ParentStudentBinding.parent_id == parent.id,
            ParentStudentBinding.student_id == student.id,
        )
        .first()
    )
    if exists:
        return
    db.add(ParentStudentBinding(parent_id=parent.id, student_id=student.id))
    try:
        db.commit()
    except Exception:
        db.rollback()


def _ensure_admin_user(db: Session) -> None:
    exists = (
        db.query(User)
        .filter(User.role == UserRole.ADMIN, User.deleted_at.is_(None))
        .first()
    )
    if exists:
        return
    admin = User(
        account="admin",
        password_hash=hash_password("Admin123"),
        role=UserRole.ADMIN,
        display_name="平台管理员",
    )
    db.add(admin)
    try:
        db.commit()
    except Exception:
        db.rollback()


def _seed_classes_if_empty(db: Session) -> None:
    if db.query(TeachingClass).count() > 0:
        return

    teacher = db.query(User).filter(User.role == UserRole.TEACHER).first()
    if teacher is None:
        return

    demo_class = TeachingClass(
        teacher_id=teacher.id,
        name="C++信奥A班",
        course_type="C++信奥基础",
        schedule="周六 14:00-16:00",
        expected_student_count=32,
        lesson_count=12,
        description="GESP 1-2 级信奥入门班级",
        created_by=teacher.id,
        updated_by=teacher.id,
    )
    db.add(demo_class)
    db.flush()

    student = db.query(User).filter(User.account == "stu2024001").first()
    if student:
        if not student.student_no:
            student.student_no = "2024001"
        student.created_by_teacher_id = teacher.id
        db.add(ClassEnrollment(class_id=demo_class.id, student_id=student.id))

    db.commit()


def _seed_problems_if_empty(db: Session) -> None:
    from app.models.problem import (
        GespLevel,
        Problem,
        ProblemDifficulty,
        ProblemLanguage,
        ProblemScope,
        PublicPublishStatus,
        TestCase,
    )

    if db.query(Problem).count() > 0:
        return

    teacher = db.query(User).filter(User.role == UserRole.TEACHER).first()
    if teacher is None:
        return

    demos = [
        {
            "title": "A+B Problem",
            "description": "输入两个整数 A 和 B，输出它们的和。",
            "language": ProblemLanguage.CPP,
            "difficulty": ProblemDifficulty.BEGINNER,
            "gesp_level": GespLevel.GESP1,
            "knowledge_point": "输入输出",
            "sample_input": "1 2",
            "sample_output": "3",
            "time_limit_ms": 1000,
            "memory_limit_mb": 256,
            "cases": [("1 2", "3"), ("100 200", "300")],
        },
        {
            "title": "判断闰年",
            "description": "输入年份，判断是否为闰年，是输出 YES，否则输出 NO。",
            "language": ProblemLanguage.CPP,
            "difficulty": ProblemDifficulty.EASY,
            "gesp_level": GespLevel.GESP2,
            "knowledge_point": "条件语句",
            "sample_input": "2024",
            "sample_output": "YES",
            "time_limit_ms": 1000,
            "memory_limit_mb": 256,
            "cases": [("2024", "YES"), ("1900", "NO"), ("2000", "YES")],
        },
        {
            "title": "计算圆的面积",
            "description": "输入半径 r，输出圆的面积，保留两位小数。",
            "language": ProblemLanguage.PYTHON,
            "difficulty": ProblemDifficulty.BEGINNER,
            "gesp_level": GespLevel.GESP1,
            "knowledge_point": "变量与运算",
            "sample_input": "2",
            "sample_output": "12.56",
            "time_limit_ms": 1000,
            "memory_limit_mb": 256,
            "cases": [("2", "12.56"), ("1", "3.14")],
        },
    ]

    from app.utils.problem_languages import apply_languages_to_problem

    for demo in demos:
        cases = demo.pop("cases")
        problem = Problem(
            teacher_id=teacher.id,
            scope=ProblemScope.PUBLIC,
            publish_status=PublicPublishStatus.PUBLISHED,
            version=1,
            created_by=teacher.id,
            updated_by=teacher.id,
            **demo,
        )
        db.add(problem)
        db.flush()
        apply_languages_to_problem(problem, ["Python", "C++"])
        problem.public_group_id = problem.id
        for index, (input_data, expected_output) in enumerate(cases):
            db.add(
                TestCase(
                    problem_id=problem.id,
                    input_data=input_data,
                    expected_output=expected_output,
                    is_sample=index == 0,
                    sort_order=index,
                )
            )

    db.commit()


def _seed_public_problems_if_empty(db: Session) -> None:
    from app.models.problem import (
        GespLevel,
        Problem,
        ProblemDifficulty,
        ProblemLanguage,
        ProblemScope,
        PublicPublishStatus,
        TestCase,
    )

    exists = (
        db.query(Problem)
        .filter(Problem.scope == ProblemScope.PUBLIC, Problem.deleted_at.is_(None))
        .first()
    )
    if exists:
        return

    admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
    if admin is None:
        return

    problem = Problem(
        teacher_id=admin.id,
        scope=ProblemScope.PUBLIC,
        publish_status=PublicPublishStatus.PUBLISHED,
        version=1,
        title="公共题库：Hello World",
        description="输出一行 Hello World。",
        language=ProblemLanguage.CPP,
        difficulty=ProblemDifficulty.BEGINNER,
        gesp_level=GespLevel.GESP1,
        knowledge_point="输入输出",
        sample_input="",
        sample_output="Hello World",
        time_limit_ms=1000,
        memory_limit_mb=256,
        created_by=admin.id,
        updated_by=admin.id,
    )
    db.add(problem)
    db.flush()
    from app.utils.problem_languages import apply_languages_to_problem

    apply_languages_to_problem(problem, ["Python", "C++"])
    problem.public_group_id = problem.id
    db.add(
        TestCase(
            problem_id=problem.id,
            input_data="",
            expected_output="Hello World",
            is_sample=True,
            sort_order=0,
        )
    )
    db.commit()


def _seed_homework_if_empty(db: Session) -> None:
    from datetime import datetime, timedelta, timezone

    from app.models.homework import Homework, HomeworkClass, HomeworkProblem
    from app.models.problem import Problem

    if db.query(Homework).count() > 0:
        return

    teacher = db.query(User).filter(User.role == UserRole.TEACHER).first()
    demo_class = db.query(TeachingClass).first()
    problems = db.query(Problem).filter(Problem.teacher_id == teacher.id).limit(2).all() if teacher else []
    if not teacher or not demo_class or len(problems) < 1:
        return

    now = datetime.now(timezone.utc)
    homework = Homework(
        teacher_id=teacher.id,
        title="循环结构练习",
        description="请按时完成以下编程练习",
        start_time=now - timedelta(days=1),
        end_time=now + timedelta(days=2),
        allow_late_submission=True,
        created_by=teacher.id,
        updated_by=teacher.id,
    )
    db.add(homework)
    db.flush()
    db.add(HomeworkClass(homework_id=homework.id, class_id=demo_class.id))
    for index, problem in enumerate(problems):
        db.add(HomeworkProblem(homework_id=homework.id, problem_id=problem.id, sort_order=index))
    db.commit()
