# Missing Pet Finder 구현 작업명세서 (실행용)

이 디렉터리는 프로젝트 전체를 완성하기 위한 실행 문서 세트입니다.  
각 문서는 순서대로 수행하도록 설계되어 있으며, 각 단계별 검증 절차를 포함합니다.

## 문서 구성

1. [01_execution_rules.md](./01_execution_rules.md)
2. [02_phase_plan.md](./02_phase_plan.md)
3. [03_server_swagger_requirement.md](./03_server_swagger_requirement.md)
4. [04_current_state_assessment.md](./04_current_state_assessment.md)
5. [05_remediation_workspec.md](./05_remediation_workspec.md)
6. [06_tips_queue_strategy_decision.md](./06_tips_queue_strategy_decision.md)
7. [07_nginx_validation_report.md](./07_nginx_validation_report.md)
8. [08_ai_quality_batch_report.md](./08_ai_quality_batch_report.md)
9. [ai_quality_dataset_30.json](./ai_quality_dataset_30.json)
10. [09_ai_quality_batch_result.md](./09_ai_quality_batch_result.md)
11. [ai_quality_ground_truth_30.json](./ai_quality_ground_truth_30.json)
12. [10_future_work_plan.md](./10_future_work_plan.md)
13. [11_misclassification_top10.md](./11_misclassification_top10.md)
14. [ai_quality_dataset_100.json](./ai_quality_dataset_100.json)
15. [ai_quality_ground_truth_100.json](./ai_quality_ground_truth_100.json)
16. [12_ai_quality_batch_result_100.md](./12_ai_quality_batch_result_100.md)
17. [13_misclassification_top10_100.md](./13_misclassification_top10_100.md)
18. [real_dataset_100_unlabeled.json](./real_dataset_100_unlabeled.json)
19. [real_dataset_100_label_template.json](./real_dataset_100_label_template.json)
20. [real_dataset_100_predictions.json](./real_dataset_100_predictions.json)
21. [real_dataset_100_runmeta.json](./real_dataset_100_runmeta.json)
22. [real_dataset_30_ground_truth_v1.json](./real_dataset_30_ground_truth_v1.json)
23. [real_dataset_30_ground_truth_v1_5.json](./real_dataset_30_ground_truth_v1_5.json)
24. [real_dataset_30_ground_truth_v2_human.json](./real_dataset_30_ground_truth_v2_human.json)
25. [14_real_data_quality_report_v1.md](./14_real_data_quality_report_v1.md)
26. [15_real_data_failure_triage_v1.md](./15_real_data_failure_triage_v1.md)
27. [16_claude_model_migration_baseline.md](./16_claude_model_migration_baseline.md)
28. [17_ai_quality_batch_result_30_candidate.md](./17_ai_quality_batch_result_30_candidate.md)
29. [17_ai_quality_batch_result_100_candidate.md](./17_ai_quality_batch_result_100_candidate.md)
30. [catapi_anchor_dataset.json](./catapi_anchor_dataset.json)
31. [catapi_anchor_ground_truth_mapped.json](./catapi_anchor_ground_truth_mapped.json)
32. [18_anchor_eval_result.json](./18_anchor_eval_result.json)
33. [real_dataset_100_pseudolabel_v3.json](./real_dataset_100_pseudolabel_v3.json)
34. [final_quality_report_nohuman_v1.md](./final_quality_report_nohuman_v1.md)
35. [nohuman_pipeline_status_v1.json](./nohuman_pipeline_status_v1.json)

## 테스트 실행
- `server`: `cd server && npm test`
- `ai_server`: `cd ai_server && pytest -q`

## 원클릭 PM2 테스트 실행
- 선행 조건:
  - 루트 `.env` 준비
  - `ai_server/.venv` 준비
  - `pm2` 설치 및 PATH 등록
- 실행:
  1. `npm run test:up`
  2. `npm run test:quality`
  3. `npm run test:down`
- 장애 점검 순서:
  - 포트 충돌(`18080`, `8000`)
  - `.venv` 실행 파일 존재(`ai_server/.venv/bin/python`, `uvicorn`)
  - API 키 및 외부 provider 상태(`.env`)

## 무인 라벨링 품질 루프 (No-Human v1)
- 실행:
  - `cd ai_server`
  - `.venv/bin/python scripts/run_nohuman_quality_v1.py --per-label 30 --real-count 100`
- 주요 산출물:
  - `catapi_anchor_dataset.json`
  - `18_anchor_eval_result.json`
  - `real_dataset_100_pseudolabel_v3.json`
  - `final_quality_report_nohuman_v1.md`

## 수행 순서

1. `01_execution_rules.md` 확인
2. `03_server_swagger_requirement.md` 먼저 반영 (server 공통 테스트 기반)
3. `02_phase_plan.md`를 Phase 0부터 순차 수행
4. 각 Phase 검증 통과 후 다음 단계 진행
5. 구현 중간 점검 시 `04`(평가서) 업데이트
6. 보완 개발은 `05`(보완 작업 명세서) 우선순위대로 수행

## 완료 기준

- 모든 Phase 작업/검증 체크리스트 완료
- `server` Swagger UI에서 인증 포함 API 테스트 가능
- PM2 기준 `server`/`ai_server` 동시 기동 및 health 통과
- Supabase/Redis/Queue/Storage/Realtime 경로 검증 완료
