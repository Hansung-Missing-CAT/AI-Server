# Missing Pet Finder — 작업 명세서

> **이 문서는 단계별로 실행 가능한 작업 명세서입니다.**
> 각 Phase는 독립적으로 실행/검증이 가능하며, 이전 Phase가 완료되어야 다음으로 진행합니다.
> 기준 문서: `architecture_analysis_v3.md` (Supabase 통합 아키텍처)
> 기준 문서: `backend_requirement_doc.md` (프론트엔드 도출 백엔드 요구사항)

---

## 기술 스택 (확정)

```
메인 서버       : Node.js 20 LTS + Express
AI 서버         : Python 3.11+ + FastAPI
DB/Auth/Storage : Supabase (PostgreSQL + pgvector + Auth + Storage + Realtime)
캐시/큐         : Upstash Redis + BullMQ
API Gateway     : Nginx
품종 분류       : The Cat API
LLM 특징 증강   : Claude Sonnet (claude-sonnet-4-20250514)
임베딩 모델     : paraphrase-multilingual-mpnet-base-v2
실시간          : Socket.io + Supabase Realtime
푸시            : FCM
```

---

## 디렉터리 구조 (최종 목표)

```
missing-pet-finder/
├── .claude                          ← 이 명세서
├── .env.example
├── docker-compose.yml               ← 로컬 개발 환경
│
├── server/                          ← Express 메인 서버
│   ├── package.json
│   ├── src/
│   │   ├── app.js                   ← Express 앱 초기화
│   │   ├── server.js                ← HTTP + Socket.io 시작
│   │   ├── config/
│   │   │   ├── supabase.js          ← Supabase 클라이언트 (admin + user)
│   │   │   ├── redis.js             ← Upstash Redis 연결
│   │   │   └── bullmq.js            ← BullMQ 큐 정의
│   │   ├── routes/
│   │   │   ├── auth.routes.js
│   │   │   ├── users.routes.js
│   │   │   ├── pets.routes.js
│   │   │   ├── tips.routes.js
│   │   │   ├── chats.routes.js
│   │   │   ├── notifications.routes.js
│   │   │   └── uploads.routes.js
│   │   ├── controllers/
│   │   │   ├── auth.controller.js
│   │   │   ├── users.controller.js
│   │   │   ├── pets.controller.js
│   │   │   ├── tips.controller.js
│   │   │   ├── chats.controller.js
│   │   │   ├── notifications.controller.js
│   │   │   └── uploads.controller.js
│   │   ├── services/
│   │   │   ├── pet.service.js
│   │   │   ├── tip.service.js
│   │   │   ├── chat.service.js
│   │   │   ├── notification.service.js
│   │   │   └── storage.service.js
│   │   ├── queues/
│   │   │   ├── producers/
│   │   │   │   ├── ai.producer.js
│   │   │   │   ├── embedding.producer.js
│   │   │   │   └── push.producer.js
│   │   │   └── workers/
│   │   │       └── push.worker.js
│   │   ├── socket/
│   │   │   ├── socket.handler.js    ← Socket.io 이벤트
│   │   │   └── realtime.handler.js  ← Redis Pub/Sub → Supabase Realtime
│   │   ├── middlewares/
│   │   │   ├── auth.middleware.js
│   │   │   ├── validate.middleware.js
│   │   │   └── error.middleware.js
│   │   └── utils/
│   │       ├── response.js          ← 표준 응답 헬퍼
│   │       ├── errors.js            ← 커스텀 에러 클래스
│   │       └── pagination.js        ← 커서 기반 페이지네이션
│   └── tests/
│
├── ai_server/                       ← Python FastAPI AI 파이프라인
│   ├── pyproject.toml
│   ├── main.py
│   ├── config.py
│   ├── routers/
│   │   ├── analyze.py
│   │   └── embed.py
│   ├── services/
│   │   ├── breed_classifier.py
│   │   ├── feature_augmentor.py
│   │   ├── embedder.py
│   │   └── vector_search.py
│   ├── workers/
│   │   └── ai_worker.py
│   ├── models/
│   │   └── schemas.py
│   └── tests/
│
├── supabase/                        ← Supabase 마이그레이션/설정
│   ├── migrations/
│   │   ├── 001_extensions.sql
│   │   ├── 002_users.sql
│   │   ├── 003_missing_pets.sql
│   │   ├── 004_pet_embeddings.sql
│   │   ├── 005_tips.sql
│   │   ├── 006_chats.sql
│   │   ├── 007_notifications.sql
│   │   ├── 008_likes_comments.sql
│   │   ├── 009_breed_mapping.sql
│   │   ├── 010_rls_policies.sql
│   │   ├── 011_functions.sql        ← RPC 함수 (search_similar_pets 등)
│   │   └── 012_triggers.sql
│   ├── seed.sql                     ← 초기 데이터 (breed_mapping, districts)
│   └── storage-policies.sql         ← Storage 버킷 + 접근 정책
│
└── nginx/
    └── nginx.conf
```

---

# Phase 0: 프로젝트 초기 설정

## Task 0-1: 프로젝트 루트 구조 생성

**작업 내용:**
- `missing-pet-finder/` 루트 디렉터리 생성
- `server/`, `ai_server/`, `supabase/`, `nginx/` 하위 디렉터리 생성
- `.env.example` 작성 (모든 환경 변수 키 + 설명 주석)
- `.gitignore` 작성

