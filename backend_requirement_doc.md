# Missing Pet Finder App — 백엔드 요구사항 명세서

> 본 문서는 `src/` 의 React 프론트엔드를 분석하여, 실제 서비스화를 위해 백엔드가 반드시 제공해야 하는 데이터/엔드포인트/실시간 기능/파일 처리/AI 연산 요구사항을 정리한 문서입니다.
> 현재 프론트엔드는 `src/app/data/mockData.ts` 에서 정적 mock 데이터를 사용하고 있으며, 이 mock 을 대체하기 위한 백엔드 사양을 도출했습니다.

---

## 0. 전체 개요

### 0.1 도메인
실종 반려동물 신고/제보 플랫폼. 핵심 기능은 다음과 같습니다.

| 영역 | 화면 | 백엔드 의존도 |
|---|---|---|
| 인증 | `LoginScreen`, `SignUpScreen` | 회원가입/로그인/소셜로그인/세션 |
| 실종 신고 목록 | `HomeTab` | 지역/검색/정렬/페이징 |
| 실종 신고 등록 | `ReportTab` | 멀티스텝 등록 + 사진 업로드 + 위치 + 푸시 발송 트리거 |
| 실종 상세 | `PetDetailScreen` | 단건 조회, 좋아요/조회수/댓글, 신고자 정보 |
| 제보(AI 유사도) | `TipTab` | 이미지 업로드, AI 유사도 분석, 결과 반환 |
| 채팅 목록 | `ChatListTab` | 채팅방 목록, 미읽음 카운트, 온라인 상태 |
| 채팅방 | `ChatRoomScreen` | 실시간 메시징, 읽음 처리, 첨부, 위치 공유 |
| 알림 | `NotificationScreen`, 메인 헤더 벨 | 알림 목록, 미읽음 카운트, 푸시 |

### 0.2 클라이언트 전제
- 모바일 웹(390px 폭) UI. 향후 네이티브 앱 확장 가능성을 고려하여 푸시 알림(FCM/APNs) 연동을 가정합니다.
- 라우팅: `react-router` v7 클라이언트 라우팅.
- 한국어 콘텐츠/한국 시간(KST), 통화 단위 KRW.
- 위치는 "구(district)" 단위로 기본 필터링 (`서울시 마포구` 등).

### 0.3 응답 포맷 (제안)
- JSON, snake/camelCase 일관성 유지(프론트는 camelCase 사용 → camelCase 권장).
- 시간은 ISO 8601 (`2025-04-14T10:00:00+09:00`).
- 에러: `{ "code": "XXX", "message": "한국어 메시지", "fields": {...} }`.
- 인증: `Authorization: Bearer <accessToken>` 헤더.

---

## 1. 인증 / 사용자 (Auth & User)

### 1.1 프론트엔드에서 도출한 요구사항

| 출처 | 요구사항 |
|---|---|
| `LoginScreen.tsx` | 이메일+비밀번호 로그인, Google 소셜 로그인, "비밀번호를 잊으셨나요?" 링크, "둘러보기(비로그인)" 게스트 모드 |
| `SignUpScreen.tsx` | 2단계 회원가입: (1) 이름/이메일/휴대폰/비밀번호(8자 이상)/비밀번호 확인, (2) 약관 동의(이용약관/개인정보처리방침=필수, 마케팅=선택) |

### 1.2 필요한 엔드포인트

| 메서드 | 경로 | 설명 |
|---|---|---|
| `POST` | `/api/auth/signup` | 회원가입. body: `{ name, email, phone, password, agreeTerms, agreePrivacy, agreeMarketing }`. 반환: `{ accessToken, refreshToken, user }` |
| `POST` | `/api/auth/login` | 이메일/비밀번호 로그인. 반환: 토큰 쌍 + user |
| `POST` | `/api/auth/login/google` | 구글 OAuth 콜백 (id_token 또는 auth code 검증) |
| `POST` | `/api/auth/refresh` | refreshToken → 신규 accessToken |
| `POST` | `/api/auth/logout` | refreshToken 무효화 |
| `POST` | `/api/auth/password/forgot` | 이메일로 재설정 링크 발송 |
| `POST` | `/api/auth/password/reset` | 토큰 기반 비밀번호 재설정 |
| `GET`  | `/api/users/me` | 내 프로필 조회 |
| `PATCH`| `/api/users/me` | 프로필 수정 |

