"""Judge0 connectivity helpers."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings


@dataclass
class Judge0Health:
    enabled: bool
    url: str | None
    reachable: bool
    mode: str
    message: str


def check_judge0_health() -> Judge0Health:
    settings = get_settings()
    if not settings.judge0_url:
        if settings.judge0_required:
            return Judge0Health(
                enabled=False,
                url=None,
                reachable=False,
                mode="missing",
                message="生产环境必须配置 JUDGE0_URL",
            )
        return Judge0Health(
            enabled=False,
            url=None,
            reachable=False,
            mode="local_subprocess",
            message="未配置 Judge0，使用本地 subprocess 判题（仅开发环境）",
        )

    try:
        import httpx

        headers: dict[str, str] = {}
        if settings.judge0_auth_token:
            headers["X-Auth-Token"] = settings.judge0_auth_token

        with httpx.Client(
            base_url=settings.judge0_url.rstrip("/"),
            timeout=settings.judge0_health_timeout_seconds,
            headers=headers,
        ) as client:
            response = client.get("/system_info")
            if response.status_code >= 400:
                return Judge0Health(
                    enabled=True,
                    url=settings.judge0_url,
                    reachable=False,
                    mode="judge0",
                    message=f"Judge0 响应异常: HTTP {response.status_code}",
                )
            return Judge0Health(
                enabled=True,
                url=settings.judge0_url,
                reachable=True,
                mode="judge0",
                message="Judge0 沙箱可用",
            )
    except Exception as exc:  # noqa: BLE001
        return Judge0Health(
            enabled=True,
            url=settings.judge0_url,
            reachable=False,
            mode="judge0",
            message=f"Judge0 不可达: {exc}",
        )
