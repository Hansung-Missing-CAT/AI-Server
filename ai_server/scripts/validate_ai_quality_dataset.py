#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from collections import Counter


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate AI quality dataset/ground-truth consistency")
    p.add_argument("--dataset", default="../../implementation_specs/ai_quality_dataset_100.json")
    p.add_argument("--ground-truth", default="../../implementation_specs/ai_quality_ground_truth_100.json")
    p.add_argument("--expected-count", type=int, default=100)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    base = Path(__file__).resolve().parent
    ds_path = (base / args.dataset).resolve()
    gt_path = (base / args.ground_truth).resolve()

    dataset = json.loads(ds_path.read_text(encoding="utf-8"))
    gt = json.loads(gt_path.read_text(encoding="utf-8"))

    ds_ids = [x.get("id") for x in dataset]
    gt_ids = [x.get("id") for x in gt]
    ds_set = set(ds_ids)
    gt_set = set(gt_ids)

    if len(dataset) != args.expected_count or len(gt) != args.expected_count:
        print(
            json.dumps(
                {
                    "ok": False,
                    "reason": "count_mismatch",
                    "dataset_count": len(dataset),
                    "ground_truth_count": len(gt),
                    "expected_count": args.expected_count,
                },
                ensure_ascii=False,
            )
        )
        return 1

    missing_in_gt = sorted(ds_set - gt_set)
    missing_in_ds = sorted(gt_set - ds_set)
    ds_counter = Counter(ds_ids)
    gt_counter = Counter(gt_ids)
    duplicated_ds = sorted([k for k, v in ds_counter.items() if v > 1 and k is not None])
    duplicated_gt = sorted([k for k, v in gt_counter.items() if v > 1 and k is not None])

    ok = not (missing_in_gt or missing_in_ds or duplicated_ds or duplicated_gt)
    print(
        json.dumps(
            {
                "ok": ok,
                "dataset_count": len(dataset),
                "ground_truth_count": len(gt),
                "missing_in_ground_truth": missing_in_gt,
                "missing_in_dataset": missing_in_ds,
                "duplicated_dataset_ids": duplicated_ds,
                "duplicated_ground_truth_ids": duplicated_gt,
            },
            ensure_ascii=False,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
