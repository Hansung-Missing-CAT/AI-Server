#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Extract top-N misclassifications from AI batch result")
    p.add_argument(
        "--result-json",
        default="../../implementation_specs/09_ai_quality_batch_result.json",
        help="Path to batch result json",
    )
    p.add_argument(
        "--ground-truth",
        default="../../implementation_specs/ai_quality_ground_truth_30.json",
        help="Path to ground truth json",
    )
    p.add_argument(
        "--dataset",
        default="../../implementation_specs/ai_quality_dataset_30.json",
        help="Path to dataset json",
    )
    p.add_argument(
        "--output-md",
        default="../../implementation_specs/11_misclassification_top10.md",
        help="Output markdown path",
    )
    p.add_argument("--top-n", type=int, default=10, help="Maximum number of rows")
    return p.parse_args()


def normalize_label(label: str | None) -> str:
    if label is None:
        return "unknown"
    s = str(label).strip().lower()
    mapping = {
        "unknown": "unknown",
        "none": "unknown",
        "null": "unknown",
        "아비시니안": "아비시니안",
        "abyssinian": "아비시니안",
        "브리티시 숏헤어": "브리티시 숏헤어",
        "브리티시 쇼트헤어": "브리티시 숏헤어",
        "british shorthair": "브리티시 숏헤어",
        "칼리코": "칼리코",
        "삼색고양이": "칼리코",
        "calico": "칼리코",
    }
    return mapping.get(s, s)


def build_markdown(rows: list[dict], top_n: int) -> str:
    lines = [
        "# AI 오분류 Top 10",
        "",
        f"- 기준: 최근 배치 결과에서 오분류 우선 {top_n}건 추출",
        "",
        "| id | expected | predicted | confidence | latencyMs | image_url |",
        "|---|---|---|---:|---:|---|",
    ]
    if not rows:
        lines.append("| - | - | - | - | - | - |")
    else:
        for row in rows:
            lines.append(
                f"| {row['id']} | {row['expected']} | {row['predicted']} | "
                f"{row['confidence']} | {row['latencyMs']} | {row['image_url']} |"
            )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    base = Path(__file__).resolve().parent

    result_path = (base / args.result_json).resolve()
    gt_path = (base / args.ground_truth).resolve()
    dataset_path = (base / args.dataset).resolve()
    output_path = (base / args.output_md).resolve()

    result = json.loads(result_path.read_text(encoding="utf-8"))
    gt_rows = json.loads(gt_path.read_text(encoding="utf-8"))
    dataset_rows = json.loads(dataset_path.read_text(encoding="utf-8"))

    gt = {x["id"]: normalize_label(x["expected_label"]) for x in gt_rows}
    image_urls = {x["id"]: x.get("image_url", "") for x in dataset_rows}

    mismatches = []
    for row in result.get("results", []):
        item_id = row.get("id")
        if item_id not in gt:
            continue
        if row.get("status") != 200:
            continue
        expected = gt[item_id]
        predicted = normalize_label(row.get("breed"))
        if predicted != expected:
            mismatches.append(
                {
                    "id": item_id,
                    "expected": expected,
                    "predicted": predicted,
                    "confidence": row.get("confidence", 0.0),
                    "latencyMs": row.get("latencyMs", 0),
                    "image_url": image_urls.get(item_id, ""),
                }
            )

    mismatches.sort(key=lambda x: (-float(x["confidence"] or 0.0), -int(x["latencyMs"] or 0), x["id"]))
    top_rows = mismatches[: max(0, args.top_n)]

    output_path.write_text(build_markdown(top_rows, args.top_n), encoding="utf-8")
    print(f"mismatch_count={len(mismatches)}")
    print(f"wrote: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

