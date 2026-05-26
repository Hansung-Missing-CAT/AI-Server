from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import get_redis, get_supabase
from services.breed_classifier import classify_breed
from services.embedder import embed_text
from services.feature_augmentor import augment_features
from services.vector_search import search_similar_pets


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def publish_progress(user_id: str, tip_id: str, progress: int, message: str) -> None:
    redis = get_redis()
    payload = {
        "userId": user_id,
        "tipId": tip_id,
        "progress": progress,
        "message": message,
        "timestamp": _now_iso(),
    }
    redis.publish("tip:progress", json.dumps(payload, ensure_ascii=False))


def publish_done(user_id: str, tip_id: str, status: str) -> None:
    redis = get_redis()
    payload = {
        "userId": user_id,
        "tipId": tip_id,
        "status": status,
        "timestamp": _now_iso(),
    }
    redis.publish("tip:done", json.dumps(payload, ensure_ascii=False))


async def process_tip_row(row: dict) -> None:
    supabase = get_supabase()
    tip_id = row["id"]
    user_id = row["user_id"]
    image_urls = row.get("image_urls") or []

    try:
        publish_progress(user_id, tip_id, 10, "데이터베이스 조회 중")
        supabase.table("tips").update({"progress": 10}).eq("id", tip_id).execute()

        publish_progress(user_id, tip_id, 35, "특징점 추출 중")
        breed, confidence = await classify_breed(image_urls)
        feature_text = await augment_features(image_urls, breed)
        supabase.table("tips").update({"progress": 35}).eq("id", tip_id).execute()

        publish_progress(user_id, tip_id, 65, "유사도 매칭 중")
        vector = embed_text(feature_text)
        matches = search_similar_pets(
            query_vector=vector,
            breed_filter=breed if confidence >= 0.7 else None,
            lat=None,
            lng=None,
            radius_m=2000,
            match_count=3,
        )

        result_payload = {
            "breed": breed,
            "confidence": confidence,
            "featureText": feature_text,
            "topMatches": matches,
        }

        supabase.table("tips").update(
            {"status": "done", "progress": 100, "results": result_payload, "updated_at": _now_iso()}
        ).eq("id", tip_id).execute()
        publish_progress(user_id, tip_id, 100, "완료")
        publish_done(user_id, tip_id, "done")
    except Exception as exc:
        supabase.table("tips").update(
            {"status": "failed", "error_msg": str(exc), "updated_at": _now_iso()}
        ).eq("id", tip_id).execute()
        publish_done(user_id, tip_id, "failed")


async def poll_and_process(interval_seconds: int = 3) -> None:
    supabase = get_supabase()
    while True:
        try:
            resp = (
                supabase.table("tips")
                .select("id,user_id,image_urls,status")
                .eq("status", "processing")
                .order("created_at")
                .limit(5)
                .execute()
            )
            rows = resp.data or []
            for row in rows:
                await process_tip_row(row)
        except Exception:
            pass
        await asyncio.sleep(interval_seconds)


if __name__ == "__main__":
    poll_interval = int(os.getenv("AI_WORKER_POLL_SECONDS", "3"))
    asyncio.run(poll_and_process(poll_interval))
