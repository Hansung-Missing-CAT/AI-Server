#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build final no-human quality report")
    p.add_argument("--anchor-result", default="../../implementation_specs/18_anchor_eval_result.json")
    p.add_argument("--real-pseudolabel", default="../../implementation_specs/real_dataset_100_pseudolabel_v3.json")
    p.add_argument("--runmeta", default="../../implementation_specs/real_dataset_100_runmeta.json")
    p.add_argument("--report", default="../../implementation_specs/final_quality_report_nohuman_v1.md")
    return p.parse_args()


def _read(path: str) -> dict:
    p = (Path(__file__).resolve().parent / path).resolve()
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()
    anchor = _read(args.anchor_result)
    pseudo = _read(args.real_pseudolabel)
    runmeta = _read(args.runmeta)
    out_path = (Path(__file__).resolve().parent / args.report).resolve()

    items = pseudo.get("items", [])
    total = len(items)
    hi = [x for x in items if x.get("expected_label") != "unknown" and float(x.get("consensus_score", 0)) >= 0.67]
    consensus_reliability = round(len(hi) / total, 4) if total else 0.0
    unknown_rate_pseudo = round(sum(1 for x in items if x.get("expected_label") == "unknown") / total, 4) if total else 0.0

    m = runmeta.get("metrics", {})
    anchor_summary = anchor.get("summary", anchor)
    text = "\n".join(
        [
            "# Final Quality Report (No-Human v1)",
            "",
            "## 1) Anchor Accuracy",
            f"- anchor_top1_accuracy: {anchor_summary.get('top1_accuracy')}",
            f"- anchor_evaluated_count: {anchor_summary.get('evaluated_count')}",
            "",
            "## 2) Consensus Reliability",
            f"- consensus_reliability: {consensus_reliability}",
            f"- pseudolabel_unknown_rate: {unknown_rate_pseudo}",
            f"- pseudolabel_total: {total}",
            "",
            "## 3) Operational Stability",
            f"- success_rate: {m.get('success_rate')}",
            f"- pred_unknown_rate: {m.get('pred_unknown_rate')}",
            f"- latency_p95_ok_ms: {m.get('latency_p95_ok_ms')}",
            f"- latency_p95_all_ms: {m.get('latency_p95_all_ms')}",
            f"- latency_p95_retry_inclusive_ms: {m.get('latency_p95_retry_inclusive_ms')}",
            "",
            "## 4) Decision",
            "- decision_rule: anchor_top1_accuracy 우위 + success_rate >= 0.99 + latency 악화폭 <= 10%",
            "- note: 사람 라벨 미사용 운영 기준",
            "",
        ]
    )
    out_path.write_text(text + "\n", encoding="utf-8")
    print(f"wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
