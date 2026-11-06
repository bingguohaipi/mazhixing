#!/usr/bin/env python3
"""对比后端 FastAPI 路由与前端 src/api 中的路径引用（启发式，供人工复核）。"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_V1 = ROOT / "backend" / "app" / "api" / "v1"
FRONT_API = ROOT / "src" / "api"

ROUTE_DECO = re.compile(
    r'@router\.(get|post|put|patch|delete)\(\s*["\']([^"\']+)["\']',
    re.MULTILINE,
)
PREFIX = re.compile(r'router\s*=\s*APIRouter\(\s*prefix\s*=\s*["\']([^"\']+)["\']')
FRONT_PATH = re.compile(
    r"""['"`](/(?:admin|auth|classes|homework|practice|problems|parent|parents|teachers|teacher|students|suggestions|notices|analytics|events|user-notifications|submissions)[^'"`]*)['"`]"""
)


def collect_backend_routes() -> list[tuple[str, str, str]]:
    routes: list[tuple[str, str, str]] = []
    for path in sorted(API_V1.glob("*.py")):
        if path.name in {"router.py", "__init__.py"}:
            continue
        text = path.read_text(encoding="utf-8")
        prefix_m = PREFIX.search(text)
        prefix = prefix_m.group(1) if prefix_m else ""
        for method, sub in ROUTE_DECO.findall(text):
            full = (prefix + sub).replace("//", "/")
            routes.append((path.name, method.upper(), full))
    return routes


def collect_frontend_paths() -> set[str]:
    paths: set[str] = set()
    for path in FRONT_API.glob("*.ts"):
        text = path.read_text(encoding="utf-8")
        for m in FRONT_PATH.findall(text):
            # 去掉模板变量，保留静态前缀
            static = re.sub(r"\$\{[^}]+\}", "{id}", m)
            paths.add(static)
    return paths


def normalize_for_match(route: str) -> str:
    return re.sub(r"\{[^}]+\}", "{id}", route)


def main() -> None:
    backend = collect_backend_routes()
    front = collect_frontend_paths()

    print("=== 后端路由可能未被前端 src/api 直接引用（需复核：可能动态路径、E2E、管理端未封装）===\n")
    unmatched: list[tuple[str, str, str]] = []
    for file, method, route in backend:
        norm = normalize_for_match(route)
        hit = any(
            norm == fp
            or fp.startswith(norm.rstrip("/") + "/")
            or norm.startswith(fp.replace("{id}", "").rstrip("/"))
            for fp in front
        )
        # 简单包含匹配
        if not hit:
            for fp in front:
                if norm.split("/")[1:3] == fp.split("/")[1:3] and "{id}" in norm and "{id}" in fp:
                    hit = True
                    break
        if not hit:
            # 常见仍有效的路由
            if route in {"/events/track"} or "export" in route:
                hit = True
        if not hit:
            unmatched.append((file, method, route))

    for file, method, route in unmatched:
        print(f"  [{method:6}] {route:55}  ({file})")

    print(f"\n后端路由总数（约）: {len(backend)}")
    print(f"前端静态路径片段数: {len(front)}")
    print(f"上述未匹配（约）: {len(unmatched)}")


if __name__ == "__main__":
    main()
