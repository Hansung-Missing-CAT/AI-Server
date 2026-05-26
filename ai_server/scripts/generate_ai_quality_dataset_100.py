#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    base = Path(__file__).resolve().parent
    dataset30_path = (base / "../../implementation_specs/ai_quality_dataset_30.json").resolve()
    gt30_path = (base / "../../implementation_specs/ai_quality_ground_truth_30.json").resolve()
    dataset100_path = (base / "../../implementation_specs/ai_quality_dataset_100.json").resolve()
    gt100_path = (base / "../../implementation_specs/ai_quality_ground_truth_100.json").resolve()

    dataset30 = json.loads(dataset30_path.read_text(encoding="utf-8"))
    gt30 = json.loads(gt30_path.read_text(encoding="utf-8"))

    dataset100 = []
    gt100 = []

    for idx in range(100):
        src_ds = dataset30[idx % len(dataset30)]
        src_gt = gt30[idx % len(gt30)]
        item_id = f"cat_{idx + 1:03d}"
        dataset100.append(
            {
                "id": item_id,
                "label_guess": src_ds["label_guess"],
                "image_url": src_ds["image_url"],
            }
        )
        gt100.append(
            {
                "id": item_id,
                "expected_label": src_gt["expected_label"],
            }
        )

    dataset100_path.write_text(json.dumps(dataset100, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    gt100_path.write_text(json.dumps(gt100, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"wrote: {dataset100_path}")
    print(f"wrote: {gt100_path}")
    print("count=100")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

