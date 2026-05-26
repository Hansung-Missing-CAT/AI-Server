# Missing Pet Finder — 백엔드 아키텍처 분석 v3

> **Supabase 도입 기반 최종 아키텍처 문서**
> 기반 자료: 아키텍처 다이어그램 + `backend_requirement_doc.md`
> 변경 이력: v2(MySQL + ChromaDB + S3) → v3(Supabase 통합)

---

## 0. 확정 기술 스택

| 레이어 | 기술 | v2 대비 변경 |
|---|---|---|
| **API Gateway** | Nginx 1.25+ | 유지 |
| **메인 서버** | Node.js + Express (Node 20 LTS) | 유지 |
| **AI 파이프라인 서버** | Python + FastAPI (Python 3.11+) | 유지 |
| **관계형 DB** | ~~MySQL~~ → **Supabase (PostgreSQL)** | ✅ 변경 |
| **벡터 DB** | ~~Chroma DB~~ → **Supabase pgvector** | ✅ 변경 |
| **인증 / 세션** | ~~직접 구현 JWT~~ → **Supabase Auth** | ✅ 변경 |
| **파일 스토리지** | ~~AWS S3~~ → **Supabase Storage** | ✅ 변경 |
| **실시간 (채팅/알림)** | Socket.io + **Supabase Realtime** 병행 | ✅ 변경 |
| **캐시** | Upstash Redis (서버리스) | ✅ 변경 (관리형) |
| **큐** | Upstash Redis + BullMQ | ✅ 변경 (관리형) |
| **품종 분류** | The Cat API | 유지 |
| **LLM 특징 증강** | Claude Sonnet (`claude-sonnet-4-20250514`) | 유지 |
| **임베딩** | `paraphrase-multilingual-mpnet-base-v2` | 유지 |
| **푸시 알림** | FCM (Android) + APNs (iOS) | 유지 |

> **Upstash Redis** 선택 이유: 서버리스 관리형 Redis로, 별도 서버 운영 없이 BullMQ와 완전 호환됩니다.
> Supabase와 마찬가지로 인프라 관리 부담을 최소화합니다.

---

## 1. 전체 시스템 아키텍처

```
┌──────────────────────────────────────────────────────────────────┐
│                          모바일 기기                               │
│                (React Native / 모바일 웹, 390px)                   │
└───────────────────────────┬──────────────────────────────────────┘
                            │ HTTPS / WSS
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Nginx (API Gateway)                          │
│   SSL 종료 │ Rate Limit │ 라우팅 │ WebSocket 업그레이드             │
│                                                                   │
│  /api/*  ──► Express :3000                                        │
│  /ai/*   ──► FastAPI  :8000                                        │
│  /ws/*   ──► Socket.io :3000                                      │
└──────────────┬────────────────────────────────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌─────────────┐   ┌─────────────────┐
│   Express   │   │  Python FastAPI  │
│  (Node 20)  │   │  AI 파이프라인   │
│             │   │                 │
│ - Auth 연동 │   │ - 품종 분류      │
│ - Pets CRUD │   │ - 특징 문장 증강 │
│ - Chat      │◄──►- 임베딩 생성    │
│ - Socket.io │   │ - 벡터 검색      │
└──────┬──────┘   └────────┬────────┘
       │                   │
       │     ┌─────────────┘
       │     │
       ▼     ▼
┌──────────────────────────────────────────────────────────────────┐
│                          Supabase                                  │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ PostgreSQL   │  │   pgvector   │  │   Supabase Auth      │   │
│  │              │  │              │  │                      │   │
│  │ - users      │  │ pet_         │  │ - 이메일/비밀번호     │   │
│  │ - pets       │  │ embeddings   │  │ - Google OAuth       │   │
│  │ - chats      │  │ (768-dim)    │  │ - JWT 발급/검증       │   │
│  │ - tips       │  │              │  │ - 세션 관리          │   │
│  │ - notifs     │  └──────────────┘  └──────────────────────┘   │
│  └──────────────┘                                                │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │   Storage    │  │   Realtime   │                             │
│  │              │  │              │                             │
│  │ - 반려동물    │  │ - 알림 실시간 │                             │
│  │   사진       │  │   브로드캐스트│                             │
│  │ - 채팅 첨부  │  │ - DB 변경    │                             │
│  │ - 프로필 사진 │  │   구독       │                             │
│  └──────────────┘  └──────────────┘                             │
└──────────────────────────────────────────────────────────────────┘

       ┌──────────────────────────┐
       │     Upstash Redis        │
       │  (서버리스 관리형)          │
       │                          │
       │  - BullMQ AI 분석 큐      │
       │  - BullMQ 임베딩 큐        │
       │  - BullMQ 푸시 알림 큐    │
       │  - 목록/상세 캐시          │
       │  - 조회수 버퍼 (INCR)     │
       └──────────────────────────┘
```

