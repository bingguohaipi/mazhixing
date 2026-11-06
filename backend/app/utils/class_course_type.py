"""班级课程类型（编程语言赛道）校验与解析。"""

from __future__ import annotations

CLASS_COURSE_TYPES = frozenset({"Python", "C++"})


def validate_class_course_type(value: str) -> str:
    key = (value or "").strip()
    if key not in CLASS_COURSE_TYPES:
        raise ValueError("课程类型仅可选 Python 或 C++")
    return key


def course_type_to_coding_language(course_type: str | None) -> str | None:
    """将班级 course_type 解析为默认编程语言；兼容历史自由文本。"""
    raw = (course_type or "").strip()
    if not raw:
        return None
    if raw in CLASS_COURSE_TYPES:
        return raw
    lower = raw.lower()
    if "c++" in lower or "cpp" in lower:
        return "C++"
    if "python" in lower:
        return "Python"
    return None
