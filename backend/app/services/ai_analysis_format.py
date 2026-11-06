"""Structured AI analysis storage (markdown + highlight line numbers)."""

from __future__ import annotations

import json
import re
from typing import Any

AI_STORAGE_VERSION = 1


def pack_ai_analysis(markdown: str, highlight_lines: list[int]) -> str:
    unique_lines = sorted({line for line in highlight_lines if line >= 1})
    payload = {"v": AI_STORAGE_VERSION, "text": markdown.strip(), "lines": unique_lines}
    return json.dumps(payload, ensure_ascii=False)


def unpack_ai_analysis(raw: str | None) -> tuple[str, list[int]]:
    if not raw:
        return "", []
    text = raw.strip()
    if not text.startswith("{"):
        lines = _extract_lines_from_markdown(text)
        return text, lines
    try:
        data: dict[str, Any] = json.loads(text)
    except json.JSONDecodeError:
        return text, []
    markdown = str(data.get("text") or "")
    lines_raw = data.get("lines") or []
    lines: list[int] = []
    if isinstance(lines_raw, list):
        for item in lines_raw:
            if isinstance(item, int) and item >= 1:
                lines.append(item)
    return markdown, sorted(set(lines))


def parse_model_json(raw: str) -> tuple[str, list[int]]:
    """Parse OpenAI JSON payload; fallback to plain text."""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return text, _extract_lines_from_markdown(text)
    markdown = str(data.get("analysis") or data.get("text") or text)
    lines_raw = data.get("highlight_lines") or data.get("lines") or []
    lines: list[int] = []
    if isinstance(lines_raw, list):
        for item in lines_raw:
            if isinstance(item, int) and item >= 1:
                lines.append(item)
    if not lines:
        lines = _extract_lines_from_markdown(markdown)
    return markdown.strip(), sorted(set(lines))


def _extract_lines_from_markdown(markdown: str) -> list[int]:
    found: set[int] = set()
    for match in re.finditer(r"(?:第?\s*)?(\d+)\s*行", markdown):
        found.add(int(match.group(1)))
    for match in re.finditer(r"line\s*[:：]?\s*(\d+)", markdown, re.I):
        found.add(int(match.group(1)))
    return sorted(found)