---

## 2. Supabase 구성 상세

### 2.1 Supabase가 대체하는 범위

```
┌─────────────────────────────────────────────────────┐
│                    Supabase                          │
│                                                      │
│  PostgreSQL ──── 모든 관계형 데이터 저장               │
│       │                                              │
│       └── pgvector ── 반려동물 임베딩 벡터 저장/검색   │
│                                                      │
│  Auth ──────────── 회원가입/로그인/Google OAuth        │
│       │             JWT accessToken / refreshToken   │
│       └── RLS ──── Row Level Security (데이터 접근제어)│
│                                                      │
│  Storage ──────── 이미지 파일 저장 (Presigned URL)    │
│                    버킷: pet-photos, chat-attachments │
│                                                      │
│  Realtime ─────── PostgreSQL CDC 기반 실시간 이벤트   │
│                    알림 브로드캐스트, DB 변경 구독      │
└─────────────────────────────────────────────────────┘
```

### 2.2 Supabase 클라이언트 설정 (Express)

```javascript
// config/supabase.js
const { createClient } = require('@supabase/supabase-js');

// 서버용 클라이언트 — service_role 키 사용 (RLS 우회, 서버 전용)
const supabaseAdmin = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY,  // ⚠️ 절대 클라이언트에 노출 금지
  {
    auth: { persistSession: false },
    db:   { schema: 'public' },
  }
);

// 사용자 권한 클라이언트 — anon 키 + 사용자 JWT
const createUserClient = (accessToken) =>
  createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_ANON_KEY,
    { global: { headers: { Authorization: `Bearer ${accessToken}` } } }
  );

module.exports = { supabaseAdmin, createUserClient };
```

---

## 3. Supabase Auth 연동

### 3.1 인증 흐름

```
[회원가입 / 로그인]

클라이언트                 Express                   Supabase Auth
    │                        │                            │
    │── POST /api/auth/login─►│                            │
    │                        │── signInWithPassword() ───►│
    │                        │◄── { accessToken,          │
    │                        │     refreshToken, user } ──│
    │◄── 토큰 반환 ───────────│                            │

[Google OAuth]

클라이언트                 Supabase Auth
    │                        │
    │── Google 로그인 버튼 ──►│── Google OAuth 처리
    │◄── accessToken ────────│── users 테이블 자동 생성
```

### 3.2 Express Auth 라우터

```javascript
// routes/auth.routes.js
const { supabaseAdmin } = require('../config/supabase');

// 회원가입
router.post('/signup', async (req, res) => {
  const { name, email, phone, password, agreeTerms, agreePrivacy, agreeMarketing } = req.body;

  // 1. Supabase Auth로 계정 생성
  const { data: authData, error: authError } = await supabaseAdmin.auth.admin.createUser({
    email,
    password,
    email_confirm: true,
    user_metadata: { name, phone, agreeMarketing },
  });
  if (authError) return res.status(400).json({ code: 'AUTH_ERROR', message: authError.message });

  // 2. public.users 테이블에 프로필 저장 (트리거로 자동 처리 권장)
  await supabaseAdmin.from('users').insert({
    id:               authData.user.id,  // Supabase Auth UID와 동일하게
    name,
    email,
    phone,
    agree_marketing:  agreeMarketing,
  });

  res.status(201).json({ message: '회원가입 완료' });
});

// 로그인
router.post('/login', async (req, res) => {
  const { email, password } = req.body;

  const { data, error } = await supabaseAdmin.auth.signInWithPassword({ email, password });
  if (error) return res.status(401).json({ code: 'INVALID_CREDENTIALS', message: '이메일 또는 비밀번호가 올바르지 않습니다.' });

  res.json({
    accessToken:  data.session.access_token,
    refreshToken: data.session.refresh_token,
    user: {
      id:    data.user.id,
      email: data.user.email,
      name:  data.user.user_metadata.name,
    },
  });
});

// 토큰 갱신
router.post('/refresh', async (req, res) => {
  const { refreshToken } = req.body;
  const { data, error } = await supabaseAdmin.auth.refreshSession({ refresh_token: refreshToken });
  if (error) return res.status(401).json({ code: 'INVALID_REFRESH_TOKEN' });

  res.json({ accessToken: data.session.access_token });
});
```

