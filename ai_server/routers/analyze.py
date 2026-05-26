import asyncio

from fastapi import APIRouter

from config import get_settings
from models.schemas import AnalyzeRequest, AnalyzeResponse
from services.breed_classifier import classify_breed
from services.feature_augmentor import augment_features
from services.embedder import embed_text
from services.vector_search import search_similar_pets

router = APIRouter()


@router.post("/analyze")
async def analyze_tip(payload: AnalyzeRequest) -> AnalyzeResponse:
    settings = get_settings()
    cat_key = settings.cat_api_key or ""
    anthropic_key = settings.anthropic_api_key or ""
    cat_api_configured = bool(cat_key) and "..." not in cat_key and len(cat_key) > 12
    anthropic_configured = bool(anthropic_key) and "..." not in anthropic_key and len(anthropic_key) > 20
    diagnostics = {
        "catApiConfigured": cat_api_configured,
        "anthropicConfigured": anthropic_configured,
        "breedDetected": False,
        "usedBreedFilter": False,
        "fallbackFeatureLikely": not anthropic_configured,
        "errors": [],
    }
    breed = None
    confidence = 0.0
    feature_text = ""
    top_matches = []
    embedding = []

    # latency guardrails (seconds)
    classify_timeout = 10.0
    feature_timeout = 10.0
    search_timeout = 3.0

    classify_task = asyncio.create_task(classify_breed(payload.imageUrls))
    feature_task = asyncio.create_task(augment_features(payload.imageUrls, payload.breedHint))

    try:
        breed, confidence = await asyncio.wait_for(classify_task, timeout=classify_timeout)
    except asyncio.TimeoutError:
        diagnostics["errors"].append("classify_breed:timeout")
        classify_task.cancel()
    except Exception as exc:
        diagnostics["errors"].append(f"classify_breed:{exc}")

    try:
        feature_text = await asyncio.wait_for(feature_task, timeout=feature_timeout)
    except asyncio.TimeoutError:
        diagnostics["errors"].append("augment_features:timeout")
        feature_task.cancel()
        feature_text = "사진에서 반려동물의 특징을 추출하지 못했습니다."
    except Exception as exc:
        diagnostics["errors"].append(f"augment_features:{exc}")
        feature_text = "사진에서 반려동물의 특징을 추출하지 못했습니다."

    try:
        embedding = embed_text(feature_text)
    except Exception as exc:
        diagnostics["errors"].append(f"embed_text:{exc}")
        embedding = []

    apply_breed_filter = (payload.breedHint or breed) if confidence >= 0.7 else None
    if embedding:
        try:
            top_matches = await asyncio.wait_for(
                asyncio.to_thread(
                    search_similar_pets,
                    query_vector=embedding,
                    breed_filter=apply_breed_filter,
                    lat=payload.latitude,
                    lng=payload.longitude,
                    radius_m=payload.radiusM or 2000,
                    match_count=payload.matchCount or 3,
                ),
                timeout=search_timeout,
            )
        except asyncio.TimeoutError:
            diagnostics["errors"].append("search_similar_pets:timeout")
            top_matches = []
        except Exception as exc:
            diagnostics["errors"].append(f"search_similar_pets:{exc}")
            top_matches = []

    diagnostics["breedDetected"] = bool(breed)
    diagnostics["usedBreedFilter"] = bool(apply_breed_filter)
    diagnostics["fallbackFeatureLikely"] = not anthropic_configured or not feature_text

    return AnalyzeResponse(
        breed=payload.breedHint or breed,
        confidence=confidence,
        featureText=feature_text,
        topMatches=top_matches,
        diagnostics=diagnostics,
    )
