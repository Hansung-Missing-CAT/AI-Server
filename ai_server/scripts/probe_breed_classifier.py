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


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Probe breed classifier on dataset samples")
    p.add_argument("--dataset", default="../../implementation_specs/ai_quality_dataset_30.json")
    p.add_argument("--limit", type=int, default=10)
    return p.parse_args()


async def run() -> int:
    args = parse_args()
    base = Path(__file__).resolve().parent
    dataset_path = (base / args.dataset).resolve()
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))

    rows = []
    for item in dataset[: args.limit]:
        breed, conf = await classify_breed([item["image_url"]])
        rows.append(
            {
                "id": item["id"],
                "label_guess": item.get("label_guess"),
                "predicted_breed": breed,
                "confidence": conf,
                "image_url": item["image_url"],
            }
        )

    print(json.dumps({"count": len(rows), "rows": rows}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