### 3.3 JWT 검증 미들웨어

```javascript
// middlewares/auth.middleware.js
const { supabaseAdmin } = require('../config/supabase');

const authenticate = async (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ code: 'NO_TOKEN' });

  // Supabase JWT 검증 (서명 + 만료 자동 확인)
  const { data: { user }, error } = await supabaseAdmin.auth.getUser(token);
  if (error || !user) return res.status(401).json({ code: 'INVALID_TOKEN' });

  req.user = user;   // user.id = Supabase Auth UID
  next();
};

// 비로그인 허용 (읽기 전용)
const optionalAuth = async (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (token) {
    const { data: { user } } = await supabaseAdmin.auth.getUser(token);
    req.user = user || null;
  }
  next();
};

module.exports = { authenticate, optionalAuth };
```

---

## 4. Supabase PostgreSQL 스키마

### 4.1 pgvector 확장 및 핵심 테이블

```sql
-- pgvector 확장 활성화 (Supabase 대시보드 또는 SQL Editor에서 실행)
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;   -- 한국어 LIKE 검색 성능 향상

-- ──────────────────────────────────────────────
-- users (Supabase Auth와 연동)
-- ──────────────────────────────────────────────
-- Supabase Auth가 auth.users를 관리하므로,
-- 앱 전용 프로필은 public.users에 별도 저장
CREATE TABLE public.users (
  id              UUID        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  name            TEXT        NOT NULL,
  phone           TEXT,
  avatar_url      TEXT,
  is_online       BOOLEAN     DEFAULT FALSE,
  last_seen_at    TIMESTAMPTZ,
  agree_marketing BOOLEAN     DEFAULT FALSE,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Auth 회원가입 시 public.users 자동 생성 트리거
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (id, name)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'name', '사용자')
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();


-- ──────────────────────────────────────────────
-- missing_pets
-- ──────────────────────────────────────────────
CREATE TABLE public.missing_pets (
  id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  name             TEXT        NOT NULL,
  breed            TEXT,                        -- Stage 1 필터링 키
  age              TEXT,
  gender           TEXT        CHECK (gender IN ('남', '여')),
  color            TEXT,
  location         TEXT        NOT NULL,
  district         TEXT        NOT NULL,        -- 구 단위 필터
  detail_address   TEXT,
  last_seen        DATE        NOT NULL,
  lost_time        TEXT,
  reward           INTEGER     DEFAULT 0,
  photo            TEXT,                        -- Supabase Storage URL
  photos           TEXT[]      DEFAULT '{}',
  description      TEXT,
  status           TEXT        DEFAULT '실종'   CHECK (status IN ('실종', '찾음')),
  reporter_id      UUID        NOT NULL REFERENCES public.users(id),
  views            INTEGER     DEFAULT 0,
  likes_count      INTEGER     DEFAULT 0,
  comments_count   INTEGER     DEFAULT 0,
  latitude         NUMERIC(10,7),
  longitude        NUMERIC(10,7),
  embedding_status TEXT        DEFAULT 'pending' CHECK (embedding_status IN ('pending','done','failed')),
  created_at       TIMESTAMPTZ DEFAULT NOW(),
  updated_at       TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_pets_district   ON public.missing_pets (district);
CREATE INDEX idx_pets_status     ON public.missing_pets (status);
CREATE INDEX idx_pets_created    ON public.missing_pets (created_at DESC);
CREATE INDEX idx_pets_location   ON public.missing_pets (latitude, longitude);
CREATE INDEX idx_pets_breed      ON public.missing_pets (breed);                -- Stage 1 필터
CREATE INDEX idx_pets_name_trgm  ON public.missing_pets USING GIN (name  gin_trgm_ops);
CREATE INDEX idx_pets_breed_trgm ON public.missing_pets USING GIN (breed gin_trgm_ops);

-- updated_at 자동 갱신 트리거
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER pets_updated_at
  BEFORE UPDATE ON public.missing_pets
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ──────────────────────────────────────────────
-- pet_embeddings (pgvector)
-- ──────────────────────────────────────────────
CREATE TABLE public.pet_embeddings (
  id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  pet_id       UUID        NOT NULL REFERENCES public.missing_pets(id) ON DELETE CASCADE,
  embedding    VECTOR(768),                     -- paraphrase-multilingual-mpnet 차원
  feature_text TEXT,                            -- Claude가 생성한 특징 문장 (디버깅용)
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- HNSW 인덱스 (고성능 근사 최근접 검색)
CREATE INDEX idx_pet_embeddings_hnsw
  ON public.pet_embeddings
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);


-- ──────────────────────────────────────────────
-- tips (AI 분석 작업)
-- ──────────────────────────────────────────────
CREATE TABLE public.tips (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID        NOT NULL REFERENCES public.users(id),
  status      TEXT        DEFAULT 'processing' CHECK (status IN ('processing','done','failed')),
  image_urls  TEXT[]      NOT NULL,
  results     JSONB,                            -- AI 분석 결과 상위 3건
  progress    INTEGER     DEFAULT 0,            -- 0~100
  error_msg   TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tips_user ON public.tips (user_id, created_at DESC);
CREATE TRIGGER tips_updated_at
  BEFORE UPDATE ON public.tips
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ──────────────────────────────────────────────
-- chats / chat_messages
-- ──────────────────────────────────────────────
CREATE TABLE public.chats (
  id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  pet_id           UUID        REFERENCES public.missing_pets(id),
  participant_ids  UUID[]      NOT NULL,        -- [userId1, userId2]
  last_message     TEXT,
  last_message_at  TIMESTAMPTZ,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE public.chat_messages (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  chat_id     UUID        NOT NULL REFERENCES public.chats(id) ON DELETE CASCADE,
  sender_id   UUID        NOT NULL REFERENCES public.users(id),
  type        TEXT        DEFAULT 'text' CHECK (type IN ('text','image','location','tipCard')),
  message     TEXT,
  image_url   TEXT,
  latitude    NUMERIC(10,7),
  longitude   NUMERIC(10,7),
  payload     JSONB,                            -- tipCard 등 확장 데이터
  read_by     UUID[]      DEFAULT '{}',         -- 읽은 사용자 ID 배열
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_messages_chat    ON public.chat_messages (chat_id, created_at DESC);
CREATE INDEX idx_messages_sender  ON public.chat_messages (sender_id);


-- ──────────────────────────────────────────────
-- notifications
-- ──────────────────────────────────────────────
CREATE TABLE public.notifications (
  id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID        NOT NULL REFERENCES public.users(id),
  type       TEXT        NOT NULL CHECK (type IN ('comment','like','tip','found','nearby_report')),
  message    TEXT        NOT NULL,
  pet_id     UUID        REFERENCES public.missing_pets(id),
  read       BOOLEAN     DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notifs_user ON public.notifications (user_id, created_at DESC);
CREATE INDEX idx_notifs_unread ON public.notifications (user_id, read) WHERE read = FALSE;


-- ──────────────────────────────────────────────
-- 품종 매핑 (The Cat API 영문 → 한국어)
-- ──────────────────────────────────────────────
CREATE TABLE public.breed_mapping (
  cat_api_name TEXT PRIMARY KEY,               -- "Pomeranian"
  kr_name      TEXT NOT NULL,                  -- "포메라니안"
  created_at   TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.2 Row Level Security (RLS) 설정

```sql
-- RLS 활성화
ALTER TABLE public.missing_pets  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chats         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

