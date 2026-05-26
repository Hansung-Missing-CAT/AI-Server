# 실사진 실패 3건 원인 분리 리포트 (v2)

- 기준 실행:
  - `scripts/predict_labels_for_real_dataset.py --only-errors-from ../../implementation_specs/real_dataset_100_predictions.json --max-retries 4 --retry-sleep-ms 800`
- 결과 파일:
  - 1차 재시도: `implementation_specs/real_dataset_100_predictions_retry_v2.json`
  - 2차 재시도(권한 상승 실행): `implementation_specs/real_dataset_100_predictions_retry_v4.json`

| sample_id | stage | 원인 | 재현 명령 | 조치 결과 |
|---|---|---|---|---|
| `real_cat_088` | `fetch_error` | `[Errno 1] Operation not permitted` (초기 재현) | `predict_labels_for_real_dataset.py ... --only-errors-from ...` | 2차 재시도에서 `status=200` 복구 |
| `real_cat_096` | `fetch_error` | `[Errno 1] Operation not permitted` (초기 재현) | `predict_labels_for_real_dataset.py ... --only-errors-from ...` | 2차 재시도에서 `status=200` 복구 |
| `real_cat_098` | `fetch_error` | `[Errno 1] Operation not permitted` (초기 재현) | `predict_labels_for_real_dataset.py ... --only-errors-from ...` | 2차 재시도에서 `status=200` 복구 |

## 해석
- 초기 실패는 권한/실행 환경 영향으로 재현되었고, 권한 상승 실행 경로에서 3건 모두 복구되었다.
- 최종 상태는 `real_dataset_100_predictions.json` 기준 `success_rate=1.0` (100/100)이다.

## 2026-05-26 추가 점검
- PM2 health 체크:
  - `http://127.0.0.1:3000/health` -> 200
  - `http://127.0.0.1:8000/health` -> 200
- provider gate:
  - `scripts/check_ai_provider_status.py` -> `ok=false`, `detect_rate=0.0`
- 판단:
  - fetch_error 3건 복구 상태는 유지되지만, 당일 provider 불안정으로 신규 예측 재생성은 중단.
  - 리포트 갱신은 `--skip-prediction` 경로로 진행.
