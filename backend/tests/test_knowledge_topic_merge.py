from app.utils.problem_knowledge import (
    KNOWLEDGE_TOPIC_ALIASES,
    knowledge_topic_filter_names,
    normalize_knowledge_point_names,
    resolve_knowledge_topic_name,
)


def test_output_topic_merged_into_io() -> None:
    assert "输出" in KNOWLEDGE_TOPIC_ALIASES
    assert resolve_knowledge_topic_name("输出") == "输入输出"
    assert set(knowledge_topic_filter_names("输入输出")) == {"输入输出", "输出"}


def test_normalize_replaces_deprecated_tag() -> None:
    names = normalize_knowledge_point_names(["输出", "输入输出"])
    assert names == ["输入输出"]


def test_knowledge_filter_matches_unicode_json_tags(db, problem) -> None:
    """SQLite JSON may store Chinese tags as \\u escapes; filter must still match."""
    from app.models.problem import Problem, ProblemScope, PublicPublishStatus
    from app.services.practice_service import PracticeService
    from app.utils.problem_knowledge import apply_knowledge_points_to_problem

    problem.scope = ProblemScope.PUBLIC
    problem.publish_status = PublicPublishStatus.PUBLISHED
    problem.public_group_id = problem.id
    problem.version = 1
    apply_knowledge_points_to_problem(problem, ["输入输出", "条件语句"])
    db.commit()

    svc = PracticeService(db)
    base = svc._public_catalog_query()
    assert svc._apply_knowledge_point_filter(base, "条件语句").filter(Problem.id == problem.id).count() == 1
    assert svc._apply_knowledge_point_filter(base, "输入输出").filter(Problem.id == problem.id).count() == 1