-- 실종 게시글: 누구나 읽기 가능, 작성자만 수정/삭제
CREATE POLICY "pets_read_public"  ON public.missing_pets FOR SELECT USING (TRUE);
CREATE POLICY "pets_insert_auth"  ON public.missing_pets FOR INSERT
  WITH CHECK (auth.uid() = reporter_id);
CREATE POLICY "pets_update_owner" ON public.missing_pets FOR UPDATE
  USING (auth.uid() = reporter_id);
CREATE POLICY "pets_delete_owner" ON public.missing_pets FOR DELETE
  USING (auth.uid() = reporter_id);

-- 채팅: 참여자만 접근
CREATE POLICY "chats_participant"  ON public.chats FOR ALL
  USING (auth.uid() = ANY(participant_ids));
CREATE POLICY "messages_participant" ON public.chat_messages FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM public.chats
      WHERE id = chat_id AND auth.uid() = ANY(participant_ids)
    )
  );

-- 알림: 본인 것만
CREATE POLICY "notifs_owner" ON public.notifications FOR ALL
  USING (auth.uid() = user_id);
```

### 4.3 Two-Stage Filtering SQL (pgvector)

pgvector가 PostgreSQL과 **같은 DB**에 있어 품종 필터 + 위치 필터 + 벡터 유사도 검색을 **단일 쿼리**로 처리할 수 있습니다.

```sql
-- Two-Stage Filtering 통합 쿼리
-- $1: 쿼리 벡터, $2: 품종명(없으면 NULL), $3/$4: 위경도(없으면 NULL), $5: 반경(m)
SELECT
    p.id,
    p.name,
    p.breed,
    p.location,
    p.photo,
    p.status,
    ROUND((1 - (pe.embedding <=> $1::VECTOR)) * 100) AS similarity_score
