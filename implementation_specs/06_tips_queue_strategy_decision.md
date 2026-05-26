# Tips 큐 처리 전략 결정서

## 결정 일자
- 2026-05-13

## 배경
- 원 명세는 Python 측 BullMQ 소비 워커를 전제로 작성됨.
- 현재 저장소는 Python BullMQ 소비 안정성/운영 복잡도 대비, 빠른 통합 안정화를 우선함.

## 최종 결정
- **단기(현행): Polling Worker 유지**
  - `ai_server/workers/ai_worker.py`
  - `tips.status='processing'` 레코드를 주기 폴링하여 처리
  - Redis Pub/Sub(`tip:progress`, `tip:done`)로 진행률 전달
- **중기(전환): BullMQ 소비 워커로 단계 전환**
  - 조건: Python BullMQ 소비 라이브러리/운영모델 확정 시 전환

## 채택 이유
1. 현재 코드베이스 기준으로 실패 복구/상태 추적이 단순함
2. `tips` 테이블 상태 기반으로 재처리/관찰이 명확함
3. 서버-워커 간 의존성 최소화로 초기 장애면 축소

## 단점
1. 실시간성은 BullMQ push 모델보다 낮음
2. polling interval 튜닝 필요
3. 처리량 급증 시 DB 폴링 비용 증가

## 운영 가드레일
- `AI_WORKER_POLL_SECONDS` 기본 3초, 운영에서 부하 관찰 후 조정
- 1회 루프 처리 건수 제한 유지(현재 limit 적용)
- 실패 건은 `tips.status='failed'`, `error_msg` 기록
- `tip:done` 발행 여부로 클라이언트 완료 신호 일치 확인

## 검증 체크리스트
- [ ] `POST /api/tips/analyze` 후 `processing` 저장 확인
- [ ] 워커 처리 후 `done` 또는 `failed` 전이 확인
- [ ] `tip:progress`, `tip:done` 소켓 수신 확인
- [ ] 실패 건 재처리 정책(수동/자동) 운영 합의 완료

## BullMQ 전환 조건 (Exit Criteria)
- Python BullMQ 소비 경로가 운영환경에서 24시간 무중단 검증
- 재시도/backoff/중복처리 방지 정책 코드화
- 전환 후 polling worker 비활성화 계획 수립