**`.env.example` 포함 항목:**
```
# Express
NODE_ENV=development
PORT=3000

# Supabase
SUPABASE_URL=https://xxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# Upstash Redis
UPSTASH_REDIS_URL=rediss://default:xxxxxx@xxxx.upstash.io:6379

# FCM
FCM_SERVER_KEY=

# Python AI Server
AI_SERVER_URL=http://localhost:8000
ANTHROPIC_API_KEY=sk-ant-...
CAT_API_KEY=live_...
```

**완료 기준:**
- [ ] 디렉터리 구조가 명세서와 일치
- [ ] `.env.example`에 모든 환경 변수 기재
- [ ] `.gitignore`에 `node_modules/`, `.env`, `__pycache__/`, `*.pyc` 포함

---

## Task 0-2: Express 서버 초기화

**작업 내용:**
- `server/package.json` 생성 (npm init)
- 의존성 설치:
  ```
  express cors helmet morgan dotenv
  @supabase/supabase-js ioredis bullmq
  socket.io express-validator
  ```
- devDependencies: `nodemon`
- `server/src/app.js`: Express 앱 기본 설정 (cors, helmet, morgan, json 파싱, 에러 핸들러)
- `server/src/server.js`: HTTP 서버 + Socket.io 바인딩 + 포트 리스닝
- `npm run dev` 스크립트: `nodemon src/server.js`

**완료 기준:**
- [ ] `cd server && npm run dev` 실행 시 `http://localhost:3000` 에서 응답
- [ ] `GET /health` → `{ "status": "ok", "timestamp": "..." }`

---

## Task 0-3: Python FastAPI 서버 초기화

**작업 내용:**
- `ai_server/pyproject.toml` 또는 `requirements.txt` 작성
- 의존성:
  ```
  fastapi uvicorn[standard] anthropic httpx
  supabase sentence-transformers redis Pillow
  bullmq pydantic
  ```
- `ai_server/main.py`: FastAPI 앱 기본 설정 + CORS
- `ai_server/config.py`: 환경 변수 로딩 + Supabase/Redis 클라이언트 초기화

**완료 기준:**
- [ ] `uvicorn main:app --port 8000` 실행 시 응답
- [ ] `GET /health` → `{ "status": "ok" }`

---

## Task 0-4: Supabase 프로젝트 연결 + 기본 설정

**작업 내용:**
- `server/src/config/supabase.js` 작성
  - `supabaseAdmin` (service_role 키 — RLS 우회, 서버 전용)
  - `createUserClient(accessToken)` (사용자 권한 클라이언트)
- `ai_server/config.py`에 Supabase 클라이언트 추가
- 연결 테스트: 간단한 SELECT 쿼리 실행 확인

**완료 기준:**
- [ ] Express에서 `supabaseAdmin.from('any_table').select('*').limit(1)` 에러 없이 실행 (빈 결과 OK)
- [ ] Python에서 `supabase.table('any_table').select('*').limit(1).execute()` 실행 확인

---

## Task 0-5: Upstash Redis + BullMQ 연결

**작업 내용:**
- `server/src/config/redis.js`: Upstash Redis 연결 (TLS)
- `server/src/config/bullmq.js`: BullMQ 큐 3개 정의
  - `ai-analysis` (AI 분석 작업)
  - `embedding-index` (임베딩 사전 저장)
  - `push-notifications` (FCM 푸시 발송)
- 연결 테스트: Redis PING + BullMQ 큐 발행/소비 라운드트립

**완료 기준:**
- [ ] Redis PING → PONG 응답
- [ ] BullMQ 테스트 작업 발행 → Worker에서 수신 확인

---

# Phase 1: Supabase 스키마 마이그레이션

## Task 1-1: 확장 기능 활성화

**파일:** `supabase/migrations/001_extensions.sql`

```sql
CREATE EXTENSION IF NOT EXISTS vector;       -- pgvector
CREATE EXTENSION IF NOT EXISTS pg_trgm;      -- 한국어 LIKE 검색 성능
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  -- UUID 생성 (fallback)
```

**완료 기준:**
- [ ] Supabase SQL Editor에서 실행 성공
- [ ] `SELECT * FROM pg_extension WHERE extname IN ('vector', 'pg_trgm')` → 2행 반환

---

## Task 1-2: users 테이블

**파일:** `supabase/migrations/002_users.sql`

**작업 내용:**
- `public.users` 테이블 생성 (`auth.users(id)` FK)
- 컬럼: id, name, phone, avatar_url, is_online, last_seen_at, agree_marketing, created_at
- `handle_new_user()` 트리거 함수: `auth.users` INSERT 시 `public.users` 자동 생성
- `on_auth_user_created` 트리거

**완료 기준:**
- [ ] Supabase Auth로 테스트 사용자 생성 시 `public.users`에 자동 삽입 확인

---

## Task 1-3: missing_pets 테이블

**파일:** `supabase/migrations/003_missing_pets.sql`

**작업 내용:**
- `public.missing_pets` 테이블 생성
- 컬럼: id(UUID), name, breed, age, gender('남'|'여'), color, location, district, detail_address, last_seen(DATE), lost_time, reward, photo, photos(TEXT[]), description, status('실종'|'찾음'), reporter_id(FK users), views, likes_count, comments_count, latitude, longitude, embedding_status('pending'|'done'|'failed'), created_at, updated_at
- 인덱스: district, status, created_at DESC, latitude/longitude, breed, name(GIN trgm), breed(GIN trgm)
- `updated_at` 자동 갱신 트리거

**완료 기준:**
- [ ] INSERT + SELECT + UPDATE 동작 확인
- [ ] `updated_at` 트리거 동작 확인 (UPDATE 시 자동 갱신)

