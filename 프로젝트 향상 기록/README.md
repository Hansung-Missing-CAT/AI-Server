# 프로젝트 향상 기록

## 한눈에 보기
이 프로젝트는 **초기 스캐폴딩(헬스체크 중심)** 상태에서 시작해, 현재는 다음이 가능한 단계까지 향상됐다.
- API 도메인 기능 구현(인증/사용자/Pets/채팅/제보/알림/업로드/디바이스)
- 운영 루프 구축(PM2, Redis/BullMQ, Supabase 연동)
- AI 품질 측정 루프 구축(데이터셋 생성 -> 배치 평가 -> 리포트 자동화)

핵심 변화는 “돌아간다” 수준에서 “측정하고 개선할 수 있다” 수준으로 올라온 것이다.

---

## 향상 흐름 (기존 + 최신 통합)

### 1) 기동 중심 -> 기능 중심
- 기존: `GET /health` 확인 중심
- 향상:
  - Auth/Users API 구현
  - Pets CRUD + Like/Comment 구현
  - Chats + 소켓 이벤트(`message.new`, `message.read`, `chat.updated`, `presence.update`)
  - Tips/Notifications/Uploads/Devices API 구현
  - Swagger 문서 경로 확장 (`/docs`, `/docs/openapi.json`)

### 2) 단발 실행 -> 운영 가능한 구조
- 기존: 수동 실행/점검 위주
- 향상:
  - PM2 기반 다중 프로세스(`server`, `ai_server`, `ai_worker`) 운영 체계 정비
  - Supabase/Redis/BullMQ/FCM 경로 정리
  - 재시작/로그/상태 확인 루프 확보

### 3) 감 기반 확인 -> 지표 기반 품질 관리
- 기존: 개별 호출 성공 여부 중심
- 향상:
  - AI 품질 배치 스크립트 체계 구축
  - 30건 검증셋 -> 100건 검증셋으로 확장
  - 오분류 추출/리포트 자동화
  - provider 상태 게이트 추가(`check_ai_provider_status.py`)

### 4) 합성 데이터 중심 -> 실사진 평가 루프 추가
- 기존: 합성/정답셋 평가 중심
- 향상:
  - `CAT_00` 실사진(1,308장) 기반 무라벨 100셋 생성
  - 실사진 파이프라인 구축(게이트 -> 예측 -> runmeta -> 리포트)
  - 실패 샘플 재실행 안정화:
    - `predict_labels_for_real_dataset.py`에 `--max-retries`, `--retry-sleep-ms`, `--only-errors-from`
    - `merge_prediction_results.py` 추가

### 5) 최신 추가: 준라벨 GT v1.5 기준선 도입
- 신규:
  - `generate_real_gt_v1_5_with_claude.py` 추가
  - `run_real_data_quality_v1.py` 확장
    - `--use-existing-ground-truth`
    - `--ground-truth-version`
    - `--skip-prediction`
- 효과:
  - “실사진 + 부분 라벨” 기준으로 재평가 가능한 상태 확보
  - 단, v1.5는 **비수동 GT**이므로 운영 비교용 기준선으로만 사용

---

## 현재 성능 상태 (최신 기준)

### A. 합성/정답셋(100) 기준
- `success=100/100`
- `top1_accuracy=1.00`
- `latency_p95_ms=10146`

### B. 실사진/사람검수 GT(v2-human) 기준
- `top1_accuracy=0.5667`
- `pred_unknown_rate=0.51`
- `success_rate=1.0`
- `latency_p95_ms=2915596`

해석:
- 합성셋에서는 목표 정확도/지연을 달성했다.
- 실사진에서는 지연 이상치가 매우 커 운영 지표 해석을 왜곡하고 있다.

---

## 남은 이슈 (현재 기준)
1. 실사진 실패 3건은 복구됐지만(100/100), provider gate 변동이 있어 재예측 안정성이 낮음
2. 실사진 `latency_p95_ms` 이상치 큼(지표 분해 필요)
3. `claude-sonnet-4-20250514` 모델 EOL(2026-06-15) 대응 필요

---

## 다음 우선순위
1. provider gate 정상화 후 실사진 100 재예측 1회 고정 실행
2. 실사진 리포트의 p95/outlier 분해를 고정 포맷으로 유지
3. Claude 후보 모델(`claude-sonnet-4-5`) 동일 조건 회귀 재실행
4. 채택/롤백 결정 문서 최종 확정

---

## 관련 산출물
- [implementation_specs/README.md](/Users/chaeminsoo/모바일%20캡스톤/backend-server/implementation_specs/README.md)
- [implementation_specs/14_real_data_quality_report_v1.md](/Users/chaeminsoo/모바일%20캡스톤/backend-server/implementation_specs/14_real_data_quality_report_v1.md)
- [implementation_specs/real_dataset_100_runmeta.json](/Users/chaeminsoo/모바일%20캡스톤/backend-server/implementation_specs/real_dataset_100_runmeta.json)
- [implementation_specs/real_dataset_30_ground_truth_v1_5.json](/Users/chaeminsoo/모바일%20캡스톤/backend-server/implementation_specs/real_dataset_30_ground_truth_v1_5.json)