### 1.3 제약 / 검증 규칙
- 이메일 형식 검증, 중복 가입 방지(409).
- 비밀번호 8자 이상 (프론트에서 `placeholder="8자 이상 입력해주세요"`).
- 휴대폰 번호 포맷 `010-0000-0000`.
- 약관 필수 항목(`agreeTerms`, `agreePrivacy`)이 false면 거절.
- 게스트 모드 지원: 비로그인 사용자도 `HomeTab`/`PetDetailScreen` 등 읽기 전용 진입 가능 → 인증 없는 GET 경로 필요.

### 1.4 사용자 모델 (User)
프론트의 `reporterId`/`reporterName`/`otherUserId`/`otherUserName`/`otherUserAvatar`/`isOnline` 필드에서 역산:

```ts
User {
  id: string            // ex. "user1"
  name: string          // 표시명
  email: string
  phone: string
  avatarUrl: string     // 채팅 목록 otherUserAvatar 로 노출
  isOnline: boolean     // 채팅 목록/방에서 온라인 표시
  lastSeenAt: string    // 오프라인 시 활용
  agreeMarketing: boolean
  createdAt: string
}
```

---

## 2. 실종 반려동물 (Missing Pet)

### 2.1 데이터 모델
`mockData.ts` 의 `MissingPet` 인터페이스를 그대로 백엔드 스키마로 반영해야 합니다.

```ts
MissingPet {
  id: number | string
  name: string
  breed: string
  age: string                // "3살" 처럼 한글 자유 텍스트
  gender: "남" | "여"
  color: string
  location: string           // "서울시 마포구 합정동" (전체 주소)
  district: string           // "마포구" (필터링용 정규화 필드)
  lastSeen: string           // "2025-04-14" (실종 날짜, YYYY-MM-DD)
  reward: number             // 사례금, 0이면 없음
  photo: string              // 대표 사진 URL
  photos?: string[]          // 추가 사진 (PetDetailScreen 캐러셀 3장 이상)
  likes: number              // 누적 좋아요 수
  comments: number           // 댓글 수
  status: "실종" | "찾음"
  description: string
  reporterId: string
  reporterName: string       // 비정규화 표시용
  createdAt: string          // ISO 8601
  views: number              // 조회수
  // ReportTab 에서 추가로 수집되는 필드
  detailAddress?: string
  lostTime?: "오전 6-12시" | "오후 12-18시" | "저녁 18-24시" | "새벽 0-6시" | "모름"
  // 위치 기반 푸시/검색을 위해 백엔드에서 보강 필요
  latitude?: number
  longitude?: number
}
```

### 2.2 필요한 엔드포인트

#### 2.2.1 목록 조회 (`HomeTab`)
- `GET /api/pets`
- 쿼리 파라미터:
  - `district`: `"전체"` 또는 `"마포구"` 등. `"전체"` 면 필터 없음 (`MainScreen` 의 districts 배열 참고: 마포구/서초구/강남구/송파구/은평구/노원구/종로구/중구/용산구).
  - `q`: 검색어. 프론트 `HomeTab` 에서 **이름/품종/위치(전체 location 문자열)** 에 부분일치 검색.
  - `sort`: `latest` | `likes` | `comments` (기본 latest).
  - `status`: `실종` | `찾음` (기본 둘 다).
  - `cursor` 또는 `page`, `limit`: 페이지네이션 (현재 mock은 7건이지만 실제 서비스에서는 무한스크롤 권장).
- 반환 항목: `MissingPet` 의 카드용 서브셋 (id, name, breed, age, gender, location, district, lastSeen, reward, photo, likes, comments, status, createdAt, views).

