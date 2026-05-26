# Final Quality Report (No-Human v1)

## 1) Anchor Accuracy
- anchor_top1_accuracy: 0.875
- anchor_evaluated_count: 32

## 2) Consensus Reliability
- consensus_reliability: 0.1
- pseudolabel_unknown_rate: 0.9
- pseudolabel_total: 20

## 3) Operational Stability
- success_rate: 1.0
- pred_unknown_rate: 0.51
- latency_p95_ok_ms: 2915596
- latency_p95_all_ms: 2915596
- latency_p95_retry_inclusive_ms: 0

## 4) Decision
- decision_rule: anchor_top1_accuracy 우위 + success_rate >= 0.99 + latency 악화폭 <= 10%
- note: 사람 라벨 미사용 운영 기준

