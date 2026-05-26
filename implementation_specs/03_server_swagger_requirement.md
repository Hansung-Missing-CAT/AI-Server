# Server Swagger 테스트 필수 요구사항

## 1. 목표

- `server` API를 Swagger UI에서 직접 테스트 가능하도록 구성한다.
- 인증이 필요한 API는 Swagger의 Authorize 버튼으로 JWT를 주입해 테스트한다.

## 2. 구현 항목

### 2.1 라이브러리

- `swagger-ui-express`
- `swagger-jsdoc` 또는 정적 OpenAPI YAML/JSON

### 2.2 라우트

- Swagger UI 경로: `/docs`
- OpenAPI JSON 경로: `/docs/openapi.json`

### 2.3 보안 스키마

- `bearerAuth` (`type: http`, `scheme: bearer`, `bearerFormat: JWT`)
- 인증 필요 엔드포인트에 `security: [{ bearerAuth: [] }]` 적용

## 3. 문서화 대상

- `/api/auth/*`
- `/api/users/*`
- `/api/pets/*`
- `/api/chats/*`
- `/api/tips/*`
- `/api/notifications/*`
- `/api/uploads/*`

각 엔드포인트에 필수 포함:
- 요청 파라미터/바디 스키마
- 성공 응답 예시
- 실패 응답 예시(401/403/409/422/500 등)

## 4. 검증 절차

1. 서버 실행 후 `/docs` 접속
2. `Authorize`에 JWT 입력
3. 인증 필요 API 3개 이상 Try it out 성공
4. 유효성 실패 케이스(잘못된 body) 1개 이상 실행
5. 무효 토큰 케이스 401 응답 확인

## 5. 완료 기준

- `/docs`에서 모든 server API가 보이고 실행 가능
- OpenAPI 스키마와 실제 응답 구조가 일치
- 신규 API 추가/변경 시 스펙 동기화 규칙이 CI 또는 PR 체크리스트에 포함
