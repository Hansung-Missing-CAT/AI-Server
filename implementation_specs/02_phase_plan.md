# Phase별 구현 절차 + 검증 체크리스트

## Phase 0. 초기 설정

### 작업
- 디렉터리 구조 최종 정렬
- `.env.example` 최신화
- `server`/`ai_server` 기본 실행 보장

### 검증
- `npm run dev` 후 `GET /health` 200
- `uvicorn main:app --port 8000` 후 `GET /health` 200
- `.gitignore`에 민감/빌드 파일 누락 없음

### 실패 시 점검
- Node/Python 버전
- `.env` 로딩 경로
- 포트 충돌(`3000`, `8000`)

---

## Phase 1. Supabase 스키마

### 작업
- `001`~`012` 마이그레이션 적용
- `seed.sql`, `storage-policies.sql` 적용

### 검증
- 핵심 테이블 존재: `users`, `missing_pets`, `pet_embeddings`, `tips`, `chats`, `chat_messages`, `notifications`
- 트리거 동작: `updated_at`, likes/comments count
- RLS 동작: anon/authenticated 권한 분리

### 실패 시 점검
- SQL 실행 순서
- 함수/트리거 의존성 누락
- policy 중복/충돌

---

## Phase 2. Auth + Users API

### 작업
- 공통 미들웨어(auth/validate/error) 완성
- `/api/auth/*` 구현
- `/api/users/me` 조회/수정 구현
- Swagger 스펙 작성 및 Authorize 연동

### 검증
- 회원가입/로그인/토큰 리프레시 동작
- 무효 토큰 `401 INVALID_TOKEN`
- 중복 이메일 `409`
- Swagger에서 auth/users 엔드포인트 테스트 통과

### 실패 시 점검
- Supabase Auth admin/client 구분
- JWT 전달 방식(`Authorization: Bearer`)
- validator 에러 매핑

---

## Phase 3. Pets CRUD + Like + Comment

### 작업
- `pet.service` 구현(필터/정렬/페이지네이션)
- pets 라우트/컨트롤러 구현
- like/comment API 구현
- 큐 발행 연결(embedding/push)

### 검증
- 비로그인 목록 조회 가능
- 작성자만 수정/삭제 가능
- like/comment count 자동 반영
- Swagger에서 목록/상세/등록/수정/삭제/좋아요/댓글 테스트

### 실패 시 점검
- 커서 페이지네이션 기준 필드
- RLS 작성자 정책
- 트리거 카운트 동기화 누락

---

## Phase 4. Storage 업로드

### 작업
- `/api/uploads/presign` 구현
- bucket/MIME/크기 제한 정책 반영

### 검증
- presigned URL 발급
- 실제 업로드 성공
- 공개/비공개 버킷 접근 정책 검증

### 실패 시 점검
- Storage policy
- 파일 경로/버킷명 오타
- content-type 제한

---

## Phase 5. 채팅 시스템

### 작업
- `chat.service` 구현
- chat/message 라우트 구현
- 참여자 권한 검증

### 검증
- 채팅방 idempotent 생성
- 메시지 전송 시 `last_message` 갱신
- 읽음 처리 시 unreadCount 감소
- 비참여자 접근 403

### 실패 시 점검
- participant_ids 조건식
- read_by 업데이트 방식
- chat/message 정렬 인덱스

---

## Phase 6. 알림 시스템

### 작업
- notification 서비스/라우트 구현
- 읽음/전체읽음/미읽음 카운트 구현
- 이벤트 발생 지점 연동

### 검증
- 알림 생성/조회/읽음 반영
- unread-count 정확성
- Realtime 브로드캐스트 수신

### 실패 시 점검
- user_id 대상 매핑
- read 플래그 갱신 조건
- Realtime 채널 권한

---

## Phase 7. Python AI 파이프라인

### 작업
- breed classifier / feature augmentor / embedder / vector search 구현
- `/ai/analyze`, `/ai/embed` 통합

### 검증
- 분석 요청 시 상위 유사 결과 반환
- 임베딩 저장 및 status 업데이트
- 품종 confidence 분기 동작

### 실패 시 점검
- 외부 API 키(`CAT`, `ANTHROPIC`)
- 모델 로딩 메모리
- RPC 파라미터 타입

---

## Phase 8. Tips 통합

### 작업
- tips analyze/poll/send 구현
- 큐 발행 및 결과 반영

### 검증
- analyze 요청 후 processing -> done/failed
- send 시 채팅 생성 + tipCard 메시지

### 실패 시 점검
- tipId 권한 검증
- 큐 payload 스키마
- 폴링 상태 업데이트 누락

---

## Phase 9. FCM Push

### 작업
- device token 등록/해제
- push worker 구현

### 검증
- 토큰 저장/삭제
- 큐 수신 후 발송 호출
- invalid token 정리

### 실패 시 점검
- FCM 인증 방식(v1 권장)
- 큐 retry/backoff 설정
- 플랫폼별 payload 포맷

---

## Phase 10. Nginx Gateway

### 작업
- upstream/rate-limit/timeout/ws 설정

### 검증
- `nginx -t` 통과
- `/api/*`, `/ai/*`, `/ws/*` 프록시 정상

### 실패 시 점검
- upstream 주소
- websocket upgrade 헤더
- 타임아웃/rate-limit 충돌

---

## Phase 11. 조회수 캐시 배치

### 작업
- Redis INCR 버퍼링
- 주기 배치 flush 구현

### 검증
- 상세 조회 후 Redis 카운트 증가
- flush 주기 이후 DB 반영

### 실패 시 점검
- 키 스캔 전략
- 동시성 업데이트
- flush 실패 재시도

---

## 최종 통합 검증 (Release Gate)

### 기능 검증
- Auth, Users, Pets, Chats, Tips, Notifications, Uploads API 정상
- AI 분석 결과 및 유사도 검색 정상
- Queue/Worker 정상

### 운영 검증
- PM2로 `server`/`ai_server` 기동/종료
- Swagger UI에서 주요 API 수동 테스트 가능
- 환경변수 누락/오류 시 명시적 에러 응답

### 보안 검증
- RLS 우회 경로 없음
- 민감정보 로그 출력 금지
- `.env`, 키 파일 Git 추적 제외
