"""Pre-submit code validation (PRD: block empty / invalid submissions)."""

from __future__ import annotations

import re

from app.core.exceptions import AppException

MAX_CODE_LENGTH = 64_000
MIN_MEANINGFUL_LENGTH = 8

_PYTHON_FORBIDDEN = (
    re.compile(r"\bos\s*\.\s*system\s*\(", re.I),
    re.compile(r"\bsubprocess\b", re.I),
    re.compile(r"\beval\s*\(", re.I),
    re.compile(r"\bexec\s*\(", re.I),
    re.compile(r"\b__import__\s*\(", re.I),
    re.compile(r"\bopen\s*\(\s*['\"]/?etc", re.I),
)

_CPP_FORBIDDEN = (
    re.compile(r"\bsystem\s*\(", re.I),
    re.compile(r"\bfork\s*\(", re.I),
    re.compile(r"\bpopen\s*\(", re.I),
)


def _strip_comments_and_strings(code: str, language: str) -> str:
    if language == "Python":
        without_triple = re.sub(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', " ", code)
        without_line = re.sub(r"#.*", " ", without_triple)
        return re.sub(r"\s+", "", without_line)
    without_block = re.sub(r"/\*[\s\S]*?\*/", " ", code)
    without_line = re.sub(r"//.*", " ", without_block)
    return re.sub(r"\s+", "", without_line)


def validate_submission_code(code: str, language: str) -> None:
    """提交前校验：非空、长度、危险系统调用关键字（不替代 Judge0 沙箱）。"""
    stripped = code.strip()
    if not stripped:
        raise AppException(400, "请勿提交空代码")

    if len(code) > MAX_CODE_LENGTH:
        raise AppException(400, "代码过长，请精简后重新提交")

    meaningful = _strip_comments_and_strings(stripped, language)
    if len(meaningful) < MIN_MEANINGFUL_LENGTH:
        raise AppException(400, "代码内容过少，请编写完整解题逻辑后再提交")

    patterns = _PYTHON_FORBIDDEN if language == "Python" else _CPP_FORBIDDEN
    for pattern in patterns:
        if pattern.search(stripped):
            raise AppException(400, "代码包含不允许的系统调用，请修改后重试")