---

## Task 1-4: pet_embeddings 테이블 (pgvector)

**파일:** `supabase/migrations/004_pet_embeddings.sql`

**작업 내용:**
- `public.pet_embeddings` 테이블: id, pet_id(FK CASCADE), embedding(VECTOR(768)), feature_text, created_at
- HNSW 인덱스: `vector_cosine_ops`, m=16, ef_construction=64

**완료 기준:**
- [ ] 768차원 벡터 INSERT 성공
- [ ] `embedding <=> '[0.1, 0.2, ...]'::vector` 코사인 거리 쿼리 동작 확인

---

## Task 1-5: tips 테이블

**파일:** `supabase/migrations/005_tips.sql`

**작업 내용:**
- `public.tips` 테이블: id, user_id(FK), status('processing'|'done'|'failed'), image_urls(TEXT[]), results(JSONB), progress(INTEGER 0~100), error_msg, created_at, updated_at
- 인덱스: user_id + created_at DESC

**완료 기준:**
- [ ] INSERT (status=processing) → UPDATE (status=done, results=JSONB) 흐름 확인

---

## Task 1-6: chats + chat_messages 테이블

**파일:** `supabase/migrations/006_chats.sql`

**작업 내용:**
- `public.chats`: id, pet_id(FK), participant_ids(UUID[]), last_message, last_message_at, created_at
- `public.chat_messages`: id, chat_id(FK CASCADE), sender_id(FK users), type('text'|'image'|'location'|'tipCard'), message, image_url, latitude, longitude, payload(JSONB), read_by(UUID[]), created_at
- 인덱스: chat_messages(chat_id, created_at DESC), chat_messages(sender_id)

**완료 기준:**
- [ ] 채팅방 생성 → 메시지 INSERT → chat.last_message 업데이트 흐름 확인

---

## Task 1-7: notifications 테이블

**파일:** `supabase/migrations/007_notifications.sql`

**작업 내용:**
- `public.notifications`: id, user_id(FK), type('comment'|'like'|'tip'|'found'|'nearby_report'), message, pet_id(FK nullable), read(BOOLEAN), created_at
- 인덱스: user_id + created_at DESC, user_id + read (미읽음 필터)

**완료 기준:**
- [ ] INSERT + 미읽음 카운트 `SELECT count(*) WHERE read = FALSE AND user_id = ?` 동작 확인

---

## Task 1-8: likes + comments 테이블

**파일:** `supabase/migrations/008_likes_comments.sql`

**작업 내용:**
- `public.pet_likes`: id, pet_id(FK CASCADE), user_id(FK), created_at + UNIQUE(pet_id, user_id)
- `public.pet_comments`: id, pet_id(FK CASCADE), user_id(FK), content(TEXT NOT NULL), created_at
- likes 카운트 자동 동기화 트리거:
  - `pet_likes` INSERT → `missing_pets.likes_count + 1`
  - `pet_likes` DELETE → `missing_pets.likes_count - 1`
- comments 카운트 동기화 트리거도 동일

**완료 기준:**
- [ ] 좋아요 INSERT → `missing_pets.likes_count` 자동 증가 확인
- [ ] 좋아요 DELETE → `missing_pets.likes_count` 자동 감소 확인
- [ ] 동일 사용자 중복 좋아요 → UNIQUE 위반 에러 확인

---

## Task 1-9: breed_mapping + 시드 데이터

**파일:** `supabase/migrations/009_breed_mapping.sql`, `supabase/seed.sql`

**작업 내용:**
- `public.breed_mapping`: cat_api_name(PK), kr_name, created_at
- `supabase/seed.sql`에 주요 견종/묘종 매핑 데이터 20~30건 INSERT
- (선택) `public.districts` 테이블 또는 시드 데이터로 서울 9개 구 INSERT

**완료 기준:**
- [ ] `SELECT * FROM breed_mapping` → 매핑 데이터 존재 확인

---

## Task 1-10: RLS 정책

**파일:** `supabase/migrations/010_rls_policies.sql`

**작업 내용:**
- 모든 테이블에 RLS 활성화
- 정책 규칙:
  - `missing_pets`: 누구나 SELECT, 로그인 사용자만 INSERT, 작성자만 UPDATE/DELETE
  - `chats`: participant_ids에 포함된 사용자만 ALL
  - `chat_messages`: 해당 chat의 참여자만 ALL
  - `notifications`: 본인 것만 ALL
  - `pet_likes`: 로그인 사용자 INSERT/DELETE, 누구나 SELECT
  - `pet_comments`: 로그인 사용자 INSERT, 작성자만 DELETE, 누구나 SELECT

**완료 기준:**
- [ ] anon 키로 `missing_pets` SELECT → 성공
- [ ] anon 키로 `missing_pets` INSERT → 실패 (RLS 차단)
- [ ] 유저 A의 토큰으로 유저 B의 알림 SELECT → 빈 결과 (RLS 필터링)

---

## Task 1-11: RPC 함수 (search_similar_pets)

**파일:** `supabase/migrations/011_functions.sql`

**작업 내용:**
- `search_similar_pets(query_embedding, breed_filter, lat, lng, radius_m, match_count)` 함수 생성
- 반환: pet_id, pet_name, pet_breed, pet_location, pet_photo, similarity_score
- 내부 로직: 품종 필터(NULL이면 스킵) + 위치 필터(NULL이면 스킵) + pgvector 코사인 유사도 + LIMIT

