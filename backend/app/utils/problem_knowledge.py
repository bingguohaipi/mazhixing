"""Knowledge-point tags stored on problems (multi-tag)."""

from __future__ import annotations

import json

from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Query

from app.knowledge.catalog import validate_knowledge_point_name
from app.models.problem import Problem

# Deprecated catalog names merged into a canonical topic for listing & filtering.
KNOWLEDGE_TOPIC_ALIASES: dict[str, str] = {
    "输出": "输入输出",
}


def resolve_knowledge_topic_name(name: str) -> str:
    key = (name or "").strip()
    return KNOWLEDGE_TOPIC_ALIASES.get(key, key)


def knowledge_topic_filter_names(name: str) -> list[str]:
    """Topic keys that should match when browsing a canonical knowledge topic."""
    canonical = resolve_knowledge_topic_name(name)
    names = {canonical}
    for alias, target in KNOWLEDGE_TOPIC_ALIASES.items():
        if target == canonical:
            names.add(alias)
    return sorted(names)


def canonicalize_knowledge_point_name(name: str) -> str:
    resolved = resolve_knowledge_topic_name(name)
    return validate_knowledge_point_name(resolved)


def normalize_knowledge_point_names(raw: list[str] | None) -> list[str]:
    if not raw:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for item in raw:
        resolved = resolve_knowledge_topic_name((item or "").strip())
        if not resolved:
            continue
        name = validate_knowledge_point_name(resolved)
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out


def problem_has_knowledge_topic(problem: Problem, knowledge_point: str) -> bool:
    """Whether a problem is tagged with the topic (canonical + legacy aliases)."""
    wanted = set(knowledge_topic_filter_names(knowledge_point))
    tags = set(get_problem_knowledge_points(problem))
    return bool(wanted & tags)


def _json_array_topic_like_patterns(topic: str) -> list[str]:
    """Match topic inside JSON array text (UTF-8 or \\u-escaped, as in SQLite JSON)."""
    patterns: set[str] = set()
    patterns.add(f'"{topic}"')
    patterns.add(json.dumps(topic, ensure_ascii=False))
    patterns.add(json.dumps(topic, ensure_ascii=True))
    inner_esc = json.dumps(topic, ensure_ascii=True)[1:-1]
    if inner_esc != topic:
        patterns.add(f'"{inner_esc}"')
    return list(patterns)


def get_problem_knowledge_points(problem: Problem) -> list[str]:
    stored = problem.knowledge_points
    if isinstance(stored, list) and stored:
        cleaned: list[str] = []
        seen: set[str] = set()
        for x in stored:
            raw = str(x).strip()
            if not raw:
                continue
            canonical = resolve_knowledge_topic_name(raw)
            if canonical in seen:
                continue
            seen.add(canonical)
            cleaned.append(canonical)
        if cleaned:
            return cleaned
    legacy = (problem.knowledge_point or "").strip()
    if legacy:
        return [resolve_knowledge_topic_name(legacy)]
    return []


def apply_knowledge_points_to_problem(problem: Problem, names: list[str]) -> None:
    normalized = normalize_knowledge_point_names(names)
    problem.knowledge_points = normalized or None
    problem.knowledge_point = normalized[0] if normalized else None


def apply_knowledge_point_filter(query: Query, knowledge_point: str) -> Query:
    name = resolve_knowledge_topic_name((knowledge_point or "").strip())
    if not name:
        return query
    if name == "未分类":
        return query.filter(
            or_(
                Problem.knowledge_point.is_(None),
                Problem.knowledge_point == "",
                Problem.knowledge_points.is_(None),
            )
        )
    topic_names = knowledge_topic_filter_names(name)
    clauses = []
    for topic in topic_names:
        clauses.append(Problem.knowledge_point == topic)
        for pattern in _json_array_topic_like_patterns(topic):
            clauses.append(cast(Problem.knowledge_points, String).like(f"%{pattern}%"))
    return query.filter(or_(*clauses))
