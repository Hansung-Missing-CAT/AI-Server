from fastapi import APIRouter, HTTPException

from models.schemas import EmbedRequest
from services.breed_classifier import classify_breed
from services.feature_augmentor import augment_features
from services.embedder import embed_text
from services.vector_search import upsert_embedding

router = APIRouter()


@router.post("/embed")
async def embed_pet(payload: EmbedRequest):
    try:
        breed, _ = await classify_breed(payload.imageUrls)
        feature_text = payload.featureText or await augment_features(payload.imageUrls, payload.breedHint or breed)
        embedding = embed_text(feature_text)
        upsert_embedding(payload.petId, feature_text, embedding)
        return {"petId": payload.petId, "status": "done", "embeddingDim": len(embedding)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"embed_failed: {exc}") from exc