**완료 기준:**
- [ ] 더미 임베딩 INSERT 후 `SELECT * FROM search_similar_pets(...)` 호출 시 결과 반환

---

## Task 1-12: Supabase Storage 버킷 + 정책

**파일:** `supabase/storage-policies.sql`

**작업 내용:**
- 버킷 생성:
  - `pet-photos` (공개 — 누구나 읽기, 로그인 사용자만 업로드)
  - `chat-attachments` (비공개 — 참여자만 읽기, 로그인 사용자만 업로드)
  - `avatars` (공개 — 누구나 읽기, 본인만 업로드)
- 파일 크기 제한: 10MB
- MIME 타입 제한: image/jpeg, image/png, image/webp

**완료 기준:**
- [ ] Supabase Dashboard에서 3개 버킷 확인
- [ ] 테스트 이미지 업로드/다운로드 성공

---

# Phase 2: Express 인증 + 사용자 API

## Task 2-1: 공통 미들웨어 + 유틸

**작업 내용:**
- `middlewares/auth.middleware.js`: `authenticate` (JWT 필수) + `optionalAuth` (비로그인 허용)
  - Supabase `auth.getUser(token)` 으로 검증
- `middlewares/validate.middleware.js`: express-validator 기반 검증 래퍼
- `middlewares/error.middleware.js`: 글로벌 에러 핸들러
  - 응답 포맷: `{ code: "XXX", message: "한국어 메시지", fields: {...} }`
- `utils/response.js`: `success(res, data, status)`, `error(res, code, message, status)`
- `utils/errors.js`: `AppError`, `NotFoundError`, `ForbiddenError`, `ValidationError` 클래스
- `utils/pagination.js`: 커서 기반 페이지네이션 헬퍼

**완료 기준:**
- [ ] 유효한 JWT → `req.user` 에 사용자 정보 세팅
- [ ] 만료/무효 JWT → `401 { code: "INVALID_TOKEN" }` 응답
- [ ] optionalAuth → 토큰 없어도 `req.user = null` 로 통과

---

## Task 2-2: Auth 라우터

**파일:** `routes/auth.routes.js`, `controllers/auth.controller.js`

**엔드포인트:**
1. `POST /api/auth/signup` — Supabase Auth `admin.createUser()` + `public.users` INSERT
   - 검증: email 형식, password 8자 이상, phone 형식, agreeTerms/agreePrivacy 필수
   - 중복 이메일 → 409
2. `POST /api/auth/login` — Supabase Auth `signInWithPassword()`
   - 반환: `{ accessToken, refreshToken, user: { id, email, name } }`
3. `POST /api/auth/login/google` — Supabase Auth `signInWithIdToken()` 또는 OAuth flow
4. `POST /api/auth/refresh` — Supabase Auth `refreshSession()`
5. `POST /api/auth/logout` — Supabase Auth `signOut()`
6. `POST /api/auth/password/forgot` — Supabase Auth `resetPasswordForEmail()`
7. `POST /api/auth/password/reset` — Supabase Auth `updateUser({ password })`

**완료 기준:**
- [ ] 회원가입 → `auth.users` + `public.users` 동시 생성 확인
- [ ] 로그인 → accessToken + refreshToken 반환
- [ ] 잘못된 비밀번호 → 401 응답
- [ ] 중복 이메일 회원가입 → 409 응답
- [ ] 리프레시 → 새 accessToken 반환

---

## Task 2-3: User 라우터

**파일:** `routes/users.routes.js`, `controllers/users.controller.js`

**엔드포인트:**
1. `GET /api/users/me` — `authenticate` 미들웨어 → `public.users` SELECT
2. `PATCH /api/users/me` — 프로필 수정 (name, phone, avatar_url)

**완료 기준:**
- [ ] 토큰 포함 `GET /api/users/me` → 프로필 반환
- [ ] 토큰 없이 → 401
- [ ] `PATCH /api/users/me` → 수정 후 반환

---

# Phase 3: 실종 반려동물 (Pets) CRUD

## Task 3-1: Pets 서비스 레이어

**파일:** `services/pet.service.js`

**메서드:**
- `listPets({ district, q, sort, status, cursor, limit })` — Supabase 쿼리 빌더
  - district: `"전체"` 이면 필터 없음, 그 외 정확 일치
  - q: name, breed, location 3개 필드 ILIKE `%q%` OR 조건
  - sort: `latest`(created_at DESC) | `likes`(likes_count DESC) | `comments`(comments_count DESC)
  - status: `"실종"` | `"찾음"` | 둘 다(기본)
  - cursor: created_at 기반 커서 페이지네이션
- `getPetById(id)` — 풀필드 + reporter 정보 JOIN
- `createPet(data, userId)` — INSERT + embedding_status='pending'
- `updatePet(id, data, userId)` — 작성자 검증 후 UPDATE
- `deletePet(id, userId)` — 작성자 검증 후 DELETE
- `incrementViews(petId)` — Redis INCR → 배치 Supabase 반영

**완료 기준:**
- [ ] 모든 메서드 단위 테스트 (mock Supabase 응답)

---

## Task 3-2: Pets 라우터 + 컨트롤러

**파일:** `routes/pets.routes.js`, `controllers/pets.controller.js`

**엔드포인트:**
1. `GET /api/pets` — `optionalAuth` + `listPets()` (비로그인 접근 허용)
   - 쿼리: `?district=마포구&q=초코&sort=latest&status=실종&cursor=xxx&limit=20`
   - 응답: `{ data: [...], nextCursor: "...", hasMore: true }`
