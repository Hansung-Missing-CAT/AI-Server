#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
from pathlib import Path

import httpx
from anthropic import AsyncAnthropic

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import get_settings

ALLOWED_LABELS = {"아비시니안", "브리티시 숏헤어", "칼리코", "unknown"}
CLAUDE_MODEL_PRIMARY = os.getenv("ANTHROPIC_MODEL_PRIMARY", "claude-sonnet-4-20250514")
CLAUDE_MODEL_CANDIDATE = os.getenv("ANTHROPIC_MODEL_CANDIDATE", "claude-sonnet-4-5")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate real dataset GT v1.5 with Claude pseudo-labeling")
    p.add_argument("--dataset", default="../../implementation_specs/real_dataset_100_unlabeled.json")
    p.add_argument("--output", default="../../implementation_specs/real_dataset_30_ground_truth_v1_5.json")
    p.add_argument("--count", type=int, default=30)
    p.add_argument("--confidence-threshold", type=float, default=0.65)
    p.add_argument("--timeout", type=int, default=30)
    return p.parse_args()


def _normalize(label: str | None) -> str:
    if not label:
        return "unknown"
    s = str(label).strip().lower()
    mapping = {
        "아비시니안": "아비시니안",
        "abyssinian": "아비시니안",
        "브리티시 숏헤어": "브리티시 숏헤어",
        "브리티시 쇼트헤어": "브리티시 숏헤어",
        "british shorthair": "브리티시 숏헤어",
        "칼리코": "칼리코",
        "calico": "칼리코",
        "삼색고양이": "칼리코",
        "unknown": "unknown",
        "알 수 없음": "unknown",
        "none": "unknown",
        "null": "unknown",
    }
    out = mapping.get(s, "unknown")
    return out if out in ALLOWED_LABELS else "unknown"


def _extract_json(text: str) -> dict | None:
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


async def _classify_one(
    anthropic: AsyncAnthropic,
    client: httpx.AsyncClient,
    image_url: str,
) -> tuple[str, float, str]:
    resp = await client.get(image_url)
    resp.raise_for_status()
    image_bytes = resp.content
    b64 = base64.b64encode(image_bytes).decode("utf-8")

    msg = await anthropic.messages.create(
        model=CLAUDE_MODEL_PRIMARY,
        max_tokens=220,
        system=(
            "너는 고양이 품종 분류 보조 라벨러다. 반드시 JSON만 출력한다. "
            "허용 breed 값: [아비시니안, 브리티시 숏헤어, 칼리코, unknown]. "
            "스키마: {\"breed\":\"허용값\",\"confidence\":0~1,\"reason\":\"한국어 한 줄\"}. "
            "근거가 약하면 unknown을 선택한다."
        ),
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "이미지를 보고 허용 라벨 중 하나로 분류해줘."},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
                ],
            }
        ],
    )
    text = " ".join(block.text for block in msg.content if getattr(block, "type", "") == "text").strip()
    payload = _extract_json(text) or {}

    label = _normalize(payload.get("breed"))
    try:
        confidence = float(payload.get("confidence", 0.0))
    except Exception:
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))
    reason = str(payload.get("reason", "")).strip()
    if not reason:
        reason = "근거 텍스트 미제공"
    return label, confidence, reason


async def _run(args: argparse.Namespace, dataset_path: Path, output_path: Path) -> int:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured")

    rows = json.loads(dataset_path.read_text(encoding="utf-8"))
    rows = rows[: args.count]
    anthropic = AsyncAnthropic(api_key=settings.anthropic_api_key)

    out = []
    async with httpx.AsyncClient(timeout=args.timeout) as client:
        for row in rows:
            rid = row["id"]
            file_name = row.get("file_name")
            image_url = row["image_url"]
            try:
                label, confidence, reason = await _classify_one(anthropic, client, image_url)
            except Exception as exc:
                label, confidence, reason = "unknown", 0.0, f"분류 실패: {exc}"

            if label not in ALLOWED_LABELS:
                label = "unknown"
            if confidence < args.confidence_threshold:
                label = "unknown"
                reason = f"신뢰도 낮음({confidence:.2f}) - {reason}"

            out.append(
                {
                    "id": rid,
                    "file_name": file_name,
                    "expected_label": label,
                    "notes": f"auto-labeled-by-claude | {reason}",
                    "confidence": round(confidence, 4),
                }
            )

    output_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"count={len(out)}")
    print(f"wrote: {output_path}")
    return 0


def main() -> int:
    args = parse_args()
    base = Path(__file__).resolve().parent
    dataset_path = (base / args.dataset).resolve()
    output_path = (base / args.output).resolve()
    import asyncio

    return asyncio.run(_run(args, dataset_path, output_path))


if __name__ == "__main__":
    raise SystemExit(main())
