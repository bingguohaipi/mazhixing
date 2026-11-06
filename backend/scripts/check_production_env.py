#!/usr/bin/env python3
"""Validate backend/.env for production readiness."""

from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = BACKEND_ROOT / ".env"

_INSECURE_SECRETS = {
    "dev-secret-key-change-in-production",
    "change-me-to-a-random-secret-key-in-production",
    "replace-with-a-long-random-secret",
}


def load_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def check(name: str, ok: bool, detail: str, errors: list[str], warnings: list[str]) -> None:
    if ok:
        print(f"  [OK]   {name}: {detail}")
    elif name.startswith("WARN"):
        warnings.append(f"{name}: {detail}")
        print(f"  [WARN] {name}: {detail}")
    else:
        errors.append(f"{name}: {detail}")
        print(f"  [FAIL] {name}: {detail}")


def main() -> int:
    print(f"Checking production env: {ENV_PATH}\n")
    env = load_env(ENV_PATH)
    if not env:
        print("  [FAIL] .env file not found or empty")
        return 1

    errors: list[str] = []
    warnings: list[str] = []

    debug = env.get("DEBUG", "true").lower() in {"1", "true", "yes"}
    check("DEBUG", not debug, "must be false", errors, warnings)

    secret = env.get("SECRET_KEY", "")
    check(
        "SECRET_KEY",
        secret not in _INSECURE_SECRETS and len(secret) >= 32,
        "random string, length >= 32",
        errors,
        warnings,
    )

    db_url = env.get("DATABASE_URL", "")
    check("DATABASE_URL", db_url.startswith("mysql"), "MySQL connection string", errors, warnings)

    cors = env.get("CORS_ORIGINS", "")
    check(
        "CORS_ORIGINS",
        cors.startswith("https://") and "localhost" not in cors,
        cors or "missing",
        errors,
        warnings,
    )

    check("JUDGE0_URL", bool(env.get("JUDGE0_URL")), env.get("JUDGE0_URL", "required"), errors, warnings)
    check(
        "JUDGE0_ALLOW_LOCAL_FALLBACK",
        env.get("JUDGE0_ALLOW_LOCAL_FALLBACK", "true").lower() == "false",
        "must be false",
        errors,
        warnings,
    )
    check(
        "CELERY_TASK_ALWAYS_EAGER",
        env.get("CELERY_TASK_ALWAYS_EAGER", "true").lower() == "false",
        "must be false",
        errors,
        warnings,
    )

    check("ENABLE_SEED", env.get("ENABLE_SEED", "false").lower() == "false", "must be false", errors, warnings)
    check(
        "ENABLE_OPENAPI",
        env.get("ENABLE_OPENAPI", "false").lower() == "false",
        "must be false",
        errors,
        warnings,
    )

    sms_provider = env.get("SMS_PROVIDER", "mock").lower()
    if env.get("SMS_ENABLED", "true").lower() != "false":
        if sms_provider == "aliyun":
            for key in (
                "ALIYUN_SMS_ACCESS_KEY_ID",
                "ALIYUN_SMS_ACCESS_KEY_SECRET",
                "ALIYUN_SMS_SIGN_NAME",
                "ALIYUN_SMS_TEMPLATE_CODE",
            ):
                check(key, bool(env.get(key)), env.get(key, "missing")[:20], errors, warnings)
        else:
            check("SMS_PROVIDER", False, f"production should use aliyun, got {sms_provider}", errors, warnings)

    ai_enabled = env.get("AI_ENABLED", "true").lower() != "false"
    if ai_enabled:
        check("OPENAI_API_KEY", bool(env.get("OPENAI_API_KEY")), "required when AI_ENABLED=true", errors, warnings)

    metrics_token = env.get("METRICS_TOKEN", "")
    if not metrics_token:
        warnings.append("METRICS_TOKEN: 建议设置随机 token 保护 /metrics 端点")
        print(f"  [WARN] METRICS_TOKEN: not set (recommended)")
    else:
        print(f"  [OK]   METRICS_TOKEN: configured")

    print()
    if warnings:
        print(f"Warnings ({len(warnings)}):")
        for item in warnings:
            print(f"  - {item}")
        print()

    if errors:
        print(f"Failed ({len(errors)}):")
        for item in errors:
            print(f"  - {item}")
        print("\nFix the items above before deploying to production.")
        return 1

    print("All required production checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
