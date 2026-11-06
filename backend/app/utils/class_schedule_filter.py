"""班级上课时间筛选辅助。"""

from __future__ import annotations

CLASS_WEEKDAYS = frozenset({"周一", "周二", "周三", "周四", "周五", "周六", "周日"})


def normalize_weekday_filter(value: str | None) -> str | None:
    if value is None:
        return None
    key = value.strip()
    if not key:
        return None
    if key not in CLASS_WEEKDAYS:
        raise ValueError("周几仅可选周一至周日")
    return key
