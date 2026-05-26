#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOWED = {"아비시니안", "브리티시 숏헤어", "칼리코", "unknown"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate real GT v2 human dataset")
    p.add_argument("--base", default="../../implementation_specs/real_dataset_30_ground_truth_v1_5.json")
    p.add_argument("--target", default="../../implementation_specs/real_dataset_30_ground_truth_v2_human.json")
    p.add_argument("--expected-count", type=int, default=30)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parent
    base_path = (root / args.base).resolve()
    target_path = (root / args.target).resolve()
    base_rows = json.loads(base_path.read_text(encoding="utf-8"))
    target_rows = json.loads(target_path.read_text(encoding="utf-8"))

    if len(target_rows) != args.expected_count:
        raise ValueError(f"count mismatch: {len(target_rows)} != {args.expected_count}")

    base_map = {r["id"]: r.get("file_name") for r in base_rows}
    target_ids = [r.get("id") for r in target_rows]
    if len(set(target_ids)) != len(target_ids):
        raise ValueError("duplicated id")
    if set(target_ids) != set(base_map):
        raise ValueError("id set mismatch with base")

    for r in target_rows:
        rid = r["id"]
        if r.get("file_name") != base_map[rid]:
            raise ValueError(f"file_name changed for {rid}")
        if r.get("expected_label") not in ALLOWED:
            raise ValueError(f"invalid label for {rid}: {r.get('expected_label')}")
        if not str(r.get("notes", "")).strip():
            raise ValueError(f"notes empty for {rid}")

    print("ok")
    print(f"count={len(target_rows)}")
    print(f"ids={len(set(target_ids))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
