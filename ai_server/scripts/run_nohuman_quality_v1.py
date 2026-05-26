#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run no-human quality pipeline v1")
    p.add_argument("--per-label", type=int, default=30)
    p.add_argument("--real-count", type=int, default=100)
    p.add_argument("--status-report", default="../../implementation_specs/nohuman_pipeline_status_v1.json")
    return p.parse_args()


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def main() -> int:
    args = parse_args()
    base = Path(__file__).resolve().parent
    repo = base.parent
    report_path = (base / args.status_report).resolve()

    steps = []

    gate_provider = _run([".venv/bin/python", "scripts/check_ai_provider_status.py", "--min-detect-rate", "0.34"], cwd=repo)
    ok_provider = gate_provider.returncode == 0
    steps.append({"step": "provider_readiness", "ok": ok_provider, "stdout": gate_provider.stdout[-400:]})
    if not ok_provider:
        report_path.write_text(
            json.dumps(
                {
                    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                    "status": "provider_unavailable",
                    "steps": steps,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print("provider_unavailable")
        print(f"wrote: {report_path}")
        return 1

    gate_fetch = _run(["curl", "-sf", "http://127.0.0.1:18080/"], cwd=repo)
    ok_fetch = gate_fetch.returncode == 0
    steps.append({"step": "image_server_reachability", "ok": ok_fetch})
    if not ok_fetch:
        report_path.write_text(
            json.dumps(
                {
                    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                    "status": "fetch_unavailable",
                    "steps": steps,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print("fetch_unavailable")
        print(f"wrote: {report_path}")
        return 1

    steps_to_run = [
        [".venv/bin/python", "scripts/build_catapi_anchor_dataset.py", "--per-label", str(args.per_label)],
        [".venv/bin/python", "scripts/evaluate_anchor_set.py"],
        [".venv/bin/python", "scripts/generate_real_pseudolabel_v3.py", "--count", str(args.real_count)],
        [".venv/bin/python", "scripts/build_final_quality_report_nohuman_v1.py"],
    ]
    for cmd in steps_to_run:
        res = _run(cmd, cwd=repo)
        steps.append({"step": " ".join(cmd[:2]), "ok": res.returncode == 0, "stdout": res.stdout[-300:]})
        if res.returncode != 0:
            report_path.write_text(
                json.dumps(
                    {
                        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                        "status": "failed",
                        "failed_cmd": cmd,
                        "steps": steps,
                        "stderr": res.stderr[-500:],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            print("failed")
            print(f"wrote: {report_path}")
            return 1

    report_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "status": "ok",
                "steps": steps,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("ok")
    print(f"wrote: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
