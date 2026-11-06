"""Lightweight nickname profanity filter for student-facing display names."""

from __future__ import annotations

import re

# 常见不文明用语片段（小写/原样匹配），可按运营需要扩展
_BLOCKED_FRAGMENTS: tuple[str, ...] = (
    "傻逼",
    "傻b",
    "sb",
    "nmsl",
    "你妈",
    "他妈",
    "去死",
    "废物",
    "贱",
    "操你",
    "草你",
    "fuck",
    "shit",
    "bitch",
    "asshole",
)

_NICKNAME_PATTERN = re.compile(r"^[\u4e00-\u9fffA-Za-z0-9_\·\-\s]{2,16}$")


def validate_student_nickname(raw: str) -> str:
    value = raw.strip()
    if not value:
        raise ValueError("昵称不能为空")
    if len(value) < 2 or len(value) > 16:
        raise ValueError("昵称长度为 2–16 个字符")
    if not _NICKNAME_PATTERN.match(value):
        raise ValueError("昵称仅支持中文、字母、数字及 ·_-")
    lowered = value.lower()
    for fragment in _BLOCKED_FRAGMENTS:
        if fragment in lowered or fragment in value:
            raise ValueError("昵称含有不当用语，请修改")
    return value
