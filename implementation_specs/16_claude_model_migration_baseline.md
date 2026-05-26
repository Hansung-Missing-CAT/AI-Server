# Claude 모델 교체 준비 비교표 (Baseline, 2026-05-26 갱신)

## 후보 확정
- 현재 운영 모델: `claude-sonnet-4-20250514`
- 교체 후보(1차): `claude-sonnet-4-5`
- **채택 결정(2026-05-26): `claude-sonnet-4-20250514` 유지 (교체 보류)**

## 공통 상수화 반영
- `ANTHROPIC_MODEL_PRIMARY` (기본값: `claude-sonnet-4-20250514`)
- `ANTHROPIC_MODEL_CANDIDATE` (기본값: `claude-sonnet-4-5`)

## 최소 비교표 (교체 전/후)
### 실사진 30샘플 기준(운영 기준, v2-human)
| 구분 | top1_accuracy | pred_unknown_rate | latency_p95_ok_ms | success_rate |
|---|---:|---:|---:|---:|
| 교체 전 (`claude-sonnet-4-20250514`) | 0.5667 | 0.51 | 2915596 | 1.0 |
| 교체 후 (`claude-sonnet-4-5`) | 미측정(당일 provider gate 실패) | 미측정 | 미측정 | 미측정 |

### 합성 100셋 비교
| 구분 | top1_accuracy | unknown_rate | latency_p95_ms | success |
|---|---:|---:|---:|---:|
| 교체 전 (기존 기록) | 1.0000 | 1.0000 | 10146 | 100 |
| 교체 후 (`17_ai_quality_batch_result_100_candidate`) | 0.9500 | 1.0000 | 15466 | 100 |

## 채택 근거
- 실사진 운영 리포트(v2-human)에서 당일 후보 재평가를 완료하지 못했다(provider gate 실패).
- 합성 100셋에서는 후보 모델이 정확도/지연 모두 열세(`1.0000 -> 0.9500`, `10146 -> 15466`).
- 운영 기준(실사진 + 합성 동시 충족) 미달로 기본 모델 유지, 후보 모델은 재평가 대기.

## 롤백 조건
- 후보 모델 적용 후 아래 중 하나라도 충족 시 즉시 롤백:
  1. 합성 100셋 `top1_accuracy < 0.98`
  2. 합성 100셋 `latency_p95_ms > 13000`
  3. 실사진 `success_rate < 0.99`

## 실행 가이드(다음 사이클)
1. provider gate 정상화 확인 후 후보 모델로 재기동 (`ANTHROPIC_MODEL_PRIMARY=claude-sonnet-4-5`)
2. 실사진 100 재예측 + v2-human 평가 재산출(동일 조건)
3. 합성 100셋 재평가와 함께 채택/롤백 규칙 재판정
