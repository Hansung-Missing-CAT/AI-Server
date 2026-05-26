# Nginx 게이트웨이 실측 검증 리포트

## 기준
- 대상 설정: [nginx/nginx.conf](/Users/chaeminsoo/모바일%20캡스톤/backend-server/nginx/nginx.conf)
- 검증 목표:
  - `/api/*` -> `:3000`
  - `/ai/*` -> `:8000`
  - `/ws/*` -> `:3000` (WebSocket upgrade)

## 1) 현재 환경 점검 결과 (2026-05-13)

### 실행 명령
```bash
nginx -t -c /Users/chaeminsoo/모바일\ 캡스톤/backend-server/nginx/nginx.conf
```

### 결과
```text
zsh:1: command not found: nginx
```

### 판정
- 현재 실행 환경에는 `nginx` 바이너리가 없어 문법 검사(`nginx -t`)와 프록시 실측을 즉시 수행할 수 없음.

---

## 2) 설정 정적 검토 결과

`nginx.conf` 기준으로 다음 항목은 명세와 일치:
- `upstream express_backend` = `127.0.0.1:3000`
- `upstream fastapi_ai` = `127.0.0.1:8000`
- rate-limit zone
  - auth: `10r/m`
  - api: `100r/m`
  - ai: `20r/m`
- 경로 라우팅
  - `/api/auth/` -> express
  - `/api/` -> express
  - `/ai/` -> fastapi
  - `/ws/` -> express + upgrade 헤더
- `/ai/` 타임아웃/바디 크기
  - `proxy_read_timeout 120s`
  - `proxy_send_timeout 120s`
  - `client_max_body_size 50M`

유의사항:
- `listen 80`이므로 실제 실행 시 권한/포트 점유 충돌 가능.
- 로컬 검증은 임시로 `listen 8080`으로 바꿔 테스트 권장.

---

## 3) 실측 절차 (로컬/서버 공통)

1. nginx 설치 확인
```bash
nginx -v
```

2. 문법 검증
```bash
nginx -t -c /ABS_PATH/backend-server/nginx/nginx.conf
```

3. nginx 실행(테스트용)
```bash
nginx -c /ABS_PATH/backend-server/nginx/nginx.conf
```

4. API 프록시 확인
```bash
curl -i http://localhost/api/auth/login
curl -i http://localhost/api/pets
curl -i http://localhost/ai/analyze
```

5. WebSocket 업그레이드 확인(예: wscat)
```bash
wscat -c ws://localhost/ws
```

6. 중지
```bash
nginx -s stop
```

---

## 4) 증적 기록 템플릿

## 4.1 nginx -t
- 명령:
- 결과:
- 판정: PASS / FAIL

## 4.2 `/api/*` 프록시
- 요청:
- 응답 상태코드:
- 백엔드 로그 확인:
- 판정: PASS / FAIL

## 4.3 `/ai/*` 프록시
- 요청:
- 응답 상태코드:
- 백엔드 로그 확인:
- 판정: PASS / FAIL

## 4.4 `/ws/*` 업그레이드
- 클라이언트:
- 연결 결과(101 여부):
- 이벤트 송수신:
- 판정: PASS / FAIL

---

## 5) 최종 판정
- 현재 리포트 상태: **부분 완료 (환경 제약으로 실측 미완료)**
- 완료 조건:
  - `nginx -t` PASS
  - `/api/*`, `/ai/*` 프록시 200계열 확인
  - `/ws/*` 업그레이드 101 확인