2. `GET /api/pets/:id` — `optionalAuth` + `getPetById()` + 조회수 증가
   - 응답에 `isLiked: boolean` 포함 (로그인 사용자 시 like 여부 확인)
3. `POST /api/pets` — `authenticate` + 검증 + `createPet()`
   - 검증: photoUrls 5장 이상, name/breed 필수, lostDate 미래날짜 금지
   - 부수효과: `embedding-index` 큐 발행 + `push-notifications` 큐 발행 (반경 2km)
4. `PATCH /api/pets/:id` — `authenticate` + `updatePet()`
5. `DELETE /api/pets/:id` — `authenticate` + `deletePet()`

**완료 기준:**
- [ ] 비로그인 `GET /api/pets` → 목록 반환
- [ ] 로그인 `POST /api/pets` → 게시글 생성 + 큐 발행 확인
- [ ] 비작성자 `PATCH /api/pets/:id` → 403

---

## Task 3-3: 좋아요 API

**엔드포인트:**
1. `POST /api/pets/:id/like` — `authenticate` → `pet_likes` INSERT + likes_count 트리거
2. `DELETE /api/pets/:id/like` — `authenticate` → `pet_likes` DELETE

**완료 기준:**
- [ ] 좋아요 → likes_count 증가
- [ ] 좋아요 취소 → likes_count 감소
- [ ] 중복 좋아요 → 409 또는 idempotent 처리

---

## Task 3-4: 댓글 API

**엔드포인트:**
1. `GET /api/pets/:id/comments` — 커서 페이지네이션
2. `POST /api/pets/:id/comments` — `authenticate` → INSERT + comments_count 트리거
3. `DELETE /api/comments/:commentId` — `authenticate` → 작성자만

**완료 기준:**
- [ ] 댓글 작성 → comments_count 증가
- [ ] 비작성자 삭제 → 403

---

# Phase 4: Supabase Storage (이미지 업로드)

## Task 4-1: Upload 라우터

**파일:** `routes/uploads.routes.js`, `controllers/uploads.controller.js`, `services/storage.service.js`

**엔드포인트:**
1. `POST /api/uploads/presign` — `authenticate`
   - body: `{ bucket, fileName, contentType }`
   - Supabase Storage `createSignedUploadUrl()` 호출
   - 응답: `{ uploadUrl, fileUrl, expiresIn }`

**완료 기준:**
- [ ] Presigned URL 발급 → curl로 해당 URL에 PUT 이미지 업로드 성공
- [ ] 업로드된 이미지 공개 URL로 접근 가능

---

# Phase 5: 채팅 시스템

## Task 5-1: Chat 서비스 레이어

**파일:** `services/chat.service.js`

**메서드:**
- `getChatList(userId, { q, cursor, limit })` — 내 채팅방 목록
  - 검색: petName, otherUserName, lastMessage 부분일치
  - 정렬: last_message_at DESC
  - 각 채팅방에 unreadCount 계산 (read_by에 내 ID 없는 메시지 수)
  - 상대방 정보 조인 (otherUserName, otherUserAvatar, isOnline)
- `getChatById(chatId, userId)` — 참여자 검증 + 메타 반환
- `getChatMessages(chatId, userId, { cursor, limit })` — 메시지 페이지네이션
- `createOrGetChat(petId, userId, otherUserId)` — idempotent 생성
- `sendMessage(chatId, senderId, { type, message, imageUrl, latitude, longitude, payload })` — INSERT + chat.last_message 업데이트
- `markAsRead(chatId, userId)` — 미읽은 메시지의 read_by에 userId 추가
- `leaveChat(chatId, userId)` — participant_ids에서 userId 제거
- `reportChat(chatId, userId, reason)` — 신고 레코드 생성

**완료 기준:**
- [ ] 채팅방 생성 → 동일 조건 재호출 시 기존 채팅방 반환 (idempotent)
- [ ] 메시지 전송 → chat.last_message 자동 업데이트
- [ ] 읽음 처리 → unreadCount 0 확인

---

## Task 5-2: Chat 라우터 + 컨트롤러

**엔드포인트:**
1. `GET /api/chats` — 채팅 목록
2. `GET /api/chats/:chatId` — 채팅방 메타
3. `GET /api/chats/:chatId/messages` — 메시지 목록
4. `POST /api/chats/:chatId/messages` — 메시지 전송
5. `POST /api/chats` — 채팅방 생성/조회
6. `POST /api/chats/:chatId/read` — 읽음 처리
7. `POST /api/chats/:chatId/leave` — 나가기
8. `POST /api/chats/:chatId/report` — 신고

**모든 엔드포인트:** `authenticate` 필수

**완료 기준:**
- [ ] 8개 엔드포인트 전부 정상 동작
- [ ] 비참여자 접근 → 403

---

## Task 5-3: Socket.io 실시간 이벤트

**파일:** `socket/socket.handler.js`

**작업 내용:**
- Socket.io 연결 시 JWT 검증 (handshake.auth.token)
- 사용자별 소켓 매핑 (userId → socketId Map)
- 이벤트 발신:
  - `message.new`: 메시지 전송 시 상대방 소켓에 전달
  - `message.read`: 읽음 처리 시 상대방에 알림
  - `chat.updated`: 채팅 목록 갱신용
  - `presence.update`: 접속/이탈 시 온라인 상태 브로드캐스트
- `POST /api/chats/:chatId/messages` 컨트롤러에서 Socket.io 이벤트 발행 연동

