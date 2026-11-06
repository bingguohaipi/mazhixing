"""Problem multi-language support."""

from app.models.problem import Problem, ProblemDifficulty, ProblemLanguage
from app.utils.problem_languages import (
    apply_languages_to_problem,
    get_problem_languages,
    normalize_languages,
    problem_supports_language,
)


def test_normalize_languages_deduplicate_and_order() -> None:
    assert normalize_languages(["C++", "Python", "Python"]) == ["Python", "C++"]


def test_get_and_support() -> None:
    p = Problem(
        teacher_id=1,
        title="t",
        description="d",
        language=ProblemLanguage.PYTHON,
        difficulty=ProblemDifficulty.EASY,
    )
    apply_languages_to_problem(p, ["Python", "C++"])
    assert get_problem_languages(p) == ["Python", "C++"]
    assert problem_supports_language(p, "Python")
    assert problem_supports_language(p, "C++")
    assert not problem_supports_language(p, "Java")
