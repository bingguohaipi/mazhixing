"""Normalize problem sample / test-case I/O text from admin forms."""


def normalize_io_text(value: str | None) -> str | None:
    """Turn literal ``\\n`` in stored text into real newlines (common admin typo)."""
    if value is None:
        return None
    text = value.strip("\r\n")
    if "\\n" in text:
        text = text.replace("\\n", "\n")
    return text
