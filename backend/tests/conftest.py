"""Pytest fixtures for API integration tests."""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Set test env before app imports
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_mazhixing.db")
os.environ.setdefault("ENABLE_SEED", "false")
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("SMS_ENABLED", "false")
os.environ.setdefault("METRICS_ENABLED", "false")

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine, get_db
from app.main import create_app
from app.models.class_model import ClassEnrollment, TeachingClass
from app.models.problem import (
    GespLevel,
    Problem,
    ProblemDifficulty,
    ProblemLanguage,
    ProblemScope,
    PublicPublishStatus,
    TestCase,
)
from app.models.user import User, UserRole
from app.models.knowledge_point import KnowledgePoint  # noqa: F401

get_settings.cache_clear()


@pytest.fixture(autouse=True)
def reset_db() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        from app.services.knowledge_point_service import KnowledgePointService

        KnowledgePointService(session).ensure_catalog()
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db
        finally:
            pass

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def teacher(db: Session) -> User:
    user = User(
        account="13800138000",
        phone="13800138000",
        password_hash=hash_password("Teacher123"),
        role=UserRole.TEACHER,
        display_name="测试教师",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def student(db: Session, teacher: User) -> User:
    user = User(
        account="stu001",
        password_hash=hash_password("123456"),
        role=UserRole.STUDENT,
        display_name="测试学生",
        student_no="001",
        created_by_teacher_id=teacher.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def teaching_class(db: Session, teacher: User, student: User) -> TeachingClass:
    cls = TeachingClass(
        teacher_id=teacher.id,
        name="测试班",
        course_type="C++",
        schedule="周六 14:00",
        created_by=teacher.id,
        updated_by=teacher.id,
    )
    db.add(cls)
    db.flush()
    db.add(ClassEnrollment(class_id=cls.id, student_id=student.id))
    db.commit()
    db.refresh(cls)
    return cls


@pytest.fixture
def problem(db: Session, teacher: User) -> Problem:
    item = Problem(
        teacher_id=teacher.id,
        scope=ProblemScope.PUBLIC,
        publish_status=PublicPublishStatus.PUBLISHED,
        version=1,
        title="A+B",
        description="读入两个整数，输出和",
        language=ProblemLanguage.CPP,
        difficulty=ProblemDifficulty.EASY,
        gesp_level=GespLevel.GESP1,
        knowledge_point="输入输出",
        time_limit_ms=1000,
        memory_limit_mb=256,
        created_by=teacher.id,
        updated_by=teacher.id,
    )
    db.add(item)
    db.flush()
    item.public_group_id = item.id
    db.add(
        TestCase(
            problem_id=item.id,
            input_data="1 2\n",
            expected_output="3\n",
            is_sample=True,
            sort_order=0,
        )
    )
    db.commit()
    db.refresh(item)
    return item


def auth_header(client: TestClient, account: str, password: str, role: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"account": account, "password": password, "role": role},
    )
    assert response.status_code == 200, response.text
    token = response.json()["data"]["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
