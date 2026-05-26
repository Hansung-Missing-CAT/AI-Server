# 보완 작업 명세서 (우선순위 실행본)

## 목적
- `04_current_state_assessment.md`에서 확인된 미흡 항목을 명세 완료 수준으로 보완한다.
- 각 작업은 **구현 -> 검증 -> 실패 시 점검** 순서를 강제한다.

---

## 진행 상태 (2026-05-13)
- [x] P0-1 AI 임베딩 실모델 전환
- [x] P0-2 Cat API 분류 경로 정합화
- [x] P0-3 조회수 Redis 버퍼 + 배치 flush
- [x] P1-1 Chat 목록 `q`/`unreadCount` 보강
- [x] P1-2 Pet 상세 `isLiked` 실값 반영
- [x] P1-3 Tips 큐 전략 결정 문서화 (`06_tips_queue_strategy_decision.md`)
- [x] P2-1 Swagger 대상 API 범위 확장
- [x] P2-2 통합 테스트 최소 세트 작성 (mock 기반 smoke 테스트 추가)
- [x] P2-3 Nginx 실측 검증 리포트 작성 (환경 제약 포함 부분완료 보고서 작성)

---

## P0 (즉시) - 기능 정확성/신뢰성

## Task P0-1: AI 임베딩을 실제 모델로 교체
### 작업
- `ai_server/services/embedder.py`
  - `sentence-transformers`의 `paraphrase-multilingual-mpnet-base-v2` 로딩
  - 싱글턴 캐시 적용
  - `normalize_embeddings=True` 사용
### 검증
- 샘플 한국어 문장 입력 시 길이 768 벡터 반환
- 벡터 norm이 `0.99~1.01` 범위
### 실패 시 점검
- Python 버전/torch 설치
- 모델 다운로드 네트워크 접근

## Task P0-2: Cat API 분류 로직 정합화
### 작업
- `ai_server/services/breed_classifier.py`
  - 입력 이미지 URL 다운로드
  - Cat API 실제 분석 엔드포인트에 이미지 전달
  - 2장까지 분석 후 최고 confidence 채택
### 검증
- 서로 다른 테스트 이미지 3세트에서 breed 결과가 변화하는지 확인
- 매핑 테이블(`breed_mapping`) 한국어 변환 확인
### 실패 시 점검
- `CAT_API_KEY` 유효성
- API rate limit/응답 스키마 변경

## Task P0-3: 조회수 캐시 배치 완성 (Phase 11)
### 작업
- `GET /api/pets/:id` 시 `Redis INCR pet:views:{id}`
- 1분 주기 flush job 구현:
  - 증가 키 스캔
  - Supabase `missing_pets.views` 일괄 업데이트
  - 반영 성공 키 삭제
### 검증
- 10회 상세 조회 후 Redis 카운트 증가 확인
- flush 후 DB 증가치 반영 확인
### 실패 시 점검
- 키 스캔 패턴
- 동시 flush 충돌(lock)

---

## P1 (다음) - API 완성도

## Task P1-1: Chat 목록 고도화
### 작업
- `server/src/services/chat.service.js`
  - `q` 검색(펫명/상대방명/마지막 메시지)
  - unreadCount 계산 추가
### 검증
- 읽지 않은 메시지 3건 생성 후 unreadCount=3
- read 처리 후 unreadCount=0
### 실패 시 점검
- `read_by` 배열 갱신 방식
- 집계 쿼리 성능

## Task P1-2: Pet 상세 `isLiked` 정확화
### 작업
- `server/src/controllers/pets.controller.js`
  - 로그인 사용자일 때 `pet_likes` 조회로 실값 주입
### 검증
- 좋아요 전/후 `isLiked` false->true 전환 확인

## Task P1-3: Tips 큐 처리 전략 명세 일치
### 작업
- 현재 폴링 워커 유지 여부 결정 후 문서 명시:
  - 유지 시: `implementation_specs`에 “BullMQ 대신 polling 채택 근거” 기록
  - 전환 시: 실제 BullMQ 소비 워커로 교체
### 검증
- 처리 실패 재시도/최종 실패 상태 일관성 확인

---

## P2 (문서/테스트) - 운영 준비

## Task P2-1: Swagger 전체 동기화
### 작업
- `03_server_swagger_requirement.md` 대상 전체 반영:
  - auth/users/pets/chats/tips/notifications/uploads/devices/comments
  - 요청/응답/에러 스키마 명시
### 검증
- `/docs`에서 인증 필요 API 5개 이상 Try it out 성공
- 유효성 실패 1건, 무효 토큰 1건 재현

## Task P2-2: 통합 테스트 최소 세트 작성
### 작업
- `server/tests`:
  - auth login smoke
  - pets CRUD smoke
  - chats send/read smoke
- `ai_server/tests`:
  - analyze 입력 검증
  - embed 저장 호출 mock
### 검증
- CI/로컬에서 테스트 명령 1회 통과

## Task P2-3: Nginx 실측 검증 리포트 작성
### 작업
- `nginx -t` 결과
- `/api/*`, `/ai/*`, `/ws/*` 프록시 캡처/로그 정리
### 검증
- 3개 경로 모두 200/101(WS) 확인

---

## 실행 순서 (권장)
1. P0-1 -> P0-2 -> P0-3
2. P1-1 -> P1-2 -> P1-3
3. P2-1 -> P2-2 -> P2-3

---

## 완료 기준 (Gate)
- AI 결과가 임시 해시가 아닌 실제 임베딩 기반
- 조회수 캐시 배치가 동작하고 누적 손실 없음
- Swagger가 구현 API와 1:1 동기화
- 최소 통합 테스트가 자동 실행 가능
- 문서(`implementation_specs`)와 실제 코드 동작 불일치 없음
