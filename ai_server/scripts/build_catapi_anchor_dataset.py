#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx
from PIL import Image, ImageStat

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import get_settings

ALLOWED = {"아비시니안", "브리티시 숏헤어", "칼리코", "unknown"}

CATAPI_TO_KR = {
    "Abyssinian": "아비시니안",
    "British Shorthair": "브리티시 숏헤어",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build anchor dataset from The Cat API has_breeds=true images")
    p.add_argument("--output-dataset", default="../../implementation_specs/catapi_anchor_dataset.json")
    p.add_argument("--output-gt", default="../../implementation_specs/catapi_anchor_ground_truth_mapped.json")
    p.add_argument("--per-label", type=int, default=40)
    p.add_argument("--max-pages", type=int, default=80)
    p.add_argument("--limit", type=int, default=25)
    p.add_argument("--min-width", type=int, default=320)
    p.add_argument("--min-height", type=int, default=320)
    p.add_argument("--blur-threshold", type=float, default=10.0)
    return p.parse_args()


def _near_duplicate_key(url: str) -> str:
    return url.rsplit("/", 1)[-1].split("?", 1)[0].lower()


def _is_low_quality(width: int, height: int, image_bytes: bytes, blur_threshold: float) -> bool:
    if width <= 0 or height <= 0:
        return True
    try:
        from io import BytesIO

        img = Image.open(BytesIO(image_bytes)).convert("L")
        stat = ImageStat.Stat(img)
        variance = stat.var[0] if stat.var else 0.0
        return variance < blur_threshold
    except Exception:
        return False


def _map_label(breeds: list[dict]) -> str:
    names = [b.get("name") for b in breeds if b.get("name")]
    mapped = [CATAPI_TO_KR.get(n, None) for n in names]
    mapped = [x for x in mapped if x]
    if mapped:
        return mapped[0]
    # fallback calico inference by category/name conventions
    text = " ".join([str(x).lower() for x in names])
    if "calico" in text:
        return "칼리코"
    return "unknown"


def main() -> int:
    args = parse_args()
    settings = get_settings()
    if not settings.cat_api_key:
        raise RuntimeError("CAT_API_KEY is required")

    out_dataset = (Path(__file__).resolve().parent / args.output_dataset).resolve()
    out_gt = (Path(__file__).resolve().parent / args.output_gt).resolve()

    counts = {"아비시니안": 0, "브리티시 숏헤어": 0, "칼리코": 0}
    keep: list[dict] = []
    seen_keys: set[str] = set()

    headers = {"x-api-key": settings.cat_api_key}
    with httpx.Client(timeout=30, headers=headers) as client:
        for page in range(args.max_pages):
            if all(v >= args.per_label for v in counts.values()):
                break
            resp = client.get(
                "https://api.thecatapi.com/v1/images/search",
                params={
                    "has_breeds": "true",
                    "include_breeds": "true",
                    "mime_types": "jpg,png",
                    "size": "med",
                    "order": "RANDOM",
                    "limit": args.limit,
                    "page": page,
                },
            )
            resp.raise_for_status()
            rows = resp.json()
            for r in rows:
                url = r.get("url")
                if not url:
                    continue
                k = _near_duplicate_key(url)
                if k in seen_keys:
                    continue
                label = _map_label(r.get("breeds") or [])
                if label not in counts:
                    continue
                if counts[label] >= args.per_label:
                    continue

                w = int(r.get("width") or 0)
                h = int(r.get("height") or 0)
                if w < args.min_width or h < args.min_height:
                    continue
                try:
                    img = client.get(url)
                    img.raise_for_status()
                    if _is_low_quality(w, h, img.content, args.blur_threshold):
                        continue
                except Exception:
                    continue

                idx = len(keep) + 1
                item_id = f"anchor_cat_{idx:04d}"
                keep.append(
                    {
                        "id": item_id,
                        "image_url": url,
                        "file_name": k,
                        "source": "thecatapi",
                        "label_guess": label,
                    }
                )
                seen_keys.add(k)
                counts[label] += 1
                if all(v >= args.per_label for v in counts.values()):
                    break

    gt = [{"id": x["id"], "expected_label": x["label_guess"]} for x in keep]
    out_dataset.write_text(json.dumps(keep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_gt.write_text(json.dumps(gt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"count": len(keep), "counts": counts}, ensure_ascii=False))
    print(f"wrote: {out_dataset}")
    print(f"wrote: {out_gt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
