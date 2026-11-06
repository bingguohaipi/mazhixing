"""Sensitive field masking for API responses."""

import re

_PHONE_PATTERN = re.compile(r"^1[3-9]\d{9}$")


def mask_phone(value: str | None) -> str | None:
    if not value:
        return value
    text = value.strip()
    if _PHONE_PATTERN.match(text):
        return f"{text[:3]}****{text[-4:]}"
    if len(text) >= 7:
        return f"{text[:2]}***{text[-2:]}"
    return "***"


def mask_account(value: str | None) -> str | None:
    if not value:
        return value
    text = value.strip()
    if _PHONE_PATTERN.match(text):
        return mask_phone(text)
    if len(text) <= 4:
        return text
    return f"{text[:2]}***{text[-2:]}"