#### 2.2.2 상세 조회 (`PetDetailScreen`)
- `GET /api/pets/:id`
- 반환: `MissingPet` 풀필드 + `photos[]` + `reporter` 객체 (`{ id, name, avatarUrl }`).
- **부수 효과**: 호출 시 `views` +1 (혹은 별도 `POST /api/pets/:id/view` 분리). 프론트는 자동 증가 가정.

#### 2.2.3 등록 (`ReportTab`)
- `POST /api/pets`
- 멀티스텝 폼이지만 최종 제출 1회로 가정. body:
  ```json
  {
    "address": "서울시 마포구 합정동",
    "detailAddress": "합정역 7번 출구 앞 공원",
    "latitude": 37.55,            // 지도 탭으로 픽한 좌표 (현재 placeholder)
    "longitude": 126.91,
    "photoUrls": ["https://...","..."],   // 5장 이상 8장 이하
    "name": "초코",
    "breed": "포메라니안",
    "age": "3살",
    "gender": "남",
    "color": "갈색",
    "description": "...",
    "lostDate": "2025-04-14",
    "lostTime": "오후 12-18시",
    "reward": 50000
  }
  ```
- 검증: 사진 5장 이상, 이름/품종 필수, 위치 필수, 실종 날짜 필수(미래 날짜 금지 — 프론트 `max` 속성).
- **부수 효과 (중요)**: `ReportTab` 완료 화면에 *"신고 주변 2km 내 사용자들에게 알림이 발송되었습니다"* 메시지 → 백엔드는 게시글 등록 시 **반경 2km 내 사용자에게 푸시/인앱 알림 발송** 작업을 트리거해야 함 (§7 참고).

#### 2.2.4 수정 / 상태 변경 / 삭제
- `PATCH /api/pets/:id` — 작성자만. 상태 `실종 → 찾음` 전환 포함.
- `DELETE /api/pets/:id` — 작성자만.

#### 2.2.5 좋아요
- `POST /api/pets/:id/like`, `DELETE /api/pets/:id/like`
- `HomeTab` / `PetDetailScreen` 의 `likedPets` 로컬 상태를 서버 상태로 옮겨야 함. 현재는 토글 시 `pet.likes + (isLiked ? 1 : 0)` 로 즉석 반영 → 서버는 사용자별 like 여부와 누적 카운트를 함께 응답.

#### 2.2.6 댓글
- `mockData` 의 `comments` 필드는 **개수만** 사용되지만, `PetDetailScreen` 에는 댓글 섹션이 노출 영역으로 존재 (현재는 카운트만). 추후 확장을 고려하면 다음 엔드포인트 필요:
  - `GET /api/pets/:id/comments`
  - `POST /api/pets/:id/comments`
  - `DELETE /api/comments/:commentId`

### 2.3 검색/정렬 동작 명세 (프론트 동작 그대로 재현)
- **District 필터**: `"전체"` 일 때 전체, 그 외엔 `pet.district === district` 일치 (정확 일치).
- **검색**: `name`, `breed`, `location` 세 필드에 대한 **부분 문자열 매칭** (한글 그대로). 백엔드는 LIKE/Full-text 어느 쪽이든 가능.
- **정렬**:
  - `latest`: `createdAt` desc
  - `likes`: `likes` desc
  - `comments`: `comments` desc

### 2.4 지역(District) 메타
프론트에 하드코딩된 목록: `전체, 마포구, 서초구, 강남구, 송파구, 은평구, 노원구, 종로구, 중구, 용산구`.
- 향후 확장을 위해 `GET /api/districts` 로 서버 제공 권장 (현재는 정적 처리도 무방).

---

## 3. 제보 / AI 유사도 (Tip & Similarity)

### 3.1 프론트 동작 (`TipTab.tsx`)
1. 사용자가 사진 3~5장 업로드.
2. "유사도 검증 시작" 클릭 → 진행률 0~100% 애니메이션 (현재는 클라이언트 setTimeout).
3. **단계별 메시지**: "데이터베이스 조회 중", "특징점 추출 중", "유사도 매칭 중".
4. 결과로 상위 3건의 `MissingPet` + 유사도 점수(현재 mock은 `[94, 78, 61]` 고정, 1위는 빨간 강조 테두리)를 노출.
5. "보호자에게 제보 전송하기" 클릭 시 채팅 목록으로 이동 → **제보 채팅방 자동 생성**이 백엔드에서 일어나야 함.

