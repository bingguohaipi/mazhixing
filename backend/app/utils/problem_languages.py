"""Supported programming languages on a problem (Python / C++)."""

from __future__ import annotations

from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Query

from app.models.problem import Problem, ProblemLanguage

ALLOWED = frozenset({"Python", "C++"})


def normalize_languages(raw: list[str] | None) -> list[str]:
    if not raw:
        raise ValueError("请至少选择一种语言（Python 或 C++）")
    seen: set[str] = set()
    out: list[str] = []
    for item in raw:
        key = (item or "").strip()
        if key not in ALLOWED:
            raise ValueError(f"不支持的语言「{key}」，仅可选 Python 或 C++")
        if key not in seen:
            seen.add(key)
            out.append(key)
    order = {"Python": 0, "C++": 1}
    out.sort(key=lambda x: order[x])
    return out


def get_problem_languages(problem: Problem) -> list[str]:
    stored = problem.languages
    if isinstance(stored, list) and stored:
        cleaned = [str(x).strip() for x in stored if str(x).strip() in ALLOWED]
        if cleaned:
            return normalize_languages(cleaned)
    return [problem.language.value]


def apply_languages_to_problem(problem: Problem, names: list[str]) -> None:
    normalized = normalize_languages(names)
    problem.languages = normalized
    problem.language = ProblemLanguage.PYTHON if normalized[0] == "Python" else ProblemLanguage.CPP


def problem_supports_language(problem: Problem, language: str) -> bool:
    return (language or "").strip() in get_problem_languages(problem)


def apply_language_filter(query: Query, language: str) -> Query:
    lang = (language or "").strip()
    if lang not in ALLOWED:
        return query
    lang_enum = ProblemLanguage.PYTHON if lang == "Python" else ProblemLanguage.CPP
    needle = f'"{lang}"'
    return query.filter(
        or_(
            Problem.language == lang_enum,
            cast(Problem.languages, String).like(f"%{needle}%"),
        )
    )
