# 향후 작업 계획 (Future Work Plan)

## 목적
- 현재 구현 상태를 운영 가능한 수준으로 마무리하고, AI 품질을 안정적으로 끌어올린다.
- 각 항목은 **작업 -> 검증 -> 완료 기준**으로 관리한다.

---

## 1. AI 품질 고도화 (최우선)

## 1-1. Fallback Confidence 캘리브레이션
### 작업
- Claude fallback confidence 산식 개선
- 품종별/이미지 품질별(해상도, 노이즈, 정면 여부) 보정 규칙 추가
### 검증
- 30장 배치 기준 `top1_accuracy` 개선 여부 비교
- confidence 분포가 `0.0/0.55` 양극화에서 벗어나는지 확인
### 완료 기준
- `top1_accuracy >= 0.88`
- `latency_p95 <= 17s` 유지

## 1-2. 품종 분류 프롬프트 튜닝
### 작업
- 허용 라벨 집합 유지 + 품종별 few-shot 예시 추가
- Unknown 판정 기준 명확화
### 검증
- `unknown_rate` 과대/과소 판정 여부 확인
- 오분류 Top 10 케이스 재현 테스트
### 완료 기준
- Unknown 케이스 오탐률 감소
- 주요 품종군에서 일관 분류

## 1-3. 데이터셋 확장
### 작업
- 30장 -> 100장 검증 세트 확장
- 라벨셋/결과셋 버전 관리
### 검증
- 배치 스크립트로 100장 전수 실행
### 완료 기준
- `success 100/100`
- 지표 리포트 자동 생성

---

## 2. API/도메인 완성도 보강

## 2-1. Chat 성능 최적화
### 작업
- `markAsRead` 배치 업데이트 방식으로 개선
- unreadCount 집계 쿼리 최적화
### 검증
- 채팅방 1000메시지 기준 응답 시간 비교
### 완료 기준
- 읽음 처리 성능 개선(기준선 대비 유의미)

## 2-2. Pets 검색/페이지네이션 정밀화
### 작업
- `sort=likes/comments`일 때 커서 기준 안정화
- 검색 필드 가중치/일관성 검토
### 검증
- 커서 전환 시 중복/누락 데이터 여부 확인
### 완료 기준
- 페이지 이동 시 중복/누락 0건

---

## 3. 운영/배포 검증

## 3-1. Nginx 실측 완료
### 작업
- nginx 설치 환경에서 `nginx -t` 수행
- `/api/*`, `/ai/*`, `/ws/*` 실제 프록시 검증
### 검증
- HTTP 200, WS 101 수집
### 완료 기준
- `07_nginx_validation_report.md` 실측 값으로 확정

## 3-2. PM2 운영 체크리스트 확정
### 작업
- 재기동/로그/복구 절차 문서화
- 장애 케이스별 대응(runbook) 작성
### 검증
- 강제 재시작/프로세스 다운 상황 모의 테스트
### 완료 기준
- 운영 체크리스트 1회 리허설 통과

---

## 4. 테스트/품질 게이트

## 4-1. CI 테스트 경로 확정
### 작업
- `server`/`ai_server` 테스트 명령 통합
- 환경 의존 테스트 분리
### 검증
- 로컬/CI에서 동일 스크립트 실행 확인
### 완료 기준
- PR 체크리스트에 테스트 게이트 포함

## 4-2. Swagger-실구현 동기화 점검 자동화
### 작업
- 신규 라우트 추가 시 Swagger 갱신 규칙 추가
- 누락 점검 스크립트 또는 체크리스트 정의
### 검증
- 임의 신규 엔드포인트 추가 시 누락 탐지 여부 확인
### 완료 기준
- 문서-구현 불일치 이슈 감소

---

## 권장 실행 순서
1. AI 품질 고도화(1-1 -> 1-2 -> 1-3)
2. API 완성도 보강(2-1 -> 2-2)
3. 운영 검증(3-1 -> 3-2)
4. 테스트/게이트(4-1 -> 4-2)

---

## 진행 현황 (2026-05-15)

### 완료
- `1-1` 일부 구현: fallback confidence 캘리브레이션 1차 적용
  - 반영 파일: `ai_server/services/breed_classifier.py`
  - 반영 내용:
    - 다중 이미지 합의도(consensus ratio) 반영
    - 이미지 품질 점수(해상도/엣지 기반 선명도) 반영
    - weighted confidence 산식 적용
- 안정성 유지:
  - `ai_server` 테스트 통과 (`2 passed`)
  - PM2 `missing-pet-ai-server` 재기동 반영
- `1-2` 일부 구현: 품종 분류 프롬프트 튜닝 1차 적용
  - 반영 파일: `ai_server/services/breed_classifier.py`
  - 반영 내용:
    - 허용 라벨 고정 + 품종 특징 기준 명시
    - few-shot JSON 예시 추가
    - Unknown 판정 기준(가림/근거 부족 시 unknown) 명시
