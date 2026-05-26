from fastapi.testclient import TestClient

from main import app


def test_analyze_invalid_body_returns_422():
    client = TestClient(app)
    res = client.post("/ai/analyze", json={"imageUrls": "not-array"})
    assert res.status_code == 422