**완료 기준:**
- [ ] 유저 A가 메시지 전송 → 유저 B의 소켓에 `message.new` 이벤트 수신
- [ ] 유저 A 접속 → 유저 B에 `presence.update { isOnline: true }` 수신
- [ ] 유저 A 이탈 → 유저 B에 `presence.update { isOnline: false }` 수신

---

# Phase 6: 알림 시스템

## Task 6-1: Notification 서비스 + 라우터

**파일:** `services/notification.service.js`, `routes/notifications.routes.js`, `controllers/notifications.controller.js`

**엔드포인트:**
1. `GET /api/notifications` — `?unreadOnly=true&cursor=&limit=20`
2. `GET /api/notifications/unread-count` — `{ count: N }`
3. `POST /api/notifications/:id/read` — 단건 읽음
4. `POST /api/notifications/read-all` — 전체 읽음

**알림 생성 헬퍼:**
- `createNotification(userId, type, message, petId)` — INSERT + Supabase Realtime broadcast

**완료 기준:**
- [ ] 알림 생성 → 목록 조회 시 노출
- [ ] 읽음 처리 → unread-count 감소
- [ ] read-all → 모든 미읽음 → 읽음 전환

---

## Task 6-2: 알림 트리거 연동

**작업 내용:**
- `pet.service.js` → 게시글 등록 시 `nearby_report` 알림 생성 (BullMQ push 큐)
- `chat.service.js` → 제보 채팅 시작 시 `tip` 알림 생성
- `pet_likes` 트리거 → N개 단위 도달 시 `like` 알림 생성
- `pet_comments` INSERT 시 `comment` 알림 생성

**완료 기준:**
- [ ] 제보 전송 → 게시글 작성자에게 `tip` 알림 생성 확인
- [ ] 댓글 작성 → 게시글 작성자에게 `comment` 알림 생성 확인
- [ ] 좋아요 N개 도달 → `like` 알림 생성 확인

---

## Task 6-3: Supabase Realtime + Redis Pub/Sub 연동

**파일:** `socket/realtime.handler.js`

**작업 내용:**
- Redis Pub/Sub 구독: `tip:progress`, `tip:done` 채널
- 수신 시 Supabase Realtime `channel.send()` 으로 해당 사용자에게 브로드캐스트
- 알림 INSERT 시 Supabase Realtime Postgres Changes 활용 (클라이언트에서 직접 구독)

**완료 기준:**
- [ ] Python Worker가 Redis Pub/Sub 발행 → Express에서 수신 → 클라이언트에 전달 확인

---

# Phase 7: Python AI 파이프라인

## Task 7-1: The Cat API 품종 분류 (Stage 1)

**파일:** `ai_server/services/breed_classifier.py`

**작업 내용:**
- 이미지 URL 다운로드 → The Cat API 전송 → 품종 레이블 + 신뢰도 반환
- 최대 2장만 분류 (비용 절감)
- 여러 장 중 최고 신뢰도 기준으로 품종 결정
- `breed_mapping` 테이블에서 한국어 이름 조회

**완료 기준:**
- [ ] 테스트 이미지 → 품종 레이블 반환 확인
- [ ] 신뢰도 값 반환 확인

---

## Task 7-2: Claude Sonnet 특징 문장 증강 (Stage 2-A)

**파일:** `ai_server/services/feature_augmentor.py`

**작업 내용:**
- Anthropic API 호출 (claude-sonnet-4-20250514)
- 멀티모달 입력: 이미지 최대 3장 (base64) + 품종 힌트 텍스트
- 시스템 프롬프트: 반려동물 특징 분석 전문가 역할
  - 추출 항목: 털 색상/패턴, 얼굴 특징, 체형, 특이 마킹, 꼬리/발 특징
- 출력: 한국어 특징 문장 (순수 텍스트, JSON 없음)

**완료 기준:**
- [ ] 테스트 이미지 → 한국어 특징 문장 생성 확인
- [ ] 문장 길이 100~500자 범위 확인

---

## Task 7-3: 임베딩 생성 (Stage 2-B)

**파일:** `ai_server/services/embedder.py`

**작업 내용:**
- `paraphrase-multilingual-mpnet-base-v2` 모델 로딩 (싱글턴)
- 특징 문장 → 768차원 벡터 변환
- `normalize_embeddings=True` 로 정규화

**완료 기준:**
- [ ] 한국어 문장 입력 → 768차원 float 리스트 반환
- [ ] 벡터 L2 norm ≈ 1.0 (정규화 확인)

---

## Task 7-4: Supabase pgvector 검색 (Stage 2-C)

**파일:** `ai_server/services/vector_search.py`

**작업 내용:**
- Supabase RPC `search_similar_pets()` 호출
- 파라미터: query_vector, breed_filter(NULL 가능), lat, lng, radius_m, match_count
- 결과 변환: `{ petId, similarity (0~100), pet: { name, breed, location, photo } }`
- `upsert_embedding()`: 신고 등록 시 임베딩 저장

**완료 기준:**
- [ ] 더미 데이터 기반 유사도 검색 → 상위 3건 반환
- [ ] 품종 필터 적용 시 해당 품종만 결과에 포함

---

## Task 7-5: 분석 라우터 통합 (전체 파이프라인)

**파일:** `ai_server/routers/analyze.py`

**작업 내용:**
- `POST /ai/analyze`: Stage 1 → Stage 2-A → Stage 2-B → Stage 2-C 순차 실행
  - 품종 신뢰도 ≥ 0.7 → breed 필터 적용
  - 품종 신뢰도 < 0.7 → 전체 후보 대상 검색