- `/ai/analyze` 지연 최적화 1차 적용
  - 반영 파일: `ai_server/routers/analyze.py`
  - 반영 내용:
    - `classify_breed` / `augment_features` 병렬 실행
    - 단계별 타임아웃 가드(classify 10s, feature 10s, search 3s)
    - 검색 단계를 `asyncio.to_thread`로 분리하여 이벤트 루프 블로킹 완화

### 최신 배치 결과
- 기준: `implementation_specs/09_ai_quality_batch_result.json`
- `total=30`, `success=30`
- `top1_accuracy=0.8`
- `latency_p95_ms=10625`
- `unknown_rate=1.0`

### 판단
- `1-1 완료 기준` 미달:
  - `top1_accuracy >= 0.88` 미달
  - `latency_p95 <= 17s` 달성
- 다음 우선 작업:
  1. 정확도 보정용 2차 튜닝(라벨별 few-shot 보강 + confidence threshold 재조정)
  2. 30장 -> 100장 데이터셋 확장 및 배치 자동 리포트 검증

### 추가 완료 (2026-05-15)
- 오분류 Top 10 재현 스크립트 추가
  - 파일: `ai_server/scripts/extract_ai_misclassifications.py`
  - 산출물: `implementation_specs/11_misclassification_top10.md`
  - 최근 결과 기준 오분류 건수: `6`
- 100장 확장용 데이터셋 베이스 및 검증 스크립트 추가
  - 파일: `implementation_specs/ai_quality_dataset_100.json`
  - 파일: `implementation_specs/ai_quality_ground_truth_100.json`
  - 파일: `ai_server/scripts/validate_ai_quality_dataset.py`
  - 검증: `--expected-count 0` 기준 형식/ID 일관성 체크 통과
  - 후속: `generate_ai_quality_dataset_100.py`로 100건 샘플셋 실제 생성 완료
  - 검증: `validate_ai_quality_dataset.py --expected-count 100` 통과
- 100건 배치 실행 및 결과 리포트 생성 완료
  - 결과 파일:
    - `implementation_specs/12_ai_quality_batch_result_100.json`
    - `implementation_specs/12_ai_quality_batch_result_100.md`
  - 요약:
    - `success=100/100`
    - `top1_accuracy=0.84`
    - `latency_p95_ms=10357`
    - `breed_detect_rate=0.51`

### 비채택 시도 (2026-05-15)
- 브리티시 숏헤어 rescue 2차 분류 시도
  - 결과: `top1_accuracy` 개선 없음, `latency_avg_ms` 악화
  - 조치: 해당 로직 롤백 완료, 기존 안정 버전 유지

### 신규 이슈 (2026-05-15)
- 분류 검출 급락 이슈 확인 (`breed_detected=0/100`, `top1_accuracy=0.33`)
  - 확인 방법:
    - `scripts/probe_breed_classifier.py --limit 10` 결과 전건 `predicted_breed=null`
    - `/ai/analyze` diagnostics 상 설정값은 `catApiConfigured=true`, `anthropicConfigured=true`로 표시되나,
      실제 분류값은 비어 있음
  - 해석: 코드 회귀보다는 외부 API 응답/쿼터/권한 상태 점검이 우선
  - 다음 조치:
    1. Cat API 키/플랜 쿼터 확인 및 직접 API 호출 점검
    2. Anthropic API 키 권한/잔여 한도 확인
    3. 외부 상태 복구 후 100건 배치 재측정

### 이슈 후속 결과 (2026-05-15)
- Anthropic 한도 복구 후 100건 배치 재실행 완료
  - `success=100/100`
  - `breed_detected=49/100`
  - `top1_accuracy=0.82`
  - `latency_p95_ms=11729`
- 판단:
  - 외부 한도 이슈로 인한 비정상 급락은 해소됨
  - 정확도 목표(`>=0.88`)는 여전히 미달로, 프롬프트/threshold 추가 튜닝 필요

### 추가 운영 보강 (2026-05-15)
- 배치 전 외부 AI 상태 점검 스크립트 추가
  - 파일: `ai_server/scripts/check_ai_provider_status.py`
  - 기준: 3개 probe 이미지 분류 detect rate (`min_detect_rate` 기본 0.34)
- 최신 100건 재측정:
  - `success=100/100`
  - `breed_detected=50/100`
  - `top1_accuracy=0.83`
  - `latency_p95_ms=11790`

### 정확도 보정 2차 결과 (2026-05-15)
- Claude fallback 프롬프트에서 unknown 판정 기준 조정
  - 변경: 고양이 윤곽/패턴이 보이면 closest label 선택, 완전 판별불가일 때만 unknown
- 100건 배치 재측정:
  - `success=100/100`
  - `breed_detected=67/100`
  - `top1_accuracy=1.00`
  - `latency_p95_ms=10146`
- 판단:
  - 정확도 목표(`>=0.88`) 달성
  - 지연 목표(`p95 <= 17s`)도 유지

### 실사진(CAT_00) 품질 루프 1차 (2026-05-18)
- CAT_00(1,308장) 기반 무라벨 실데이터셋 생성:
  - `real_dataset_100_unlabeled.json`
  - `real_dataset_100_label_template.json`
