#!/usr/bin/env python3
"""Smoke check for /health latency (PRD: regular APIs <= 300ms target)."""

from __future__ import annotations

import sys
import time
import urllib.error
import urllib.request

DEFAULT_URL = "http://localhost:8000/health"
THRESHOLD_MS = 3000


def main() -> int:
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            body = resp.read(200)
    except urllib.error.URLError as exc:
        print(f"FAIL: cannot reach {url}: {exc}")
        return 1
    elapsed_ms = (time.perf_counter() - start) * 1000
    ok = elapsed_ms <= THRESHOLD_MS
    print(f"{'OK' if ok else 'WARN'}: {url} {elapsed_ms:.0f}ms (threshold {THRESHOLD_MS}ms)")
    print(body.decode('utf-8', errors='replace')[:120])
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
