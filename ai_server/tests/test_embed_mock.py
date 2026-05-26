from fastapi.testclient import TestClient

from main import app
from routers import embed as embed_router


def test_embed_with_mocked_storage(monkeypatch):
    async def _mock_classify(_image_urls):
        return "코리안숏헤어", 0.8

    async def _mock_augment(_image_urls, breed_hint=None):
        return "테스트 특징"

    monkeypatch.setattr(embed_router, "upsert_embedding", lambda pet_id, feature_text, embedding: None)
    monkeypatch.setattr(embed_router, "classify_breed", _mock_classify)
    monkeypatch.setattr(embed_router, "augment_features", _mock_augment)
    monkeypatch.setattr(embed_router, "embed_text", lambda text: [0.1] * 768)

    client = TestClient(app)
    res = client.post(
        "/ai/embed",
        json={"petId": "00000000-0000-0000-0000-000000000001", "imageUrls": [], "featureText": "테스트 특징"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "done"
    assert res.json()["embeddingDim"] == 768
