#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Merge patch prediction rows into full prediction rows by id")
    p.add_argument("--base", default="../../implementation_specs/real_dataset_100_predictions.json")
    p.add_argument("--patch", required=True)
    p.add_argument("--output", default="../../implementation_specs/real_dataset_100_predictions.json")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    base_rows = json.loads(Path(args.base).read_text(encoding="utf-8"))
    patch_rows = json.loads(Path(args.patch).read_text(encoding="utf-8"))
    patch_map = {str(r.get("id")): r for r in patch_rows}

    merged = []
    replaced = 0
    for row in base_rows:
        rid = str(row.get("id"))
        if rid in patch_map:
            merged.append(patch_map[rid])
            replaced += 1
        else:
            merged.append(row)

    Path(args.output).write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"base={len(base_rows)} patch={len(patch_rows)} replaced={replaced}")
    print(f"wrote: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
