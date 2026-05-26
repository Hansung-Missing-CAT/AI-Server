#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ALLOWED_LABELS = {"아비시니안", "브리티시 숏헤어", "칼리코", "unknown"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run real-data quality v1 pipeline")
    p.add_argument("--dataset", default="../../implementation_specs/real_dataset_100_unlabeled.json")
    p.add_argument("--predictions", default="../../implementation_specs/real_dataset_100_predictions.json")
    p.add_argument("--runmeta", default="../../implementation_specs/real_dataset_100_runmeta.json")
    p.add_argument("--gt-v1", default="../../implementation_specs/real_dataset_30_ground_truth_v1.json")
    p.add_argument("--ground-truth-version", default="v1-auto-provisional")
    p.add_argument("--use-existing-ground-truth", action="store_true")
    p.add_argument("--report", default="../../implementation_specs/14_real_data_quality_report_v1.md")
    p.add_argument("--base-url", default="http://127.0.0.1:8000")
    p.add_argument("--provider-min-detect-rate", type=float, default=0.34)
    p.add_argument("--label-count", type=int, default=30)
    p.add_argument("--prompt-version", default="fallback_unknown_relaxed_v2")
    p.add_argument("--predict-timeout", type=int, default=20)
    p.add_argument("--skip-prediction", action="store_true")
    return p.parse_args()


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def _normalize(label: str | None) -> str:
    if not label:
        return "unknown"
    s = str(label).strip().lower()
    mapping = {
        "아비시니안": "아비시니안",
        "abyssinian": "아비시니안",
        "브리티시 숏헤어": "브리티시 숏헤어",
        "브리티시 쇼트헤어": "브리티시 숏헤어",
        "british shorthair": "브리티시 숏헤어",
        "칼리코": "칼리코",
        "calico": "칼리코",
        "삼색고양이": "칼리코",
        "unknown": "unknown",
        "알 수 없음": "unknown",
        "none": "unknown",
        "null": "unknown",
    }
    out = mapping.get(s, "unknown")
    return out if out in ALLOWED_LABELS else "unknown"


def _build_gt_v1(pred_rows: list[dict], label_count: int) -> list[dict]:
    gt = []
    for row in pred_rows[:label_count]:
        gt.append(
            {
                "id": row["id"],
                "file_name": row.get("file_name"),
                "expected_label": _normalize(row.get("predicted_label")),
                "notes": "auto-provisional-from-model",
            }
        )
    return gt


def _compute_metrics(pred_rows: list[dict], gt_rows: list[dict]) -> dict:
    gt_map = {x["id"]: _normalize(x["expected_label"]) for x in gt_rows}
    total = len(pred_rows)
    success_rows = [r for r in pred_rows if r.get("status") == 200]
    success_rate = (len(success_rows) / total) if total else 0.0
    unknown_pred_count = sum(1 for r in success_rows if _normalize(r.get("predicted_label")) == "unknown")
    pred_unknown_rate = (unknown_pred_count / len(success_rows)) if success_rows else 0.0
    latencies_ok = sorted([int(r.get("latency_ms", 0)) for r in success_rows])
    p95_ok = latencies_ok[max(0, int(len(latencies_ok) * 0.95) - 1)] if latencies_ok else 0
    latencies_all = sorted([int(r.get("latency_ms", 0)) for r in pred_rows if r.get("latency_ms") is not None])
    p95_all = latencies_all[max(0, int(len(latencies_all) * 0.95) - 1)] if latencies_all else 0
    latencies_retry = sorted(
        [
            int(r.get("latency_ms", 0))
            for r in pred_rows
            if r.get("latency_ms") is not None and int(r.get("attempts", 1) or 1) > 1
        ]
    )
    p95_retry = latencies_retry[max(0, int(len(latencies_retry) * 0.95) - 1)] if latencies_retry else 0

    eval_rows = [r for r in success_rows if r.get("id") in gt_map]
    hit = 0
    mismatches = []
    for r in eval_rows:
        pred = _normalize(r.get("predicted_label"))
        exp = gt_map[r["id"]]
        if pred == exp:
            hit += 1
        else:
            mismatches.append(
                {
                    "id": r["id"],
                    "file_name": r.get("file_name"),
                    "expected": exp,
                    "predicted": pred,
                    "confidence": r.get("confidence", 0.0),
                    "latency_ms": r.get("latency_ms", 0),
                }
            )

    mismatches.sort(key=lambda x: (-float(x["confidence"] or 0.0), -int(x["latency_ms"] or 0)))
    outliers = sorted(
        [
            {
                "id": r.get("id"),
                "file_name": r.get("file_name"),
                "status": r.get("status"),
                "latency_ms": int(r.get("latency_ms", 0)),
                "attempts": int(r.get("attempts", 1) or 1),
            }
            for r in pred_rows
            if r.get("latency_ms") is not None
        ],
        key=lambda x: -x["latency_ms"],
    )

    return {
        "total_count": total,
        "labeled_count": len(gt_rows),
        "evaluated_count": len(eval_rows),
        "top1_accuracy": round((hit / len(eval_rows)), 4) if eval_rows else 0.0,
        "pred_unknown_rate": round(pred_unknown_rate, 4),
        "latency_p95_ok_ms": p95_ok,
        "latency_p95_all_ms": p95_all,
        "latency_p95_retry_inclusive_ms": p95_retry,
        "success_rate": round(success_rate, 4),
        "misclassifications_top10": mismatches[:10],
        "latency_outliers_top10": outliers[:10],
    }


