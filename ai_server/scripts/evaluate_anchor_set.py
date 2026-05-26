#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ALLOWED = {"아비시니안", "브리티시 숏헤어", "칼리코", "unknown"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Evaluate anchor set against /ai/analyze")
    p.add_argument("--dataset", default="../../implementation_specs/catapi_anchor_dataset.json")
    p.add_argument("--ground-truth", default="../../implementation_specs/catapi_anchor_ground_truth_mapped.json")
    p.add_argument("--base-url", default="http://127.0.0.1:8000")
    p.add_argument("--output", default="../../implementation_specs/18_anchor_eval_result.json")
    p.add_argument("--timeout", type=int, default=45)
    return p.parse_args()


def _norm(label: str | None) -> str:
    if not label:
        return "unknown"
    s = str(label).strip().lower()
    m = {
        "abyssinian": "아비시니안",
        "아비시니안": "아비시니안",
        "british shorthair": "브리티시 숏헤어",
        "브리티시 숏헤어": "브리티시 숏헤어",
        "브리티시 쇼트헤어": "브리티시 숏헤어",
        "calico": "칼리코",
        "칼리코": "칼리코",
        "삼색고양이": "칼리코",
        "unknown": "unknown",
        "알 수 없음": "unknown",
    }
    out = m.get(s, "unknown")
    return out if out in ALLOWED else "unknown"


def main() -> int:
    args = parse_args()
    base = Path(__file__).resolve().parent
    ds = json.loads((base / args.dataset).resolve().read_text(encoding="utf-8"))
    gt = json.loads((base / args.ground_truth).resolve().read_text(encoding="utf-8"))
    gt_map = {x["id"]: _norm(x["expected_label"]) for x in gt}
    out_path = (base / args.output).resolve()

    rows = []
    with httpx.Client(timeout=args.timeout) as client:
        for item in ds:
            started = time.time()
            payload = {"imageUrls": [item["image_url"]], "matchCount": 3}
            try:
                resp = client.post(f"{args.base_url}/ai/analyze", json=payload)
                body = resp.json()
                pred = _norm(body.get("breed"))
                rows.append(
                    {
                        "id": item["id"],
                        "status": resp.status_code,
                        "predicted_label": pred,
                        "expected_label": gt_map.get(item["id"], "unknown"),
                        "latency_ms": int((time.time() - started) * 1000),
                    }
                )
            except Exception as exc:
                rows.append(
                    {
                        "id": item["id"],
                        "status": "error",
                        "predicted_label": "unknown",
                        "expected_label": gt_map.get(item["id"], "unknown"),
                        "latency_ms": int((time.time() - started) * 1000),
                        "error": str(exc),
                    }
                )

    ok = [r for r in rows if r.get("status") == 200]
    eval_rows = [r for r in ok if r["id"] in gt_map]
    hit = sum(1 for r in eval_rows if r["predicted_label"] == r["expected_label"])
    summary = {
        "total": len(rows),
        "success": len(ok),
        "evaluated_count": len(eval_rows),
        "top1_accuracy": round(hit / len(eval_rows), 4) if eval_rows else 0.0,
        "success_rate": round(len(ok) / len(rows), 4) if rows else 0.0,
    }
    out_path.write_text(json.dumps({"summary": summary, "results": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    print(f"wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
