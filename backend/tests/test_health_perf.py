import time

from fastapi.testclient import TestClient


def test_health_responds_within_300ms(client: TestClient) -> None:
    start = time.perf_counter()
    response = client.get("/health")
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert response.status_code in (200, 503)
    body = response.json()
    assert "data" in body
    assert "dependencies" in body["data"]
    assert elapsed_ms < 3000, f"health too slow: {elapsed_ms:.0f}ms"
