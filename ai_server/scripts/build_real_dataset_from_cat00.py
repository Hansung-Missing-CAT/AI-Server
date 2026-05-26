#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build unlabeled real cat dataset from CAT_00 folder")
    p.add_argument(
        "--source-dir",
        default="../../CAT_00",
        help="Directory containing real cat images",
    )
    p.add_argument(
        "--count",
        type=int,
        default=100,
        help="Number of images to include",
    )
    p.add_argument(
        "--base-url",
        default="http://127.0.0.1:18080",
        help="Base URL for local static server",
    )
    p.add_argument(
        "--output-dataset",
        default="../../implementation_specs/real_dataset_100_unlabeled.json",
        help="Output dataset json path",
    )
    p.add_argument(
        "--output-label-template",
        default="../../implementation_specs/real_dataset_100_label_template.json",
        help="Output label template json path",
    )
    return p.parse_args()


def is_image(path: Path) -> bool:
    return path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}


def main() -> int:
    args = parse_args()
    base = Path(__file__).resolve().parent

    source_dir = (base / args.source_dir).resolve()
    output_dataset = (base / args.output_dataset).resolve()
    output_label_template = (base / args.output_label_template).resolve()

    files = sorted([p for p in source_dir.iterdir() if p.is_file() and is_image(p)])
    selected = files[: max(0, args.count)]

    dataset = []
    labels = []

    for idx, file_path in enumerate(selected, start=1):
        item_id = f"real_cat_{idx:03d}"
        image_url = f"{args.base_url.rstrip('/')}/{file_path.name}"
        dataset.append(
            {
                "id": item_id,
                "label_guess": "unknown",
                "image_url": image_url,
                "file_name": file_path.name,
                "source": "CAT_00",
            }
        )
        labels.append(
            {
                "id": item_id,
                "file_name": file_path.name,
                "expected_label": "",
                "notes": "",
            }
        )

    output_dataset.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_label_template.write_text(json.dumps(labels, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"source_count={len(files)}")
    print(f"selected_count={len(selected)}")
    print(f"wrote: {output_dataset}")
    print(f"wrote: {output_label_template}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