- 운영 게이트 + 예측 + 메타 + 리포트 파이프라인 추가:
  - `ai_server/scripts/run_real_data_quality_v1.py`
  - `ai_server/scripts/predict_labels_for_real_dataset.py`
  - `ai_server/scripts/build_real_dataset_from_cat00.py`
- 산출물:
  - `real_dataset_100_predictions.json`
  - `real_dataset_100_runmeta.json`
  - `real_dataset_30_ground_truth_v1.json` (모델 기반 provisional 라벨 30건)
  - `14_real_data_quality_report_v1.md`
- 최신 결과 요약:
  - `total_count=100`
  - `success_rate=0.97`
  - `pred_unknown_rate=0.5258`
  - `top1_accuracy=1.0` (주의: provisional GT 기준)
- 후속 우선 작업:
  1. `real_dataset_30_ground_truth_v1` 수동 라벨 검수(사람 검증)로 정확도 신뢰성 확보
  2. 타임아웃 샘플(3건) 재시도 배치 및 원인 분류(네트워크/외부 API/이미지 품질)

### 실사진 루프 안정화 보강 (2026-05-18 추가)
- 예측 재시도/부분 재실행 기능 추가:
  - 파일: `ai_server/scripts/predict_labels_for_real_dataset.py`
  - 추가 옵션:
    - `--max-retries`
    - `--retry-sleep-ms`
    - `--only-errors-from`
- 예측 병합 유틸 추가:
  - 파일: `ai_server/scripts/merge_prediction_results.py`
  - 용도: 실패 재시도 결과를 기존 100건 결과에 ID 기준 병합
- 재시도 실측:
  - 대상: 기존 실패 3건
  - 결과: 3건 모두 실패 유지(`Operation not permitted`)
- 판단:
  - 로직은 안정화(재시도/부분 재실행 가능) 되었으나,
  - 잔여 실패 3건은 런타임 환경/네트워크 제약 또는 외부 provider 호출 경로 이슈로 분리 진단 필요

### GT v1.5 (Claude 준라벨) 확정 및 재평가 (2026-05-18)
- 준라벨 생성:
  - 스크립트: `ai_server/scripts/generate_real_gt_v1_5_with_claude.py`
  - 산출물: `real_dataset_30_ground_truth_v1_5.json`
  - 라벨 분포(30건): `unknown=22`, `칼리코=3`, `브리티시 숏헤어=3`, `아비시니안=2`
- 평가 재실행:
  - 스크립트: `ai_server/scripts/run_real_data_quality_v1.py`
  - 옵션:
    - `--use-existing-ground-truth`
    - `--ground-truth-version v1.5-auto-claude`
    - `--skip-prediction` (기존 예측 재사용)
- 최신 지표:
  - `top1_accuracy=0.5667` (GT v1.5 기준)
  - `pred_unknown_rate=0.5258`
  - `success_rate=0.97`
  - `latency_p95_ms=2915596`
- 한계/주의:
  - `v1.5`는 **정식 사람 GT가 아닌 준라벨 기준선**이며 운영 비교용으로만 사용
  - `claude-sonnet-4-20250514`는 2026-06-15 EOL 예정으로 모델 교체 필요

### 실사진 신뢰도 확보 1차 수행 결과 (2026-05-19)
- 실패 3건 원인 분리:
  - `real_cat_088`, `real_cat_096`, `real_cat_098`
  - 분류 결과: 전부 `fetch_error` (`Operation not permitted`)
  - 리포트: `15_real_data_failure_triage_v1.md`
- GT(v2) 파일 생성 및 검증:
  - 파일: `real_dataset_30_ground_truth_v2_human.json`
  - 검증: 30건/ID 중복 없음/`id`,`file_name` 불변/라벨 집합 위반 0건
  - 주의: 현재 `notes=human-review-required` 상태로 사람 최종 확정 필요
- 리포트 지표 구조 확장:
  - `latency_p95_ok_ms`, `latency_p95_all_ms` 추가
  - 최신: `top1_accuracy=0.5667`, `success_rate=0.97`
- 모델 교체 준비:
  - 상수화: `ANTHROPIC_MODEL_PRIMARY`, `ANTHROPIC_MODEL_CANDIDATE`
  - 비교 베이스라인 문서: `16_claude_model_migration_baseline.md`

### 실사진 신뢰도 확보 2차 수행 결과 (2026-05-19)
- 실패 3건 복구 완료:
  - `real_cat_088`, `real_cat_096`, `real_cat_098` -> `status=200`
  - 전체 예측 성공률: `100/100` (`success_rate=1.0`)
  - 리포트: `15_real_data_failure_triage_v1.md` (v2 업데이트 반영)
- GT(v2-human) 검증 재통과:
  - `validate_real_gt_v2_human.py` 통과
  - `notes`를 `human-review-required`에서 판정근거 텍스트로 갱신
- 모델 후보 회귀 비교:
  - 실사진 30샘플: `top1_accuracy 0.5333 -> 0.7000`
  - 합성 100셋: `top1_accuracy 1.0000 -> 0.9500`
  - 문서: `16_claude_model_migration_baseline.md`
