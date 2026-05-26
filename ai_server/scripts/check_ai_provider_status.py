#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.breed_classifier import classify_breed


PROBE_URLS = [
    "https://cdn2.thecatapi.com/images/0XYvRd7oD.jpg",  # Abyssinian-like
    "https://cdn2.thecatapi.com/images/MTY3ODIyMQ.jpg",  # British-like
    "https://cdn2.thecatapi.com/images/bpc.jpg",  # Calico-like
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Check external AI provider readiness before batch run")
    p.add_argument("--min-detect-rate", type=float, default=0.34)
    return p.parse_args()


async def main_async(min_detect_rate: float) -> int:
    results = []
    detected = 0

    for url in PROBE_URLS:
        breed, confidence = await classify_breed([url])
        hit = bool(breed)
        if hit:
            detected += 1
        results.append(
            {
                "image_url": url,
                "breed": breed,
                "confidence": confidence,
                "detected": hit,
            }
        )

    detect_rate = detected / len(PROBE_URLS)
    payload = {
        "ok": detect_rate >= min_detect_rate,
        "min_detect_rate": min_detect_rate,
        "detect_rate": round(detect_rate, 4),
        "detected": detected,
        "total": len(PROBE_URLS),
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if payload["ok"] else 1


def main() -> int:
    args = parse_args()
    return asyncio.run(main_async(args.min_detect_rate))


if __name__ == "__main__":
    raise SystemExit(main())