def _validate_gt_rows(gt_rows: list[dict], expected_count: int) -> None:
    if len(gt_rows) != expected_count:
        raise ValueError(f"ground truth count mismatch: expected {expected_count}, got {len(gt_rows)}")
    ids = [str(x.get("id")) for x in gt_rows]
    if any(not i for i in ids):
        raise ValueError("ground truth has empty id")
    if len(set(ids)) != len(ids):
        raise ValueError("ground truth has duplicated id")
    for x in gt_rows:
        n = _normalize(x.get("expected_label"))
        if n not in ALLOWED_LABELS:
            raise ValueError(f"invalid expected_label: {x.get('expected_label')}")


def _to_report(meta: dict, metrics: dict) -> str:
    lines = [
        "# 실사진 품질 리포트 v1",
        "",
        f"- generated_at_utc: {meta['generated_at_utc']}",
        f"- prompt_version: {meta['prompt_version']}",
        f"- ground_truth_version: {meta.get('ground_truth_version', 'unknown')}",
        f"- provider_gate_ok: {meta['provider_gate']['ok']}",
        f"- provider_detect_rate: {meta['provider_gate'].get('detect_rate')}",
        "",
        "## 평가 대상",
        f"- 전체 샘플: {metrics['total_count']}",
        f"- 라벨 보유: {metrics['labeled_count']}",
        f"- 정확도 평가 대상: {metrics['evaluated_count']}",
        "",
        "## 지표",
        f"- top1_accuracy (라벨 보유 샘플): {metrics['top1_accuracy']}",
        f"- pred_unknown_rate (전체 성공 샘플): {metrics['pred_unknown_rate']}",
        f"- latency_p95_ok_ms (status=200 샘플): {metrics['latency_p95_ok_ms']}",
        f"- latency_p95_all_ms (전체 샘플): {metrics['latency_p95_all_ms']}",
        f"- latency_p95_retry_inclusive_ms (attempts>1 샘플): {metrics['latency_p95_retry_inclusive_ms']}",
        f"- success_rate (전체 샘플): {metrics['success_rate']}",
        "",
        "## 지연 Outlier Top 10",
        "| id | file_name | status | attempts | latency_ms |",
        "|---|---|---|---:|---:|",
    ]
    if not metrics["latency_outliers_top10"]:
        lines.append("| - | - | - | - | - |")
    else:
        for x in metrics["latency_outliers_top10"]:
            lines.append(
                f"| {x.get('id') or ''} | {x.get('file_name') or ''} | {x.get('status')} | "
                f"{x.get('attempts')} | {x.get('latency_ms')} |"
            )
    lines += [
        "",
        "## 오분류 Top 10",
        "| id | file_name | expected | predicted | confidence | latency_ms |",
        "|---|---|---|---|---:|---:|",
    ]
    if not metrics["misclassifications_top10"]:
        lines.append("| - | - | - | - | - | - |")
    else:
        for x in metrics["misclassifications_top10"]:
            lines.append(
                f"| {x['id']} | {x.get('file_name') or ''} | {x['expected']} | {x['predicted']} | "
                f"{x['confidence']} | {x['latency_ms']} |"
            )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    base = Path(__file__).resolve().parent
    dataset_path = (base / args.dataset).resolve()
    predictions_path = (base / args.predictions).resolve()
    runmeta_path = (base / args.runmeta).resolve()
    gt_v1_path = (base / args.gt_v1).resolve()
    report_path = (base / args.report).resolve()

    provider_cmd = [
        ".venv/bin/python",
        "scripts/check_ai_provider_status.py",
        "--min-detect-rate",
        str(args.provider_min_detect_rate),
    ]
    provider_res = _run(provider_cmd, cwd=base.parent)
    provider_stdout = provider_res.stdout.strip()
    provider_payload = {}
    if provider_stdout:
        try:
            provider_payload = json.loads(provider_stdout.splitlines()[-1])
        except Exception:
            provider_payload = {"ok": False, "raw": provider_stdout}
    if provider_res.returncode != 0 or not provider_payload.get("ok"):
        fail_meta = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "provider_unavailable",
            "provider_gate": provider_payload,
            "provider_stderr": provider_res.stderr,
        }
        runmeta_path.write_text(json.dumps(fail_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        report_path.write_text(
            "# 실사진 품질 리포트 v1\n\n- status: provider unavailable\n\n```json\n"
            + json.dumps(provider_payload, ensure_ascii=False, indent=2)
            + "\n```\n",
            encoding="utf-8",
        )
        print("provider unavailable")
        print(f"wrote: {runmeta_path}")
        print(f"wrote: {report_path}")
        return 1

    if not args.skip_prediction:
        predict_cmd = [
            ".venv/bin/python",
            "scripts/predict_labels_for_real_dataset.py",
            "--dataset",
            str(dataset_path),
            "--base-url",
            args.base_url,
            "--output",
            str(predictions_path),
            "--timeout",
            str(args.predict_timeout),
        ]
        pred_res = _run(predict_cmd, cwd=base.parent)
        if pred_res.returncode != 0:
            print(pred_res.stdout)
            print(pred_res.stderr)
            return pred_res.returncode
    elif not predictions_path.exists():
        raise FileNotFoundError(f"predictions file not found: {predictions_path}")

    pred_rows = json.loads(predictions_path.read_text(encoding="utf-8"))
    if args.use_existing_ground_truth and gt_v1_path.exists():
        gt_v1 = json.loads(gt_v1_path.read_text(encoding="utf-8"))
    else:
        gt_v1 = _build_gt_v1(pred_rows, args.label_count)
        gt_v1_path.write_text(json.dumps(gt_v1, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    _validate_gt_rows(gt_v1, args.label_count)

    metrics = _compute_metrics(pred_rows, gt_v1)
    runmeta = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ok",
        "dataset_path": str(dataset_path),
        "predictions_path": str(predictions_path),
        "gt_v1_path": str(gt_v1_path),
        "ground_truth_version": args.ground_truth_version,
        "prompt_version": args.prompt_version,
        "provider_gate": provider_payload,
        "metrics": {
            "total_count": metrics["total_count"],
            "labeled_count": metrics["labeled_count"],
            "evaluated_count": metrics["evaluated_count"],
            "top1_accuracy": metrics["top1_accuracy"],
            "pred_unknown_rate": metrics["pred_unknown_rate"],
            "latency_p95_ok_ms": metrics["latency_p95_ok_ms"],
            "latency_p95_all_ms": metrics["latency_p95_all_ms"],
            "latency_p95_retry_inclusive_ms": metrics["latency_p95_retry_inclusive_ms"],
            "success_rate": metrics["success_rate"],
        },
    }
    runmeta_path.write_text(json.dumps(runmeta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(_to_report(runmeta, metrics), encoding="utf-8")

    print(json.dumps(runmeta["metrics"], ensure_ascii=False))
    print(f"wrote: {runmeta_path}")
    print(f"wrote: {gt_v1_path}")
    print(f"wrote: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