- `POST /ai/embed`: 단일 게시글 임베딩 생성 + Supabase 저장

**완료 기준:**
- [ ] `POST /ai/analyze` 호출 → 상위 3건 + 유사도 점수 반환
- [ ] `POST /ai/embed` 호출 → `pet_embeddings` 테이블에 벡터 저장 + `embedding_status = 'done'` 확인

---

## Task 7-6: BullMQ Worker (Python)

**파일:** `ai_server/workers/ai_worker.py`

**작업 내용:**
- BullMQ `ai-analysis` 큐 구독
- 작업 수신 → `POST /ai/analyze` 내부 로직 실행
- 진행률 업데이트: Redis Pub/Sub `tip:progress` 채널 발행
  - 10%: "데이터베이스 조회 중"
  - 35%: "특징점 추출 중"
  - 65%: "유사도 매칭 중"
  - 100%: "완료"
- 완료 시: Supabase `tips` 테이블 업데이트 + Redis Pub/Sub `tip:done` 발행
- 실패 시: `tips.status = 'failed'`, `tips.error_msg` 저장
- BullMQ `embedding-index` 큐 구독 (신고 등록 시 임베딩 생성)

**완료 기준:**
- [ ] Express에서 `ai-analysis` 큐 발행 → Python Worker 수신 → 처리 → `tips` 테이블 결과 저장
- [ ] Redis Pub/Sub `tip:progress` 메시지 발행 확인
- [ ] 실패 시 `tips.status = 'failed'` 확인
- [ ] `embedding-index` 큐 → 임베딩 생성 + 저장 확인

---

# Phase 8: Tips (제보) API 통합

## Task 8-1: Tips 서비스 + 라우터

**파일:** `services/tip.service.js`, `routes/tips.routes.js`, `controllers/tips.controller.js`

**엔드포인트:**
1. `POST /api/tips/analyze` — `authenticate`
   - body: `{ imageUrls: string[] }` (3~5장)
   - Supabase `tips` INSERT (status: processing)
   - BullMQ `ai-analysis` 큐 발행
   - 즉시 응답: `{ tipId, status: "processing" }`
2. `GET /api/tips/:tipId` — 폴링용
   - 응답: `{ tipId, status, progress, results }`
3. `POST /api/tips/:tipId/send` — 제보 전송
   - body: `{ petId }`
   - 해당 pet의 reporter와 채팅방 생성 (idempotent)
   - 제보 사진 + 유사도 정보를 첫 메시지로 자동 전송 (type: tipCard)
   - 게시글 작성자에게 `tip` 알림 생성
   - 응답: `{ chatId }`

**완료 기준:**
- [ ] 분석 요청 → 큐 발행 → Worker 처리 → 폴링으로 결과 확인
- [ ] 제보 전송 → 채팅방 생성 + 첫 메시지 + 알림 생성

---

# Phase 9: 푸시 알림 (FCM)

## Task 9-1: 디바이스 토큰 + FCM Worker

**엔드포인트:**
1. `POST /api/devices/register` — body: `{ token, platform }` → 디바이스 토큰 저장
2. `DELETE /api/devices/:tokenId` — 토큰 해제

**BullMQ Worker:** `server/src/queues/workers/push.worker.js`
- `push-notifications` 큐 구독
- FCM HTTP v1 API 호출로 푸시 발송
- 실패 토큰 자동 삭제 (InvalidRegistration)

