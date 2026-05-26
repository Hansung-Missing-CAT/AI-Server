from __future__ import annotations

import os
import tempfile
import base64
import json
import re
import io
from collections import Counter

import httpx
from anthropic import AsyncAnthropic
from PIL import Image, ImageFilter, ImageStat

from config import get_settings, get_supabase

ALLOWED_BREEDS = {"아비시니안", "브리티시 숏헤어", "칼리코", "알 수 없음"}
CLAUDE_MODEL_PRIMARY = os.getenv("ANTHROPIC_MODEL_PRIMARY", "claude-sonnet-4-20250514")
CLAUDE_MODEL_CANDIDATE = os.getenv("ANTHROPIC_MODEL_CANDIDATE", "claude-sonnet-4-5")


async def _download_file(client: httpx.AsyncClient, image_url: str) -> str | None:
    try:
        resp = await client.get(image_url, timeout=20)
        resp.raise_for_status()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as fp:
            fp.write(resp.content)
            return fp.name
    except Exception:
        return None


async def _classify_single_image(client: httpx.AsyncClient, image_path: str, api_key: str) -> tuple[str | None, float]:
    headers = {"x-api-key": api_key}
    try:
        with open(image_path, "rb") as file_obj:
            files = {"file": (os.path.basename(image_path), file_obj, "image/jpeg")}
            upload_resp = await client.post(
                "https://api.thecatapi.com/v1/images/upload",
                headers=headers,
                files=files,
                timeout=30,
            )
        upload_resp.raise_for_status()
        uploaded = upload_resp.json()
        image_id = uploaded.get("id")
        if not image_id:
            return None, 0.0

        info_resp = await client.get(f"https://api.thecatapi.com/v1/images/{image_id}", headers=headers, timeout=20)
        info_resp.raise_for_status()
        info = info_resp.json()
        breeds = info.get("breeds", [])
        if not breeds:
            return None, 0.0

        breed_name = breeds[0].get("name")
        confidence = 0.85 if breed_name else 0.0
        return breed_name, confidence
    except Exception:
        return None, 0.0


async def classify_breed(image_urls: list[str]) -> tuple[str | None, float]:
    settings = get_settings()
    if not image_urls or not settings.cat_api_key:
        if image_urls:
            return await _fallback_classify_with_claude(image_urls)
        return None, 0.0

    best_breed = None
    best_score = 0.0

    async with httpx.AsyncClient() as client:
        for image_url in image_urls[:2]:
            temp_path = await _download_file(client, image_url)
            if not temp_path:
                continue
            try:
                candidate, confidence = await _classify_single_image(client, temp_path, settings.cat_api_key)
                if candidate and confidence > best_score:
                    best_breed = candidate
                    best_score = confidence
            finally:
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    if not best_breed:
        return await _fallback_classify_with_claude(image_urls)

    try:
        supabase = get_supabase()
        mapped = (
            supabase.table("breed_mapping")
            .select("kr_name")
            .eq("cat_api_name", best_breed)
            .limit(1)
            .execute()
        )
        data = mapped.data or []
        if data and data[0].get("kr_name"):
            return data[0]["kr_name"], best_score
    except Exception:
        pass

    return best_breed, best_score


async def _fallback_classify_with_claude(image_urls: list[str]) -> tuple[str | None, float]:
    settings = get_settings()
    if not settings.anthropic_api_key or not image_urls:
        return None, 0.0

    try:
        anthropic = AsyncAnthropic(api_key=settings.anthropic_api_key)
        predictions: list[tuple[str, float, float]] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for image_url in image_urls[:2]:
                img_resp = await client.get(image_url)
                img_resp.raise_for_status()
                image_bytes = img_resp.content
                b64 = base64.b64encode(image_bytes).decode("utf-8")
                pred = await _classify_with_claude_single(anthropic, b64)
                if pred:
                    quality_score = _estimate_image_quality(image_bytes)
                    predictions.append((pred[0], pred[1], quality_score))

        if not predictions:
            return None, 0.0

        names = [_normalize_predicted_breed(name) for name, _, _ in predictions]
        confidences = [conf for _, conf, _ in predictions]
        qualities = [q for _, _, q in predictions]
        name_counter = Counter(names)
        best_name, votes = name_counter.most_common(1)[0]

        # confidence calibration:
        # - weighted base confidence by image quality (resolution + sharpness)
        # - consensus/disagreement adjustments across multi-image predictions
        quality_weight_sum = sum(qualities) if qualities else 0.0
        if quality_weight_sum > 0:
            weighted_conf = sum(c * q for c, q in zip(confidences, qualities)) / quality_weight_sum
        else:
            weighted_conf = sum(confidences) / len(confidences)

        avg_quality = sum(qualities) / len(qualities) if qualities else 0.5
        consensus_ratio = votes / len(predictions)
        consensus_adjust = (consensus_ratio - 0.5) * 0.24
        quality_adjust = (avg_quality - 0.5) * 0.18

        raw_conf = weighted_conf + consensus_adjust + quality_adjust
        final_conf = max(0.30, min(0.92, raw_conf))

        if best_name in {"알 수 없음", "unknown", "Unknown"}:
            return None, 0.0
        return best_name, round(final_conf, 2)
    except Exception:
        return None, 0.0


