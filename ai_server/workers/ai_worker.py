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
from services.vector_search import search_similar_pets, upsert_embedding


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def publish_progress(user_id: str, tip_id: str, progress: int, message: str) -> None:
    print(f"[PROGRESS] tip={tip_id} progress={progress} msg={message}")
    try:
        redis = get_redis()
        redis.publish("tip:progress", json.dumps({
            "userId": user_id,
            "tipId": tip_id,
            "progress": progress,
            "message": message,
        }))
    except Exception as e:
        print(f"[WARN] Redis publish 실패 (tip:progress): {e}")


def publish_done(user_id: str, tip_id: str, status: str) -> None:
    print(f"[DONE] tip={tip_id} status={status}")
    try:
        redis = get_redis()
        redis.publish("tip:done", json.dumps({
            "userId": user_id,
            "tipId": tip_id,
            "status": status,
        }))
    except Exception as e:
        print(f"[WARN] Redis publish 실패 (tip:done): {e}")

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
        print(f"[DEBUG] embed_text 시작...")
        vector = embed_text(feature_text)
        print(f"[DEBUG] embed_text 완료, vector 길이: {len(vector)}")

        print(f"[DEBUG] search_similar_pets 시작...")
        matches = search_similar_pets(
            query_vector=vector,
            breed_filter=breed if confidence >= 0.7 else None,
            lat=None,
            lng=None,
            radius_m=2000,
            match_count=3,
        )
        print(f"[DEBUG] search_similar_pets 완료, {len(matches)}건")

        result_payload = {
            "breed": breed,
            "confidence": confidence,
            "featureText": feature_text,
            "topMatches": matches,
        }

        print(f"[DEBUG] tips 테이블 done 업데이트 시작...")
        supabase.table("tips").update(
            {"status": "done", "progress": 100, "results": result_payload, "updated_at": _now_iso()}
        ).eq("id", tip_id).execute()
        verify = supabase.table("tips").select("id, status").eq("id", tip_id).execute()
        actual_status = verify.data[0].get("status") if verify.data else None
        if actual_status != "done":
            raise RuntimeError(f"tips 업데이트 검증 실패: DB 실제 status={actual_status}")
        print(f"[DEBUG] tips 테이블 업데이트 완료! DB 확인 status=done")
        publish_progress(user_id, tip_id, 100, "완료")
        publish_done(user_id, tip_id, "done")
    except Exception as exc:
        print(f"[ERROR] process_tip_row 실패: {exc}")
        import traceback
        traceback.print_exc()
        supabase.table("tips").update(
            {"status": "failed", "error_msg": str(exc), "updated_at": _now_iso()}
        ).eq("id", tip_id).execute()
        publish_done(user_id, tip_id, "failed")


async def process_embedding(row: dict) -> None:
    """missing_pets 단일 행의 임베딩을 생성하고 pet_embeddings에 저장한다."""
    supabase = get_supabase()
    pet_id: str = row["id"]
    breed: str | None = row.get("breed")
    image_urls: list[str] = row.get("photos") or []

    try:
        print(f"[EMBED] pet={pet_id} 임베딩 시작 (이미지 {len(image_urls)}장, 품종={breed})")
        feature_text = await augment_features(image_urls, breed)
        embedding = embed_text(feature_text)
        upsert_embedding(pet_id, feature_text, embedding)
        # missing_pets의 embedding_status를 done으로 갱신
        supabase.table("missing_pets").update({"embedding_status": "done"}).eq("id", pet_id).execute()
        print(f"[EMBED] pet={pet_id} 완료 (vector dim={len(embedding)})")
    except Exception as exc:
        print(f"[EMBED ERROR] pet={pet_id} 실패: {exc}")
        import traceback
        traceback.print_exc()
        supabase.table("missing_pets").update({"embedding_status": "failed"}).eq("id", pet_id).execute()


async def poll_and_process(interval_seconds: int = 3) -> None:
    supabase = get_supabase()
    print("[INFO] 워커 폴링 시작...")
    while True:
        # --- tip 분석 폴링 ---
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
            if rows:
                print(f"[INFO] tips processing 상태 {len(rows)}건 발견")
            for row in rows:
                await process_tip_row(row)
        except Exception as e:
            print(f"[WARN] tips poll 에러: {e}")

        # --- 임베딩 인덱싱 폴링 ---
        try:
            embed_resp = (
                supabase.table("missing_pets")
                .select("id,breed,photos")
                .eq("embedding_status", "pending")
                .order("created_at")
                .limit(5)
                .execute()
            )
            embed_rows = embed_resp.data or []
            if embed_rows:
                print(f"[INFO] embedding pending 상태 {len(embed_rows)}건 발견")
            for row in embed_rows:
                await process_embedding(row)
        except Exception as e:
            print(f"[WARN] embedding poll 에러: {e}")

        await asyncio.sleep(interval_seconds)


if __name__ == "__main__":
    poll_interval = int(os.getenv("AI_WORKER_POLL_SECONDS", "3"))
    asyncio.run(poll_and_process(poll_interval))
