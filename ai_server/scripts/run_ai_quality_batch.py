#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import httpx


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run /ai/analyze quality batch")
    p.add_argument(
        "--dataset",
        default="../../implementation_specs/ai_quality_dataset_30.json",
        help="Path to dataset json",
    )
    p.add_argument("--base-url", default="http://127.0.0.1:8000", help="AI server base url")
    p.add_argument("--output-json", default="../../implementation_specs/09_ai_quality_batch_result.json")
    p.add_argument("--output-md", default="../../implementation_specs/09_ai_quality_batch_result.md")
    p.add_argument(
        "--ground-truth",
        default="../../implementation_specs/ai_quality_ground_truth_30.json",
        help="Path to ground truth labels json",
    )
    return p.parse_args()


def normalize_label(label: str | None) -> str:
    if not label:
        return "unknown"
    s = str(label).strip().lower()
    alias = {
        "none": "unknown",
        "null": "unknown",
        "unknown": "unknown",
        "아비시니안": "아비시니안",
        "abyssinian": "아비시니안",
        "브리티시 숏헤어": "브리티시 숏헤어",
        "브리티시 쇼트헤어": "브리티시 숏헤어",
        "british shorthair": "브리티시 숏헤어",
        "칼리코": "칼리코",
        "삼색고양이": "칼리코",
        "calico": "칼리코",
    }
    return alias.get(s, label)


def summarize(results: list[dict], ground_truth: dict[str, str]) -> dict:
    ok = [r for r in results if r.get("status") == 200]
    detected = [r for r in ok if r.get("breedDetected")]
    lat = [r.get("latencyMs", 0) for r in ok]
    acc_total = 0
    acc_hit = 0
    unknown_total = 0
    unknown_pred_unknown = 0
    for r in ok:
        item_id = r.get("id")
        if item_id not in ground_truth:
            continue
        pred = normalize_label(r.get("breed"))
        gt = normalize_label(ground_truth[item_id])
        acc_total += 1
        if pred == gt:
            acc_hit += 1
        if gt == "unknown":
            unknown_total += 1
            if pred == "unknown":
                unknown_pred_unknown += 1

    return {
        "total": len(results),
        "success": len(ok),
        "breed_detected": len(detected),
        "breed_detect_rate": round(len(detected) / len(ok), 4) if ok else 0.0,
        "latency_avg_ms": round(sum(lat) / len(lat), 2) if lat else 0.0,
        "latency_p95_ms": sorted(lat)[int(len(lat) * 0.95) - 1] if lat else 0.0,
        "top1_accuracy": round(acc_hit / acc_total, 4) if acc_total else 0.0,
        "unknown_rate": round(unknown_pred_unknown / unknown_total, 4) if unknown_total else 0.0,
        "evaluated_count": acc_total,
    }


def to_markdown(summary: dict, results: list[dict]) -> str:
    lines = [
        "# AI 품질 배치 결과",
        "",
        f"- total: {summary['total']}",
        f"- success: {summary['success']}",
        f"- breed_detected: {summary['breed_detected']}",
        f"- breed_detect_rate: {summary['breed_detect_rate']}",
        f"- latency_avg_ms: {summary['latency_avg_ms']}",
        f"- latency_p95_ms: {summary['latency_p95_ms']}",
        f"- top1_accuracy: {summary['top1_accuracy']}",
        f"- unknown_rate: {summary['unknown_rate']}",
        f"- evaluated_count: {summary['evaluated_count']}",
        "",
        "| id | status | ms | breed | confidence | detected | top1Similarity |",
        "|---|---:|---:|---|---:|---|---:|",
    ]
    for r in results:
        lines.append(
            f"| {r.get('id')} | {r.get('status')} | {r.get('latencyMs')} | "
            f"{r.get('breed')} | {r.get('confidence')} | {r.get('breedDetected')} | {r.get('top1Similarity')} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    dataset_path = (Path(__file__).resolve().parent / args.dataset).resolve()
    output_json = (Path(__file__).resolve().parent / args.output_json).resolve()
    output_md = (Path(__file__).resolve().parent / args.output_md).resolve()
    ground_truth_path = (Path(__file__).resolve().parent / args.ground_truth).resolve()

    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    gt_rows = json.loads(ground_truth_path.read_text(encoding="utf-8"))
    ground_truth = {x["id"]: x["expected_label"] for x in gt_rows}
    results: list[dict] = []

    with httpx.Client(timeout=60) as client:
        for item in dataset:
            started = time.time()
            payload = {"imageUrls": [item["image_url"]], "matchCount": 3}
            try:
                resp = client.post(f"{args.base_url}/ai/analyze", json=payload)
                elapsed_ms = int((time.time() - started) * 1000)
                body = resp.json()
                top = (body.get("topMatches") or [None])[0]
                results.append(
                    {
                        "id": item.get("id"),
                        "labelGuess": item.get("label_guess"),
                        "status": resp.status_code,
                        "latencyMs": elapsed_ms,
                        "breed": body.get("breed"),
                        "confidence": body.get("confidence"),
                        "breedDetected": (body.get("diagnostics") or {}).get("breedDetected"),
                        "top1Similarity": (top or {}).get("similarity") if top else None,
                    }
                )
            except Exception as exc:
                results.append(
                    {
                        "id": item.get("id"),
                        "labelGuess": item.get("label_guess"),
                        "status": "error",
                        "latencyMs": int((time.time() - started) * 1000),
                        "error": str(exc),
                    }
                )

    summary = summarize(results, ground_truth)
    output_json.write_text(json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    output_md.write_text(to_markdown(summary, results), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    print(f"wrote: {output_json}")
    print(f"wrote: {output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