def _estimate_image_quality(image_bytes: bytes) -> float:
    # returns 0.0 ~ 1.0, blending resolution and edge-sharpness signals
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            rgb = img.convert("RGB")
            width, height = rgb.size
            pixels = max(1, width * height)
            resolution_score = min(1.0, pixels / (1024 * 1024))

            edges = rgb.filter(ImageFilter.FIND_EDGES).convert("L")
            sharpness_var = ImageStat.Stat(edges).var[0]
            sharpness_score = min(1.0, sharpness_var / 1500.0)

            return round((resolution_score * 0.55) + (sharpness_score * 0.45), 4)
    except Exception:
        return 0.5


def _extract_json(text: str) -> dict | None:
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except Exception:
        return None


async def _classify_with_claude_single(client: AsyncAnthropic, b64_image: str) -> tuple[str, float] | None:
    resp = await client.messages.create(
        model=CLAUDE_MODEL_PRIMARY,
        max_tokens=160,
        system=(
            "너는 고양이 품종 분류 전문가다. 반드시 JSON만 출력해라. "
            "허용 breed 값은 정확히 다음 중 하나만 가능하다: "
            "[아비시니안, 브리티시 숏헤어, 칼리코, 알 수 없음]. "
            "스키마: {\"breed\":\"허용값 중 하나\",\"confidence\":0~1 실수}. "
            "판별 근거가 약하거나 얼굴/몸통 특징이 가려져 있으면 반드시 '알 수 없음'을 선택해라. "
            "단, 고양이 윤곽/얼굴/털 패턴이 보이면 '알 수 없음' 대신 가장 가까운 허용 품종 하나를 선택해라. "
            "특징 기준: "
            "아비시니안=짧은 털, 티킹 패턴, 슬림한 체형. "
            "브리티시 숏헤어=둥근 얼굴, 통통한 체형, 촘촘한 단모. "
            "칼리코=흰색+주황/갈색+검정의 뚜렷한 3색 패턴."
        ),
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "다음 규칙으로 분류해줘:\n"
                            "1) 허용 라벨 외 값 금지\n"
                            "2) 고양이가 보이면 가장 가까운 허용 라벨 선택, 완전히 판별 불가할 때만 알 수 없음\n"
                            "3) JSON 외 텍스트 금지\n\n"
                            "few-shot 예시:\n"
                            "{\"breed\":\"칼리코\",\"confidence\":0.86}\n"
                            "{\"breed\":\"브리티시 숏헤어\",\"confidence\":0.81}\n"
                            "{\"breed\":\"알 수 없음\",\"confidence\":0.42}\n"
                        ),
                    },
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64_image}},
                ],
            }
        ],
    )
    text_chunks = []
    for block in resp.content:
        if getattr(block, "type", "") == "text":
            text_chunks.append(block.text.strip())
    answer = " ".join(text_chunks).strip()
    payload = _extract_json(answer)
    if not payload:
        return None
    breed = str(payload.get("breed", "")).strip()
    try:
        confidence = float(payload.get("confidence", 0.0))
    except Exception:
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))
    breed = _normalize_predicted_breed(breed)
    if not breed:
        return None
    return breed, confidence


def _normalize_predicted_breed(label: str | None) -> str:
    if not label:
        return "알 수 없음"
    s = str(label).strip().lower()
    mapping = {
        "abyssinian": "아비시니안",
        "아비시니안": "아비시니안",
        "british shorthair": "브리티시 숏헤어",
        "브리티시 숏헤어": "브리티시 숏헤어",
        "브리티시 쇼트헤어": "브리티시 숏헤어",
        "calico": "칼리코",
        "칼리코": "칼리코",
        "삼색고양이": "칼리코",
        "unknown": "알 수 없음",
        "알 수 없음": "알 수 없음",
        "none": "알 수 없음",
        "null": "알 수 없음",
    }
    normalized = mapping.get(s, "알 수 없음")
    return normalized if normalized in ALLOWED_BREEDS else "알 수 없음"
