# 실사진 품질 리포트 v1

- generated_at_utc: 2026-05-25T15:18:53.421494+00:00
- prompt_version: fallback_unknown_relaxed_v2
- ground_truth_version: v2-human
- provider_gate_ok: True
- provider_detect_rate: 1.0

## 평가 대상
- 전체 샘플: 100
- 라벨 보유: 30
- 정확도 평가 대상: 30

## 지표
- top1_accuracy (라벨 보유 샘플): 0.5667
- pred_unknown_rate (전체 성공 샘플): 0.51
- latency_p95_ok_ms (status=200 샘플): 2915596
- latency_p95_all_ms (전체 샘플): 2915596
- latency_p95_retry_inclusive_ms (attempts>1 샘플): 0
- success_rate (전체 샘플): 1.0

## 지연 Outlier Top 10
| id | file_name | status | attempts | latency_ms |
|---|---|---|---:|---:|
| real_cat_077 | 00000009_026.jpg | 200 | 1 | 3030145 |
| real_cat_075 | 00000009_022.jpg | 200 | 1 | 3022607 |
| real_cat_083 | 00000010_029.jpg | 200 | 1 | 3013087 |
| real_cat_095 | 00000011_023.jpg | 200 | 1 | 3005048 |
| real_cat_079 | 00000010_003.jpg | 200 | 1 | 2932251 |
| real_cat_089 | 00000011_010.jpg | 200 | 1 | 2915596 |
| real_cat_093 | 00000011_017.jpg | 200 | 1 | 2890644 |
| real_cat_086 | 00000011_003.jpg | 200 | 1 | 2879316 |
| real_cat_097 | 00000011_027.jpg | 200 | 1 | 2769384 |
| real_cat_090 | 00000011_014.jpg | 200 | 1 | 2762085 |

## 오분류 Top 10
| id | file_name | expected | predicted | confidence | latency_ms |
|---|---|---|---|---:|---:|
| real_cat_013 | 00000002_003.jpg | unknown | 아비시니안 | 0.92 | 8403 |
| real_cat_015 | 00000002_026.jpg | unknown | 칼리코 | 0.91 | 8477 |
| real_cat_011 | 00000001_029.jpg | unknown | 칼리코 | 0.91 | 8452 |
| real_cat_001 | 00000001_000.jpg | unknown | 브리티시 숏헤어 | 0.91 | 6069 |
| real_cat_028 | 00000004_012.jpg | unknown | 아비시니안 | 0.9 | 351488 |
| real_cat_027 | 00000004_008.jpg | unknown | 브리티시 숏헤어 | 0.88 | 8814 |
| real_cat_009 | 00000001_024.jpg | unknown | 브리티시 숏헤어 | 0.88 | 8772 |
| real_cat_007 | 00000001_017.jpg | unknown | 아비시니안 | 0.86 | 9196 |
| real_cat_018 | 00000003_012.jpg | unknown | 브리티시 숏헤어 | 0.86 | 8314 |
| real_cat_029 | 00000004_018.jpg | unknown | 아비시니안 | 0.85 | 8976 |

## 2026-05-26 실행 메모
- 본 리포트는 `--skip-prediction`으로 기존 `real_dataset_100_predictions.json`을 사용해 재산출했다.
- 같은 날 라이브 provider 점검(`check_ai_provider_status.py`)은 `detect_rate=0.0`으로 실패했다.
- 따라서 본 수치는 **예측 모델 재실행 결과가 아니라 기존 예측 + v2-human GT 재평가 결과**로 해석해야 한다.