**DB 추가:**
```sql
CREATE TABLE public.device_tokens (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    token      TEXT NOT NULL UNIQUE,
    platform   TEXT CHECK (platform IN ('android', 'ios', 'web')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**완료 기준:**
- [ ] 토큰 등록 → DB 저장 확인
- [ ] 푸시 큐 발행 → FCM 요청 발송 확인 (실제 FCM 또는 mock)
- [ ] 무효 토큰 자동 삭제 확인

---

# Phase 10: Nginx 게이트웨이 설정

## Task 10-1: Nginx 설정 파일 작성

**파일:** `nginx/nginx.conf`

**작업 내용:**
- upstream 정의: express_backend(:3000), fastapi_ai(:8000)
- Rate Limit Zone:
  - auth: 10req/min
  - api: 100req/min
  - ai: 20req/min
- 라우팅:
  - `/api/auth/*` → express (auth rate limit)
  - `/ai/*` → fastapi (ai rate limit, 120s timeout, 50M body)
  - `/api/*` → express (api rate limit)
  - `/ws/*` → express (WebSocket upgrade, 3600s timeout)
- SSL: Let's Encrypt 인증서 경로 (placeholder)
- 보안 헤더: X-Real-IP, X-Forwarded-For, X-Frame-Options

**완료 기준:**
- [ ] `nginx -t` 설정 문법 검증 통과
- [ ] `/api/auth/login` → Express 프록시 확인
- [ ] `/ai/analyze` → FastAPI 프록시 확인
- [ ] `/ws/` → WebSocket 업그레이드 확인

---

# Phase 11: 조회수 캐시 + 배치 처리

## Task 11-1: Redis 조회수 버퍼

**작업 내용:**
- `GET /api/pets/:id` 호출 시 Redis `INCR pet:views:{id}`
- 1분 간격 cron (setInterval 또는 node-cron):
  - Redis에서 변경된 조회수 키 전부 조회
  - Supabase `missing_pets.views` 일괄 UPDATE
  - Redis 키 삭제

**완료 기준:**
- [ ] 상세 조회 → Redis 조회수 INCR 확인
- [ ] 1분 후 Supabase views 컬럼 반영 확인

---

# Phase 12: Docker + 로컬 개발 환경

## Task 12-1: docker-compose.yml 작성

**작업 내용:**
- services:
  - `express`: Node.js Express 서버 (포트 3000)
  - `fastapi`: Python FastAPI 서버 (포트 8000)
  - `nginx`: Nginx 리버스 프록시 (포트 80/443)
- Supabase / Upstash Redis는 외부 클라우드 서비스이므로 docker-compose에 포함하지 않음
- 볼륨 마운트: 소스 코드 변경 시 자동 리로드
- 환경 변수: `.env` 파일 참조

**완료 기준:**
- [ ] `docker compose up` → 3개 서비스 정상 기동
- [ ] `curl http://localhost/api/health` → Express 응답
- [ ] `curl http://localhost/ai/health` → FastAPI 응답

---

# Phase 13: 통합 테스트 + 검증

## Task 13-1: E2E 시나리오 검증

**시나리오 1: 회원가입 → 로그인 → 게시글 등록**
```
1. POST /api/auth/signup → 200
2. POST /api/auth/login → accessToken 획득
3. POST /api/uploads/presign → uploadUrl 획득
4. PUT uploadUrl → 이미지 업로드
5. POST /api/pets (Authorization: Bearer token) → petId 획득
6. GET /api/pets → 목록에 방금 등록한 게시글 존재
7. GET /api/pets/:petId → 상세 조회 + views 증가
```

**시나리오 2: AI 제보 분석**
```
1. POST /api/uploads/presign (3장) → uploadUrl 3개
2. 이미지 업로드
3. POST /api/tips/analyze → tipId + status: processing
4. GET /api/tips/:tipId (폴링) → status: done + results 3건
5. POST /api/tips/:tipId/send → chatId 반환
6. GET /api/chats → 새 채팅방 존재 확인
```

**시나리오 3: 채팅**
```
1. POST /api/chats → chatId
2. POST /api/chats/:chatId/messages (유저 A) → 메시지 전송
3. Socket.io 유저 B → message.new 이벤트 수신
4. POST /api/chats/:chatId/read (유저 B) → 읽음 처리
5. GET /api/chats/:chatId/messages → read_by에 유저 B 포함
```

**시나리오 4: 좋아요 + 알림**
```
1. POST /api/pets/:id/like → likes_count 증가
2. GET /api/notifications (게시글 작성자) → like 알림 존재
3. DELETE /api/pets/:id/like → likes_count 감소
```

**완료 기준:**
- [ ] 4개 시나리오 전부 수동 또는 자동 테스트 통과

---

# 전체 Phase 요약 (체크리스트)

| Phase | 내용 | Task 수 | 핵심 산출물 |
|---|---|---|---|
| **Phase 0** | 프로젝트 초기 설정 | 5 | Express + FastAPI + Supabase + Redis 연결 |
| **Phase 1** | Supabase 스키마 마이그레이션 | 12 | 전체 DB 테이블 + RLS + RPC 함수 + Storage |
| **Phase 2** | 인증 + 사용자 API | 3 | Auth 7개 엔드포인트 + User 2개 |
| **Phase 3** | 실종 반려동물 CRUD | 4 | Pets 5개 + 좋아요 2개 + 댓글 3개 엔드포인트 |
| **Phase 4** | 이미지 업로드 | 1 | Presigned URL 엔드포인트 |
| **Phase 5** | 채팅 시스템 | 3 | Chat 8개 엔드포인트 + Socket.io 실시간 |
| **Phase 6** | 알림 시스템 | 3 | Notification 4개 엔드포인트 + 트리거 + Realtime |
| **Phase 7** | Python AI 파이프라인 | 6 | Two-Stage Filtering 전체 + BullMQ Worker |
| **Phase 8** | 제보 API 통합 | 1 | Tips 3개 엔드포인트 + 큐 연동 |
| **Phase 9** | 푸시 알림 | 1 | FCM Worker + 디바이스 토큰 관리 |
| **Phase 10** | Nginx | 1 | 리버스 프록시 + Rate Limit + WebSocket |
| **Phase 11** | 조회수 캐시 | 1 | Redis 버퍼 + 배치 반영 |
| **Phase 12** | Docker | 1 | docker-compose 로컬 개발 환경 |
| **Phase 13** | 통합 테스트 | 1 | E2E 시나리오 4개 검증 |
| **합계** | | **43 Tasks** | |

---

# 실행 순서 요약

```
Phase 0  → 프로젝트 뼈대 + 외부 서비스 연결
Phase 1  → DB 스키마 전부 완성
Phase 2  → 인증 → 로그인해야 나머지 API 테스트 가능
Phase 3  → 핵심 도메인 (Pets CRUD)
Phase 4  → 이미지 업로드 (Pets 등록에 필요)
Phase 5  → 채팅 (제보 전송의 전제 조건)
Phase 6  → 알림 (트리거 연동은 기존 서비스에 hook 추가)
Phase 7  → AI 파이프라인 (가장 복잡, 독립적으로 개발 가능)
Phase 8  → Tips API (Phase 5 + Phase 7 결합)
Phase 9  → 푸시 알림 (Phase 6 확장)
Phase 10 → Nginx (모든 서비스 앞에 배치)
Phase 11 → 캐시 최적화
Phase 12 → Docker 환경
Phase 13 → 전체 통합 검증
```

---

*Last updated: 2026-05-06*
*Based on: architecture_analysis_v3.md + backend_requirement_doc.md*
