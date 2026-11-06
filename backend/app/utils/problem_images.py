"""Problem illustration URLs stored as JSON list."""


def normalize_problem_image_urls(urls: list[str] | None) -> list[str]:
    if not urls:
        return []
    cleaned = [item.strip() for item in urls if item and item.strip()]
    return cleaned[:5]


def get_problem_image_urls(problem) -> list[str]:
    raw = getattr(problem, "image_urls", None)
    if raw is None:
        return []
    if isinstance(raw, list):
        return normalize_problem_image_urls(raw)
    return []
