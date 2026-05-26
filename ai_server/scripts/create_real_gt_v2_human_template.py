#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Create GT v2 human template from v1.5 pseudo labels")
    p.add_argument("--input", default="../../implementation_specs/real_dataset_30_ground_truth_v1_5.json")
    p.add_argument("--output", default="../../implementation_specs/real_dataset_30_ground_truth_v2_human.json")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    base = Path(__file__).resolve().parent
    in_path = (base / args.input).resolve()
    out_path = (base / args.output).resolve()

    rows = json.loads(in_path.read_text(encoding="utf-8"))
    out = []
    for r in rows:
        out.append(
            {
                "id": r["id"],
                "file_name": r.get("file_name"),
                "expected_label": r.get("expected_label", "unknown"),
                "notes": "human-review-required",
            }
        )

    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"count={len(out)}")
    print(f"wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
