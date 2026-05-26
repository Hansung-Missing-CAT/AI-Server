#!/usr/bin/env zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR/ai_server"

.venv/bin/python scripts/run_real_data_quality_v1.py \
  --dataset ../../implementation_specs/real_dataset_100_unlabeled.json \
  --predictions ../../implementation_specs/real_dataset_100_predictions.json \
  --gt-v1 ../../implementation_specs/real_dataset_30_ground_truth_v2_human.json \
  --runmeta ../../implementation_specs/real_dataset_100_runmeta.json \
  --report ../../implementation_specs/14_real_data_quality_report_v1.md \
  --ground-truth-version v2-human \
  --use-existing-ground-truth \
  --label-count 30 \
  --skip-prediction