### 3.2 필요한 엔드포인트

| 메서드 | 경로 | 설명 |
|---|---|---|
| `POST` | `/api/tips/analyze` | 멀티파트(또는 사전 업로드한 URL) 사진 3~5장 업로드 → AI 모델로 매칭. 반환: `{ tipId, results: [{ petId, similarity:0~100, pet:{...요약} }, ...최대 3건] }`. 응답 시간이 길 경우 §3.3 비동기 모델 권장. |
| `POST` | `/api/tips/:tipId/send` | body: `{ petId }`. 제보를 해당 게시글 작성자에게 전송 → 채팅방 생성 + 첫 메시지(사진 + 위치) 자동 발송. 반환: `{ chatId }`. |
| `GET`  | `/api/tips/me` | 내가 보낸 제보 이력 (확장용) |

### 3.3 비동기 처리 (선택, 권장)
유사도 분석이 수 초 이상 걸릴 수 있으므로:
- `POST /api/tips/analyze` 는 즉시 `{ tipId, status:"processing" }` 반환.
- `GET /api/tips/:tipId` 폴링 또는 WebSocket 으로 `{ status:"done", results:[...] }` 수신.
- 프론트의 진행률 바는 서버 보고 진행률(`progress: 0~100`)과 동기화 가능하도록 설계 권장.

### 3.4 AI 모델 측 요구사항 (백엔드 책임)
- 입력: JPEG/PNG 이미지 N장(3~5).
- 후보군: `status === "실종"` 인 `MissingPet` 의 등록 사진들.
- 출력: 상위 3건 + 0~100 정수 유사도.
- 추가 필터(권장): 제보 사진의 EXIF/업로더 위치를 사용해 **반경 N km 이내 실종 건 우선 매칭**.

---

## 4. 사진 업로드 (Image Upload)

### 4.1 사용 처
- `ReportTab`: 5~8장 등록.
- `TipTab`: 3~5장 분석.
- `ChatRoomScreen`: 메시지 첨부(앨범/카메라).
- `SignUpScreen`/`User`: 향후 프로필 사진.

### 4.2 권장 방식
- `POST /api/uploads/presign` → S3/GCS presigned URL 반환 후 클라이언트 직업로드.
- 응답: `{ uploadUrl, fileUrl, expiresAt }`.
- 또는 단순 멀티파트: `POST /api/uploads` (file) → `{ url }`.
- 제약: 이미지 MIME 화이트리스트, 최대 10MB/장 권장, EXIF 회전 보정 처리(서버측 권장).

---

## 5. 채팅 (Chat)

### 5.1 데이터 모델 (mockData)

```ts
Chat {
  id: number
  petId: number               // 채팅이 어떤 실종건에 묶이는지
  petName, petPhoto, petBreed, petDistrict   // 비정규화 (목록 표시용)
  otherUserId, otherUserName, otherUserAvatar // 상대방 정보
  lastMessage: string
  lastMessageTime: string     // 표시 포맷 "오후 2:30", "어제", "3일 전"
  unreadCount: number
  isOnline: boolean
}

ChatMessage {
  id: string                  // 클라가 임시로 "msg_<ts>" 생성
  senderId: "me" | "other"    // 서버는 실제 userId 로, 클라가 자체 변환
  message: string
  time: string                // 표시 포맷
  read: boolean
  type: "text" | "image"
  imageUrl?: string
}
```