FROM public.missing_pets p
JOIN public.pet_embeddings pe ON p.id = pe.pet_id
WHERE
    p.status = '실종'
    -- Stage 1: 품종 필터 (신뢰도 ≥ 0.7일 때만 적용)
    AND ($2 IS NULL OR p.breed = $2)
    -- 위치 필터 (좌표가 있을 때만 적용)
    AND (
        $3 IS NULL OR $4 IS NULL
        OR (
            6371000 * ACOS(
                COS(RADIANS($3)) * COS(RADIANS(p.latitude))
                * COS(RADIANS(p.longitude) - RADIANS($4))
                + SIN(RADIANS($3)) * SIN(RADIANS(p.latitude))
            ) <= $5
        )
    )
ORDER BY similarity_score DESC
LIMIT 3;
```

---

## 5. Supabase Storage 연동

### 5.1 버킷 구성

```
Supabase Storage
├── pet-photos/           (공개 버킷)
│   └── {petId}/          ← 실종 신고 사진
│       ├── main.jpg
│       └── 1.jpg, 2.jpg ...
├── chat-attachments/     (비공개 버킷 — 참여자만 접근)
│   └── {chatId}/{messageId}.jpg
└── avatars/              (공개 버킷)
    └── {userId}.jpg
```

### 5.2 이미지 업로드 (Presigned URL 방식)

```javascript
// services/storage.service.js
const { supabaseAdmin } = require('../config/supabase');

/**
 * 클라이언트가 직접 Supabase Storage에 업로드할 수 있는
 * Presigned URL 생성 (서버 부하 없음)
 */
async function createPresignedUploadUrl(bucket, filePath) {
  const { data, error } = await supabaseAdmin.storage
    .from(bucket)
    .createSignedUploadUrl(filePath, { upsert: false });

  if (error) throw new Error(error.message);

  return {
    uploadUrl: data.signedUrl,    // 클라이언트가 PUT 요청을 보낼 URL
    fileUrl: `${process.env.SUPABASE_URL}/storage/v1/object/public/${bucket}/${filePath}`,
    expiresIn: 300,               // 5분
  };
}

/**
 * POST /api/uploads/presign
 */
