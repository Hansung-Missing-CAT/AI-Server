# 현재 구현 상태 평가서 (2026-05-12)

## 평가 범위
- 기준: `implementation_specs/02_phase_plan.md`, `03_server_swagger_requirement.md`
- 대상: `server/`, `ai_server/`, `supabase/migrations/`

## 총평
- 현재 상태는 **골격 단계는 통과**, 일부 핵심 API는 동작 코드가 반영됨.
- 다만 명세 기준으로는 **운영 품질 관점의 미완료 항목**이 다수 존재.
- 특히 `AI 정확성`, `Swagger 완전성`, `조회수 캐시 설계`, `테스트 자동화`가 부족함.

---

## Phase별 평가

## 0. 초기 설정
- 상태: 부분 완료
- 확인:
  - `server`, `ai_server`, `supabase`, `nginx` 구조 존재
  - `.env.example` 존재
- 미흡:
  - `.env.example`에 일부 운영 키 설명 부족(FCM v1 토큰 수급 방식, 만료 주기 주석 없음)

## 1. Supabase 스키마
- 상태: 대부분 완료
- 확인:
  - `001`~`012` 존재, 추가로 `013_chat_reports_device_tokens.sql` 반영됨
- 미흡:
  - `increment_pet_views` RPC 사용 코드가 있으나, 함수 존재 여부를 명세/마이그레이션 검증 문서에 명시하지 않음

## 2. Auth + Users API
- 상태: 구현됨
- 확인:
  - `/api/auth/*`, `/api/users/me` 동작 코드 존재
  - 검증/에러 포맷 적용
- 미흡:
  - Google 로그인은 `idToken` 직접 입력 방식만 구현되어 실제 모바일 OAuth 연계 검증 절차 미정

## 3. Pets/Like/Comment
- 상태: 구현됨(기본)
- 확인:
  - 목록/상세/등록/수정/삭제/좋아요/댓글 API 존재
- 미흡:
  - 상세 조회 `isLiked`가 실제 조회 로직 없이 `false` 고정
  - 조회수 증가가 RPC 의존이며 fallback 부재
  - 페이지네이션 커서가 일부 정렬 옵션(`likes/comments`)에서 엄밀하지 않음

## 4. Storage 업로드
- 상태: 구현됨(기본)
- 확인:
  - `/api/uploads/presign` 구현
- 미흡:
  - 버킷별 접근 제약(예: `avatars` 본인만)과 API 레벨 정책 정합 검증 부족

## 5. 채팅 시스템
- 상태: 구현됨(기본)
- 확인:
  - 8개 엔드포인트 존재
  - 소켓 이벤트 발행(`message.new`, `message.read`, `chat.updated`, `presence.update`)
- 미흡:
  - `getChatList`에 명세 요구 검색(`q`) 및 unreadCount 계산 없음
  - `markAsRead`가 메시지별 반복 UPDATE(대량시 비효율)

## 6. 알림 시스템
- 상태: 구현됨(기본)
- 확인:
  - 목록/카운트/읽음/전체읽음 구현
  - Redis Pub/Sub -> Socket 브리지 존재
- 미흡:
  - 좋아요 N개 단위 알림 등 이벤트 정책 구현 미완

## 7. AI 파이프라인
- 상태: 부분 구현(핵심 미달)
- 확인:
  - `/ai/analyze`, `/ai/embed` 동작
  - worker 폴링 동작 존재
- 치명 미흡:
  - `embedder`가 명세 모델(`paraphrase-multilingual-mpnet-base-v2`)이 아니라 해시 기반 임시 벡터
  - `breed_classifier`가 입력 이미지를 실제 Cat API 분류 엔드포인트에 전달하지 않음(랜덤 검색 방식)
  - 결과적으로 유사도 품질 신뢰 불가

## 8. Tips 통합
- 상태: 구현됨(기본)
- 확인:
  - analyze/poll/send 흐름 존재
- 미흡:
  - BullMQ 소비가 아닌 폴링 워커로 대체됨(명세와 상이)
  - 큐 기반 재시도/backoff/시도 횟수 제어 미구현

## 9. FCM Push
- 상태: 부분 구현
- 확인:
  - 디바이스 토큰 등록/삭제 API 존재
  - push worker 존재, v1 우선 + legacy fallback
- 미흡:
  - v1 `access token` 자동 갱신 로직 없음(현재 고정 토큰 주입 전제)

## 10. Nginx Gateway
- 상태: 파일 존재, 실제 검증 미확인
- 미흡:
  - `nginx -t`, 프록시/WS 업그레이드 실측 결과 문서화 없음

## 11. 조회수 캐시 배치
- 상태: 미완료
- 확인:
  - 명세는 Redis INCR + 배치 flush인데 현재 코드에는 배치 플러시 루프 없음

---

## Swagger 요구사항 대비
- 상태: 부분 충족
- 충족:
  - `/docs`, `/docs/openapi.json`, `bearerAuth` 존재
- 미흡:
  - 문서화 대상 전체 경로 미반영
  - 성공/실패 응답 스키마가 실제 구조와 충분히 동기화되지 않음

---

## 테스트/검증 관점 미흡 항목
- 자동 테스트 부재 (`server/tests`, `ai_server/tests` 실질 테스트 없음)
- 통합 E2E 시나리오 부재 (Auth -> Pets -> Tips -> Chats -> Notifications)
- 포트 바인딩 제한 환경 외 별도 실행 검증 기록 필요

---

## 결론
- 현재는 **개발 진행 가능한 베이스라인**으로는 충분함.
- 그러나 명세 완료 기준(특히 AI 품질/Swagger 완전성/운영 신뢰성)에는 미달.
- 즉시 보완 우선순위는 다음 4개:
  1. AI 실제 모델/분류 경로 정합화
  2. 조회수 캐시 배치(Phase 11) 완성
  3. Swagger 전체 API 동기화
  4. 테스트 자동화(최소 smoke + 핵심 API 통합)
