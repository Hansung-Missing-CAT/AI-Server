#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import httpx


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Predict labels for unlabeled real cat dataset via /ai/analyze")
    p.add_argument(
        "--dataset",
        default="../../implementation_specs/real_dataset_100_unlabeled.json",
        help="Input unlabeled dataset json",
    )
    p.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="AI server base URL",
    )
    p.add_argument(
        "--output",
        default="../../implementation_specs/real_dataset_100_predictions.json",
        help="Output prediction json",
    )
    p.add_argument("--timeout", type=int, default=60)
    p.add_argument("--max-retries", type=int, default=2, help="Retry count for timeout/transport errors")
    p.add_argument("--retry-sleep-ms", type=int, default=400, help="Backoff between retries")
    p.add_argument(
        "--only-errors-from",
        default="",
        help="If provided, run only IDs whose status != 200 in the given prediction file",
    )
    return p.parse_args()


def _load_error_ids(path: Path | None) -> set[str]:
    if not path:
        return set()
    rows = json.loads(path.read_text(encoding="utf-8"))
    return {str(r.get("id")) for r in rows if r.get("status") != 200}


def _classify_error_stage(message: str) -> str:
    m = (message or "").lower()
    if "json" in m and ("decode" in m or "expecting value" in m):
        return "parse_error"
    if any(x in m for x in ["timed out", "connection", "dns", "name or service", "all connection attempts failed"]):
        return "provider_error"
    if any(x in m for x in ["operation not permitted", "permission denied", "no such file", "404"]):
        return "fetch_error"
    return "provider_error"


def main() -> int:
    args = parse_args()
    base = Path(__file__).resolve().parent
    dataset_path = (base / args.dataset).resolve()
    output_path = (base / args.output).resolve()

    rows = json.loads(dataset_path.read_text(encoding="utf-8"))
    error_path = (base / args.only_errors_from).resolve() if args.only_errors_from else None
    error_ids = _load_error_ids(error_path)
    if error_ids:
        rows = [r for r in rows if str(r.get("id")) in error_ids]
    results = []

    with httpx.Client(timeout=args.timeout) as client:
        for row in rows:
            payload = {"imageUrls": [row["image_url"]], "matchCount": 3}
            last_error = ""
            for attempt in range(args.max_retries + 1):
                started = time.time()
                try:
                    resp = client.post(f"{args.base_url}/ai/analyze", json=payload)
                    body = resp.json()
                    elapsed = int((time.time() - started) * 1000)
                    results.append(
                        {
                            "id": row["id"],
                            "file_name": row.get("file_name"),
                            "image_url": row["image_url"],
                            "status": resp.status_code,
                            "predicted_label": body.get("breed") or "unknown",
                            "confidence": body.get("confidence", 0.0),
                            "latency_ms": elapsed,
                            "attempts": attempt + 1,
                        }
                    )
                    break
                except Exception as exc:
                    elapsed = int((time.time() - started) * 1000)
                    last_error = str(exc)
                    if attempt < args.max_retries:
                        time.sleep(args.retry_sleep_ms / 1000)
                        continue
                    results.append(
                        {
                            "id": row["id"],
                            "file_name": row.get("file_name"),
                            "image_url": row["image_url"],
                            "status": "error",
                            "predicted_label": "unknown",
                            "confidence": 0.0,
                            "latency_ms": elapsed,
                            "attempts": attempt + 1,
                            "error_stage": _classify_error_stage(last_error),
                            "error": last_error,
                        }
                    )

    output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"count={len(results)}")
    print(f"wrote: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