router.post('/presign', authenticate, async (req, res) => {
  const { bucket = 'pet-photos', fileName, petId } = req.body;
  const filePath = `${petId}/${Date.now()}_${fileName}`;

  const result = await createPresignedUploadUrl(bucket, filePath);
  res.json(result);
});
```

---

## 6. Supabase Realtime 연동

### 6.1 Realtime 활용 범위

| 기능 | 방식 | 비고 |
|---|---|---|
| 알림 실시간 수신 | Postgres Changes 구독 | `notifications` 테이블 INSERT 감지 |
| 채팅 메시지 수신 | Postgres Changes 구독 | `chat_messages` INSERT 감지 |
| 온라인 상태 | Presence 채널 | 접속/이탈 브로드캐스트 |
| AI 분석 진행률 | Broadcast 채널 | Python Worker → 클라이언트 진행률 Push |

### 6.2 Express에서 Realtime 브로드캐스트 (AI 진행률)

```javascript
// socket/realtime.handler.js
// Python Worker가 Redis Pub/Sub으로 완료 신호를 보내면
// Express가 Supabase Realtime 채널로 브로드캐스트

const redisSubscriber = new IORedis(process.env.UPSTASH_REDIS_URL);
const { supabaseAdmin } = require('../config/supabase');

redisSubscriber.subscribe('tip:progress', 'tip:done');

redisSubscriber.on('message', async (channel, message) => {
  const data = JSON.parse(message);

  // Supabase Realtime Broadcast로 해당 사용자에게 전송
  await supabaseAdmin
    .channel(`tip:${data.userId}`)
    .send({
      type:    'broadcast',
      event:   channel === 'tip:done' ? 'tip.complete' : 'tip.progress',
      payload: data,
    });
});
```

### 6.3 클라이언트 Realtime 구독 예시 (React)

```javascript
// 클라이언트 측 구독 예시 (참고용)
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// AI 분석 진행률 수신
const tipChannel = supabase
  .channel(`tip:${userId}`)
  .on('broadcast', { event: 'tip.progress' }, ({ payload }) => {
    setProgress(payload.progress);
    setProgressMsg(payload.message);
  })
  .on('broadcast', { event: 'tip.complete' }, ({ payload }) => {
    setResults(payload.results);
  })
  .subscribe();

// 알림 실시간 수신
const notifChannel = supabase
  .channel('notifications')
  .on('postgres_changes', {
    event:  'INSERT',
    schema: 'public',
    table:  'notifications',
    filter: `user_id=eq.${userId}`,
  }, (payload) => {
    addNotification(payload.new);
  })
  .subscribe();
```

---

## 7. AI 파이프라인 (Python FastAPI) — Supabase 연동

### 7.1 Python에서 Supabase 연결

```python
# config.py
from supabase import create_client, Client
import os

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY"),  # 서버용 — RLS 우회
)
```

### 7.2 pgvector 검색 (Python → Supabase RPC)

Supabase에서 pgvector 쿼리는 **PostgreSQL Function(RPC)**으로 등록하여 Python에서 호출합니다.

```sql
-- Supabase SQL Editor에서 함수 등록
CREATE OR REPLACE FUNCTION search_similar_pets(
    query_embedding VECTOR(768),
    breed_filter    TEXT    DEFAULT NULL,
    lat             NUMERIC DEFAULT NULL,
    lng             NUMERIC DEFAULT NULL,
    radius_m        INTEGER DEFAULT 10000,
    match_count     INTEGER DEFAULT 3
)
RETURNS TABLE (
    pet_id           UUID,
    pet_name         TEXT,
    pet_breed        TEXT,
    pet_location     TEXT,
    pet_photo        TEXT,
    similarity_score INTEGER
)
LANGUAGE SQL STABLE AS $$
    SELECT
        p.id,
        p.name,
        p.breed,
        p.location,
        p.photo,
        ROUND((1 - (pe.embedding <=> query_embedding)) * 100)::INTEGER
    FROM public.missing_pets p
    JOIN public.pet_embeddings pe ON p.id = pe.pet_id
    WHERE
        p.status = '실종'
        AND (breed_filter IS NULL OR p.breed = breed_filter)
        AND (
            lat IS NULL OR lng IS NULL
            OR (
                6371000 * ACOS(
                    COS(RADIANS(lat)) * COS(RADIANS(p.latitude))
                    * COS(RADIANS(p.longitude) - RADIANS(lng))
                    + SIN(RADIANS(lat)) * SIN(RADIANS(p.latitude))
                ) <= radius_m
            )
        )
    ORDER BY pe.embedding <=> query_embedding
    LIMIT match_count;
