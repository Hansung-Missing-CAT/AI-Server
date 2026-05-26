# 실행 규칙

## 1. 기본 원칙

- Phase는 순서대로 진행한다.
- 한 Phase의 검증이 끝나기 전 다음 Phase로 넘어가지 않는다.
- 작업 단위는 `구현 -> 검증 -> 기록` 순서를 따른다.

## 2. 브랜치/커밋 기준

- 권장 브랜치: `feat/phase-x-topic`
- 커밋은 기능 단위로 쪼갠다.
- 커밋 메시지 예시:
  - `feat(server): implement auth login and refresh`
  - `feat(supabase): add rls policies for chats`
  - `test(server): add integration test for pets list`

## 3. 공통 검증 규칙

### 3.1 실행 상태 검증

- `server`: `GET /health` 200
- `ai_server`: `GET /health` 200
- PM2 실행 시 두 프로세스 모두 `online`

### 3.2 API 검증

- 성공/실패 케이스 모두 확인
- 에러 응답 포맷 통일: `{ code, message, fields? }`
- 인증 API는 만료 토큰/무효 토큰 케이스 포함

### 3.3 데이터 검증

- 테이블/인덱스/트리거/RLS 정책 존재 확인
- seed 데이터 적용 확인
- anon/authenticated 권한 케이스 확인

## 4. 테스트 계층

- 단위 테스트: service/util
- 통합 테스트: route + middleware + db 경계
- 수동 테스트: Swagger + curl

## 5. 실패 처리

- 실패 시 다음 기록 필수:
  - 실패 단계
  - 재현 명령
  - 에러 원문
  - 원인 및 수정 커밋
- 동일 이슈 재발 방지 테스트 추가

## 6. Swagger 필수 조건 (server)

- Swagger UI 제공 필수
- 신규/변경 API는 OpenAPI 문서 갱신 필수
- 각 엔드포인트 최소 예시:
  - 200 성공
  - 4xx/5xx 실패
- JWT 보호 엔드포인트는 Swagger Authorize로 테스트 가능해야 함
