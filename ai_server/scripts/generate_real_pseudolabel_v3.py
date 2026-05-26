#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

import httpx
from anthropic import AsyncAnthropic

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import get_settings
from services.breed_classifier import classify_breed
from services.embedder import embed_text

ALLOWED = {"아비시니안", "브리티시 숏헤어", "칼리코", "unknown"}
LABEL_PROTOTYPES = {
    "아비시니안": "짧은 털, 티킹 패턴, 슬림한 체형, 큰 귀",
    "브리티시 숏헤어": "둥근 얼굴, 통통한 체형, 촘촘한 단모",
    "칼리코": "흰색과 주황/갈색/검정이 섞인 3색 패턴",
    "unknown": "근거 부족 또는 품종 판별 불가",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate real pseudolabel v3 with 3-way consensus")
    p.add_argument("--dataset", default="../../implementation_specs/real_dataset_100_unlabeled.json")
    p.add_argument("--output", default="../../implementation_specs/real_dataset_100_pseudolabel_v3.json")
    p.add_argument("--count", type=int, default=100)
    p.add_argument("--consensus-threshold", type=float, default=0.67)
    p.add_argument("--confidence-threshold", type=float, default=0.65)
    p.add_argument("--timeout", type=int, default=45)
    return p.parse_args()


def _norm(label: str | None) -> str:
    if not label:
        return "unknown"
    s = str(label).strip().lower()
    m = {
        "abyssinian": "아비시니안",
        "아비시니안": "아비시니안",
        "british shorthair": "브리티시 숏헤어",
        "브리티시 숏헤어": "브리티시 숏헤어",
        "브리티시 쇼트헤어": "브리티시 숏헤어",
        "calico": "칼리코",
        "칼리코": "칼리코",
        "삼색고양이": "칼리코",
        "unknown": "unknown",
        "알 수 없음": "unknown",
    }
    out = m.get(s, "unknown")
    return out if out in ALLOWED else "unknown"


def _nearest_embedding_label(feature_text: str) -> str:
    v = embed_text(feature_text)
    best = ("unknown", -1.0)
    for label, proto in LABEL_PROTOTYPES.items():
        pv = embed_text(proto)
        dot = sum(a * b for a, b in zip(v, pv))
        if dot > best[1]:
            best = (label, dot)
    return best[0]


async def _claude_label(client: AsyncAnthropic, http: httpx.AsyncClient, image_url: str) -> tuple[str, float]:
    img = await http.get(image_url)
    img.raise_for_status()
    b64 = base64.b64encode(img.content).decode("utf-8")
    msg = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=180,
        system=(
            "고양이 품종 보조 라벨러다. JSON만 출력. "
            "스키마: {\"breed\":\"아비시니안|브리티시 숏헤어|칼리코|unknown\",\"confidence\":0~1}."
        ),
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "허용 라벨 중 하나를 선택해."},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
                ],
            }
        ],
    )
    t = " ".join(x.text for x in msg.content if getattr(x, "type", "") == "text")
    try:
        payload = json.loads(t[t.find("{") : t.rfind("}") + 1])
    except Exception:
        return "unknown", 0.0
    return _norm(payload.get("breed")), max(0.0, min(1.0, float(payload.get("confidence", 0.0))))


async def main_async(args: argparse.Namespace) -> int:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY required")
    dataset_path = (Path(__file__).resolve().parent / args.dataset).resolve()
    output_path = (Path(__file__).resolve().parent / args.output).resolve()
    rows = json.loads(dataset_path.read_text(encoding="utf-8"))[: args.count]

    anth = AsyncAnthropic(api_key=settings.anthropic_api_key)
    proto = [{"label": k, "prototype": v} for k, v in LABEL_PROTOTYPES.items()]
    out = []
    async with httpx.AsyncClient(timeout=args.timeout) as http:
        for row in rows:
            image_url = row["image_url"]
            cat_label, cat_conf = await classify_breed([image_url])
            cat_label = _norm(cat_label)
            try:
                claude_l, claude_c = await _claude_label(anth, http, image_url)
            except Exception:
                claude_l, claude_c = "unknown", 0.0
            feature_text = f"cat_label={cat_label}, claude_label={claude_l}, file={row.get('file_name','')}"
            emb_label = _nearest_embedding_label(feature_text)

            votes = [cat_label, claude_l, emb_label]
            counts: dict[str, int] = {}
            for v in votes:
                counts[v] = counts.get(v, 0) + 1
            best_label = max(counts, key=lambda k: counts[k])
            consensus = counts[best_label] / 3.0
            max_conf = max(cat_conf or 0.0, claude_c)
            final = best_label if consensus >= args.consensus_threshold and max_conf >= args.confidence_threshold else "unknown"
            out.append(
                {
                    "id": row["id"],
                    "file_name": row.get("file_name"),
                    "image_url": image_url,
                    "expected_label": final,
                    "label_source": {"cat_api": cat_label, "claude": claude_l, "embedding": emb_label},
                    "consensus_score": round(consensus, 4),
                    "quality_score": round(max_conf, 4),
                    "attempts": 1,
                    "notes": "auto-pseudolabel-v3",
                }
            )

    output_path.write_text(json.dumps({"items": out, "prototypes": proto}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"count": len(out)}, ensure_ascii=False))
    print(f"wrote: {output_path}")
    return 0


def main() -> int:
    import asyncio

    return asyncio.run(main_async(parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