$$;
```

```python
# services/vector_search.py
async def search_similar_pets(
    query_vector: list[float],
    breed_filter: str | None,
    lat: float | None = None,
    lng: float | None = None,
) -> list[dict]:
    """Supabase RPC로 pgvector 유사도 검색"""

    response = supabase.rpc(
        "search_similar_pets",
        {
            "query_embedding": query_vector,
            "breed_filter":    breed_filter,
            "lat":             lat,
            "lng":             lng,
            "radius_m":        10000,
            "match_count":     3,
        }
    ).execute()

    return [
        {
            "petId":      row["pet_id"],
            "similarity": row["similarity_score"],
            "pet": {
                "name":     row["pet_name"],
                "breed":    row["pet_breed"],
                "location": row["pet_location"],
                "photo":    row["pet_photo"],
            }
        }
        for row in response.data
    ]


async def upsert_embedding(pet_id: str, vector: list[float], feature_text: str):
    """실종 신고 등록 시 임베딩 저장 / 갱신"""
    supabase.table("pet_embeddings").upsert({
        "pet_id":       pet_id,
        "embedding":    vector,
        "feature_text": feature_text,
    }, on_conflict="pet_id").execute()

    # embedding_status 업데이트
    supabase.table("missing_pets").update(
        {"embedding_status": "done"}
    ).eq("id", pet_id).execute()
```

---

## 8. BullMQ + Upstash Redis 큐 설계

### 8.1 Upstash Redis 연결

```javascript
// config/redis.js  (Express)
const IORedis = require('ioredis');

// Upstash는 TLS 필수
const redis = new IORedis(process.env.UPSTASH_REDIS_URL, {
  tls: { rejectUnauthorized: false },
  maxRetriesPerRequest: null,       // BullMQ 필수
});

module.exports = redis;
```

```python
# config.py  (Python)
import redis.asyncio as aioredis
import ssl

redis_client = aioredis.from_url(
    os.getenv("UPSTASH_REDIS_URL"),
    ssl_cert_reqs=ssl.CERT_NONE,    # Upstash TLS
)
```

### 8.2 큐 흐름

```
[Express] POST /api/tips/analyze
    │
    │  1. Supabase에 tip 레코드 생성 (status: 'processing')
    │  2. Supabase Storage 업로드 URL 확인
    │  3. BullMQ ai-analysis 큐에 작업 발행
    │
    ▼
Upstash Redis (BullMQ 브로커)
    │
    ▼
[Python FastAPI Worker]
    │
    ├── The Cat API → 품종 분류
    ├── Claude Sonnet → 특징 문장 증강
    ├── sentence-transformers → 임베딩
    ├── Supabase RPC(search_similar_pets) → 유사도 검색
    ├── Supabase tips 테이블 → 결과 저장 (status: 'done')
    └── Redis Pub/Sub → Express에 완료 신호
    │
    ▼
[Express] Redis Pub/Sub 수신
    │
    └── Supabase Realtime Broadcast → 클라이언트에 tip.complete 이벤트
```

### 8.3 큐 목록

| 큐 이름 | 발행자 | 소비자 | 목적 |
|---|---|---|---|
| `ai-analysis` | Express | Python Worker | 제보 AI 파이프라인 실행 |
| `embedding-index` | Express | Python Worker | 신고 등록 시 임베딩 사전 저장 |
| `push-notifications` | Express | Node.js Worker | FCM/APNs 푸시 발송 |

---

## 9. 환경 변수 구성

```bash
# ── Express (.env) ──────────────────────────────────
NODE_ENV=production
PORT=3000

# Supabase
SUPABASE_URL=https://xxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...           # 클라이언트용 (공개 가능)
SUPABASE_SERVICE_ROLE_KEY=eyJ...   # 서버 전용 (절대 노출 금지)

# Upstash Redis
UPSTASH_REDIS_URL=rediss://default:xxxxxx@xxxx.upstash.io:6379

# FCM
FCM_SERVER_KEY=AAAA...

# Python AI Server (내부 통신)
AI_SERVER_URL=http://localhost:8000
```

```bash
# ── Python FastAPI (.env) ────────────────────────────
PYTHON_ENV=production
PORT=8000

# Supabase
SUPABASE_URL=https://xxxxxxxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...   # 서버 전용