### 5.2 필요한 엔드포인트 / 실시간

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/api/chats` | 내 채팅방 목록. 검색(`q` — petName/otherUserName/lastMessage 부분일치)·정렬(최근 메시지순). |
| `GET` | `/api/chats/:chatId` | 채팅방 메타(상대방, 연관 pet, 온라인 상태) |
| `GET` | `/api/chats/:chatId/messages?cursor=...&limit=50` | 메시지 페이지네이션 |
| `POST` | `/api/chats/:chatId/messages` | 메시지 전송. body: `{ type, message?, imageUrl?, latitude?, longitude? }`. |
| `POST` | `/api/chats` | 채팅방 생성/조회 (idempotent). body: `{ petId, otherUserId }` → 이미 있으면 기존 반환. (`PetDetailScreen` 의 "제보하기" 버튼, `TipTab` 결과 화면이 트리거) |
| `POST` | `/api/chats/:chatId/read` | 읽음 처리. 미읽음 카운트 0으로. |
| `POST` | `/api/chats/:chatId/leave` | 채팅방 나가기 (헤더 더보기 메뉴) |
| `POST` | `/api/chats/:chatId/report` | 신고하기 (헤더 더보기 메뉴) |

### 5.3 실시간 (WebSocket / SSE)
프론트 `ChatRoomScreen` 은 즉시 송수신을 가정합니다. 다음 이벤트 채널이 필요합니다.

- 연결: `wss://.../ws` + Bearer 인증.
- 구독 단위: 사용자(전역) + 활성 채팅방.
- 서버→클라 이벤트:
  - `message.new`: `{ chatId, message: ChatMessage }`
  - `message.read`: `{ chatId, messageIds:[...], readerId }`
  - `chat.updated`: `{ chatId, lastMessage, lastMessageTime, unreadCount }`
  - `presence.update`: `{ userId, isOnline, lastSeenAt }`
- 클라→서버 이벤트:
  - `typing` (선택): `{ chatId, isTyping }` — 현재 화면엔 타이핑 인디케이터 placeholder 만 존재.

### 5.4 메시지 첨부 (액션 드로어)
`ChatRoomScreen` 의 `+` 버튼 액션:
- `앨범` / `카메라` → 이미지 메시지 (`type:"image"`, `imageUrl`).
- `장소` → 위치 메시지. body 에 `latitude/longitude` + 표시용 `placeName` 권장. 별도 `type: "location"` 도입 필요.
- `제보` → 제보 정보 카드 (실종건 요약 카드 첨부). `type: "tipCard"` + `payload: { petId, ... }` 등 확장.

### 5.5 시간 표시 포맷
프론트는 KST 기준 `오후 2:30`, `오전 11:15`, `어제`, `3일 전` 형식을 사용합니다.
- 백엔드는 ISO 시간만 내려주고, 프론트 변환 책임으로 두는 것을 권장 (현재 일부 mock 은 사람이 손으로 만든 문자열).
- 채팅 목록의 `lastMessageTime` 필드도 ISO 로 통일하고, 프론트에서 "오늘이면 시:분, 어제면 어제, 그 외엔 N일 전" 변환 로직을 갖도록 가이드.

---

## 6. 좋아요 / 댓글 / 조회수

| 항목 | 트리거 | 백엔드 처리 |
|---|---|---|
| 좋아요 | `HomeTab` 의 하트 버튼, `PetDetailScreen` 의 헤더 하트 | 사용자별 like 1건 (unique). 카운트 캐시 갱신. |
| 조회수 | 상세 진입 | 사용자/세션당 중복 카운트 방지 (디바운스 또는 일자별 1회). |
| 댓글 | (현재 카운트만) | §2.2.6 |

---

## 7. 알림 (Notifications)

### 7.1 화면 동작
- `MainScreen` 헤더 종 아이콘에 미읽음 뱃지 표시.
- `NotificationScreen` 에서 목록 조회, 개별/전체 읽음 처리.
- mockData `AppNotification` 타입:
  ```ts
  AppNotification {
    id: number
    type: "comment" | "like" | "tip" | "found"
    message: string         // "초코 게시글에 새로운 제보가 있습니다"
    time: string            // "방금 전" / "10분 전" / "1시간 전" 표시 — 백엔드는 ISO 권장
    read: boolean
    petName: string
    petPhoto: string
  }
  ```

### 7.2 필요한 엔드포인트

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/api/notifications` | 페이지네이션, `?unreadOnly=true` 옵션 |
| `GET` | `/api/notifications/unread-count` | 헤더 뱃지용 |
| `POST` | `/api/notifications/:id/read` | 단건 읽음 |
| `POST` | `/api/notifications/read-all` | 전체 읽음 |
| `POST` | `/api/devices/register` | 푸시 토큰 등록 (FCM/APNs) |
| `DELETE` | `/api/devices/:tokenId` | 토큰 해제 |

### 7.3 알림 발생 트리거 (서버 측)

| 타입 | 발생 조건 | 수신자 |
|---|---|---|
| `tip` | 게시글에 새 제보(채팅) 도착 | 게시글 작성자 |
| `comment` | 게시글에 댓글 작성 | 게시글 작성자 |
| `like` | 누적 좋아요 N개 단위 도달 (mock: "12명이 좋아합니다") | 게시글 작성자 |
| `found` | **반경 2km 내 유사 동물 발견** (실종 후 일정 기간 경과) | 실종 신고 작성자 |
| `nearby_report` | **새 실종 신고 등록 시 반경 2km 사용자에게 푸시** (§2.2.3 부수효과) | 인근 사용자 |

### 7.4 시간 표시
프론트는 `방금 전 / 10분 전 / 1시간 전` 표시. 서버는 ISO `createdAt` 만 내려주고 프론트가 가공하도록 통일 권장.

---

## 8. 위치 / 지도 (Geolocation)

### 8.1 사용 처
- `MainScreen`: 헤더의 지역(구) 선택. 클라 상태이며 백엔드 없이 동작 가능하나, 사용자 기본 지역(`defaultDistrict`)을 프로필에 저장할 수 있음.
- `ReportTab`: 지도 탭 후 위치 픽 (현재 placeholder 이미지). 실서비스에서는 카카오/네이버 맵 SDK 사용을 가정.
- `HomeTab`: "지도로 보기" 버튼 (현재 라우팅만, 미구현).
- 알림 발송 반경 2km 계산 → 백엔드는 위경도 기반 지오공간 인덱스(PostGIS / MongoDB 2dsphere 등) 필요.

### 8.2 백엔드가 필요한 것
- `MissingPet.latitude/longitude` 저장.
- `User.lastKnownLocation` (선택) — 반경 내 푸시 발송용.
- 지오쿼리: `pets within 2km of (lat, lng)`.

### 8.3 외부 의존성 (참고)
- 주소 → 좌표 변환은 카카오/네이버/Google geocoding 사용 가정 (프론트 또는 백엔드 어느 쪽에서든 호출 가능). 백엔드 측에서 통합 처리하면 키 노출 방지에 유리.

---

## 9. 비기능 요구사항

### 9.1 인증/보안
- JWT (access ~15분 / refresh ~30일) + 회전.
- 비밀번호: bcrypt/argon2 해싱.
- 게시글/채팅/제보에 **소유자 권한 검증** 필수 (수정/삭제/메시지 송신).
- 신고/허위 게시글 처리(`/api/pets/:id/report`, `/api/chats/:id/report`).

### 9.2 페이지네이션
- 커서 기반 권장 (특히 채팅 메시지/알림). 응답에 `nextCursor` 포함.

### 9.3 캐싱/성능
- 목록 응답: `ETag` 또는 `If-Modified-Since` 활용.
- 상세 조회의 view 카운트 증가는 별도 큐(예: Redis INCR) 후 배치 반영.

### 9.4 실시간 채널 인증
- WS 연결 시 JWT 검증, 채널 ACL (자기 chatId 만 구독).

### 9.5 로깅/관측
- 게시 등록, 알림 발송 수, AI 분석 요청량/지연시간 메트릭 필수.

### 9.6 다국어/시간대
- 현재 한국어/KST 전제. `Accept-Language` 헤더 대비 i18n 키 분리는 추후 과제.

---

## 10. 엔드포인트 요약 (체크리스트)

### Auth
- [ ] `POST /api/auth/signup`
- [ ] `POST /api/auth/login`
- [ ] `POST /api/auth/login/google`
- [ ] `POST /api/auth/refresh`
- [ ] `POST /api/auth/logout`
- [ ] `POST /api/auth/password/forgot`
- [ ] `POST /api/auth/password/reset`

### User
- [ ] `GET /api/users/me`
- [ ] `PATCH /api/users/me`

### Pets
- [ ] `GET /api/pets` (district, q, sort, status, cursor)
- [ ] `GET /api/pets/:id`
- [ ] `POST /api/pets`
- [ ] `PATCH /api/pets/:id`
- [ ] `DELETE /api/pets/:id`
- [ ] `POST /api/pets/:id/like`, `DELETE /api/pets/:id/like`
- [ ] `GET /api/pets/:id/comments`, `POST /api/pets/:id/comments`, `DELETE /api/comments/:commentId`
- [ ] `POST /api/pets/:id/view` (옵션)
- [ ] `POST /api/pets/:id/report`

### Tips (AI)
- [ ] `POST /api/tips/analyze`
- [ ] `GET /api/tips/:tipId` (비동기 폴링)
- [ ] `POST /api/tips/:tipId/send` → 채팅방 생성

### Chats
- [ ] `GET /api/chats`
- [ ] `GET /api/chats/:chatId`
- [ ] `GET /api/chats/:chatId/messages`
- [ ] `POST /api/chats/:chatId/messages`
- [ ] `POST /api/chats` (idempotent create)
- [ ] `POST /api/chats/:chatId/read`
- [ ] `POST /api/chats/:chatId/leave`
- [ ] `POST /api/chats/:chatId/report`
- [ ] `WSS /ws` (실시간 이벤트)

### Notifications
- [ ] `GET /api/notifications`
- [ ] `GET /api/notifications/unread-count`
- [ ] `POST /api/notifications/:id/read`
- [ ] `POST /api/notifications/read-all`
- [ ] `POST /api/devices/register`, `DELETE /api/devices/:tokenId`

### Uploads
- [ ] `POST /api/uploads/presign` 또는 `POST /api/uploads`

### Meta (옵션)
- [ ] `GET /api/districts`

---

## 11. 프론트엔드가 백엔드와 통합되기 위한 변경점 (참고)

> 백엔드 사양과 직접 관계는 없지만, 통합 시 프론트에서도 다음 작업이 필요합니다.

1. `src/app/data/mockData.ts` 의존 제거 → API 호출 레이어(`src/app/api/*.ts`)로 교체.
2. `LoginScreen.handleLogin` / `SignUpScreen.handleSubmit` 의 setTimeout mock 을 실제 API 호출로 교체, 토큰 저장(localStorage / httpOnly cookie).
3. `HomeTab` 의 클라이언트 사이드 정렬/필터를 서버 쿼리 파라미터로 위임.
4. `ChatRoomScreen` 의 자동 응답 setTimeout 제거 → WebSocket 수신으로 대체.
5. `TipTab` 의 진행률 애니메이션을 서버 진행률 또는 폴링 결과와 동기화.
6. `NotificationScreen` 의 로컬 상태 변경을 API 호출 후 반영.
7. 시간 표시(`오후 2:30`, `1시간 전` 등)는 ISO → 표시 변환 유틸로 통합 (`date-fns` 이미 의존성 있음).
8. 좋아요(`likedPets` Set 로컬 상태)를 서버 상태로 이전.

---

## 12. 우선순위 제안 (MVP → 확장)

| 단계 | 범위 |
|---|---|
| **MVP** | Auth(이메일), Pets(CRUD/목록/상세/검색/필터), Uploads, 알림 목록(폴링), 기본 채팅(REST 폴링) |
| **v1.1** | 실시간 채팅(WS), 푸시 알림(FCM), 좋아요/조회수 |
| **v1.2** | AI 유사도 매칭(Tips), 반경 2km 푸시(지오공간) |
| **v1.3** | 소셜 로그인(Google), 신고/차단/관리자, 댓글 |

---

*Last updated: 2026-05-06*