# Upstash Redis
UPSTASH_REDIS_URL=rediss://default:xxxxxx@xxxx.upstash.io:6379

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# The Cat API
CAT_API_KEY=live_...
```

---

## 10. 데이터 흐름 전체 시퀀스

### 10.1 제보 분석 시퀀스

```
클라이언트    Nginx   Express  Upstash(BullMQ)  Python Worker  Supabase
    │           │        │            │                │            │
    │─사진업로드─►│        │            │                │            │
    │           │─라우팅─►│            │                │            │
    │           │        │─Storage URL 생성────────────────────────►│
    │◄─Upload URL─────────│            │                │            │
    │─S3직접업로드──────────────────────────────────────────────────►│
    │           │        │─tip 생성 ───────────────────────────────►│
    │           │        │─큐 발행 ───►│                │            │
    │◄─tipId ────────────│            │                │            │
    │ (processing)       │            │─작업 전달 ──────►│            │
    │           │        │            │                │─Cat API    │
    │           │        │            │                │─Claude     │
    │           │        │            │                │─임베딩      │
    │           │        │            │                │─RPC 검색──►│
    │           │        │            │                │◄─결과 3건───│
    │           │        │            │                │─tip 업데이트►│
    │           │        │            │                │─Pub/Sub ──►│
    │           │◄─Realtime Broadcast─────────────────│            │
    │◄─tip.complete───────│            │                │            │
```

### 10.2 실종 신고 등록 + 임베딩 사전 저장

```
클라이언트       Express        Upstash      Python Worker    Supabase
    │               │              │               │              │
    │─POST /pets ──►│              │               │              │
    │               │─pets INSERT ─────────────────────────────►│
    │◄─petId ───────│              │               │              │
    │               │─embedding 큐 발행►│             │              │
    │               │              │─작업 전달 ────►│              │
    │               │              │               │─Claude Sonnet │
    │               │              │               │─임베딩 생성    │
    │               │              │               │─upsert ──────►│
    │               │              │               │─status 업데이트►│
    │               │─푸시 알림 큐 발행►│             │              │
    │               │              │─반경 2km 유저 조회─────────────►│
    │               │              │─FCM 발송       │              │
```

---

## 11. Nginx 설정 (최종)

```nginx
upstream express_backend { server 127.0.0.1:3000; keepalive 64; }
upstream fastapi_ai       { server 127.0.0.1:8000; keepalive 16; }

limit_req_zone $binary_remote_addr zone=auth:10m rate=10r/m;
limit_req_zone $binary_remote_addr zone=api:10m  rate=100r/m;
limit_req_zone $binary_remote_addr zone=ai:10m   rate=20r/m;

server {
    listen 443 ssl http2;
    server_name api.missingpet.kr;

    ssl_certificate     /etc/letsencrypt/live/api.missingpet.kr/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.missingpet.kr/privkey.pem;

    # 인증 (엄격한 Rate Limit)
    location /api/auth/ {
        limit_req zone=auth burst=5 nodelay;
        proxy_pass http://express_backend;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # AI 분석 (긴 타임아웃)
    location /ai/ {
        limit_req zone=ai burst=3 nodelay;
        client_max_body_size 50M;
        proxy_read_timeout 120s;
        proxy_pass http://fastapi_ai;
    }

    # 일반 API
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://express_backend;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://express_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade    $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 3600s;
    }
}
```

---

## 12. MVP 구현 우선순위

| 단계 | 범위 | Supabase 활용 포인트 |
|---|---|---|
| **MVP** | Auth + Pets CRUD + Storage + 알림 목록 | Supabase Auth, PostgreSQL, Storage |
| **v1.1** | pgvector + 임베딩 파이프라인 | pgvector 확장, RPC 함수 등록 |
| **v1.2** | Claude Sonnet 특징 증강 + BullMQ | Upstash Redis + BullMQ 비동기 |
| **v1.3** | Two-Stage Filtering 완성 | The Cat API + breed 필터 SQL 통합 |
| **v1.4** | 실시간 채팅 + 푸시 + 반경 알림 | Supabase Realtime + FCM |

---

*Last updated: 2026-05-06*
*Tech Stack: Node.js(Express) + Python(FastAPI) + Supabase(PostgreSQL + pgvector + Auth + Storage + Realtime) + Upstash Redis(BullMQ) + Nginx*
