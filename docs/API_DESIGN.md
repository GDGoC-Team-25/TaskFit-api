# TaskFit API 기획

## 결정사항 요약

- 기업/직무: 사전 등록 (시드 데이터)
- 인증: Google OAuth → JWT 발급
- 채팅: 동기 REST (요청-응답)
- 과제: 기업+직무 조합당 3~5개 생성 후 DB 캐싱
- **DB FK 미사용**: ForeignKey 제약조건 없이 Integer 컬럼으로만 관리. 관계는 코드(application) 레벨에서 처리.

---

## 1. DB 스키마

### users
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | |
| google_id | String UNIQUE | Google OAuth sub |
| email | String UNIQUE | |
| name | String | |
| profile_image | String NULL | |
| created_at | DateTime | |
| updated_at | DateTime | |

### companies
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | |
| name | String UNIQUE | 기업명 (토스, 카카오 등) |
| description | Text NULL | 기업 소개 |
| logo_url | String NULL | |
| tech_blog_url | String NULL | 기술 블로그 URL |
| created_at | DateTime | |

### job_roles
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | |
| name | String UNIQUE | 직무명 (백엔드, 프론트엔드 등) |
| description | Text NULL | |
| created_at | DateTime | |

### tasks
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | |
| company_id | Integer | companies.id 참조 |
| job_role_id | Integer | job_roles.id 참조 |
| title | String | 과제 제목 |
| persona_name | String | 상사 이름 (김과장 등) |
| persona_role | String | 상사 직책/역할 |
| background | Text | 과제 배경 |
| tech_stack | JSONB | 기술 스택 목록 |
| requirements | Text | 요구사항 |
| deliverables | JSONB | 제출물 목록 |
| difficulty | String | 난이도 (junior/mid/senior) |
| created_at | DateTime | |

### task_key_points
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | |
| task_id | Integer | tasks.id 참조 |
| point | Text | 핵심 평가 포인트 |
| category | String | 카테고리 (구현력/이해도/설계) |

### submissions
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | |
| user_id | Integer | users.id 참조 |
| task_id | Integer | tasks.id 참조 |
| content | Text | 제출 내용 (마크다운) |
| status | String | pending / reviewing / evaluated |
| created_at | DateTime | |
| updated_at | DateTime | |

### threads
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | |
| submission_id | Integer UNIQUE | submissions.id 참조 (1:1) |
| status | String | questioning / completed |
| total_questions | Integer | 생성된 총 질문 수 |
| asked_count | Integer DEFAULT 0 | 질문한 수 |
| created_at | DateTime | |

### messages
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | |
| thread_id | Integer | threads.id 참조 |
| role | String | ai / user |
| content | Text | 메시지 내용 |
| message_order | Integer | 순서 |
| created_at | DateTime | |

### evaluations
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | |
| submission_id | Integer UNIQUE | submissions.id 참조 (1:1) |
| implementation_score | Integer | 구현력 점수 (0-100) |
| understanding_score | Integer | 이해도 점수 (0-100) |
| total_score | Integer | 종합 점수 (0-100) |
| feedback | Text | 종합 피드백 |
| detail | JSONB | 항목별 상세 평가 |
| created_at | DateTime | |

### user_competencies
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | |
| user_id | Integer | users.id 참조 |
| company_id | Integer | companies.id 참조 |
| job_role_id | Integer | job_roles.id 참조 |
| avg_score | Float | 평균 점수 |
| attempt_count | Integer | 시도 횟수 |
| updated_at | DateTime | |

---

## 2. API 엔드포인트

### Auth (`/auth`)

#### `POST /auth/google`
Google OAuth 로그인 → JWT 발급
```
Request:  { "id_token": "Google에서 받은 ID 토큰" }
Response: { "access_token": "jwt...", "user": { "id", "email", "name", "profile_image" } }
```

#### `GET /auth/me`
현재 로그인 사용자 정보
```
Headers:  Authorization: Bearer <jwt>
Response: { "id", "email", "name", "profile_image" }
```

---

### Companies (`/companies`)

#### `GET /companies`
기업 목록 조회
```
Response: [{ "id", "name", "description", "logo_url" }]
```

---

### Job Roles (`/job-roles`)

#### `GET /job-roles`
직무 목록 조회
```
Response: [{ "id", "name", "description" }]
```

---

### Tasks (`/tasks`)

#### `GET /tasks?company_id={id}&job_role_id={id}`
과제 목록 조회 (DB에 없으면 AI로 3~5개 생성 후 반환)
```
Headers:  Authorization: Bearer <jwt>
Response: [{ "id", "company_id", "job_role_id", "title", "persona_name", "persona_role", "difficulty" }]
```
- 내부 로직: company_id + job_role_id 조합으로 DB 조회 → 없으면 Vertex AI Search + Gemini로 생성 → DB 저장 → 반환

#### `GET /tasks/{task_id}`
과제 상세 조회
```
Headers:  Authorization: Bearer <jwt>
Response: {
  "id", "title", "persona_name", "persona_role",
  "background", "tech_stack", "requirements", "deliverables", "difficulty",
  "company": { "id", "name" },
  "job_role": { "id", "name" }
}
```

---

### Submissions (`/submissions`)

#### `POST /submissions`
과제 제출 (자동으로 채팅 스레드 생성 + AI 첫 질문 포함)
```
Headers:  Authorization: Bearer <jwt>
Request:  { "task_id": 1, "content": "마크다운 제출 내용" }
Response: {
  "submission": { "id", "task_id", "content", "status": "reviewing" },
  "thread": { "id", "status": "questioning", "total_questions": 4 },
  "first_message": { "id", "role": "ai", "content": "제출 확인했습니다. 첫 번째 질문입니다..." }
}
```
- 내부 로직: 제출물 저장 → 스레드 생성 → 제출물 + key_points 기반으로 Gemini에 질문 목록 생성 → 첫 질문 메시지 저장 → 반환

#### `GET /submissions/{submission_id}`
제출 상세 조회
```
Headers:  Authorization: Bearer <jwt>
Response: {
  "id", "task_id", "content", "status", "created_at",
  "task": { "id", "title", "persona_name" },
  "thread": { "id", "status", "total_questions", "asked_count" },
  "evaluation": { "total_score", ... } | null
}
```

#### `GET /submissions`
내 제출 목록
```
Headers:  Authorization: Bearer <jwt>
Query:    ?task_id={id} (선택)
Response: [{ "id", "task_id", "status", "created_at", "task": { "title", "persona_name" } }]
```

---

### Messages (`/submissions/{submission_id}/messages`)

#### `GET /submissions/{submission_id}/messages`
채팅 메시지 목록
```
Headers:  Authorization: Bearer <jwt>
Response: [{ "id", "role", "content", "message_order", "created_at" }]
```

#### `POST /submissions/{submission_id}/messages`
사용자 답변 전송 → AI 후속 응답 반환 (마지막 질문이면 자동 채점)
```
Headers:  Authorization: Bearer <jwt>
Request:  { "content": "사용자 답변" }
Response: {
  "user_message": { "id", "role": "user", "content": "..." },
  "ai_message": { "id", "role": "ai", "content": "..." } | null,
  "thread": { "status": "questioning" | "completed", "asked_count": 3 },
  "evaluation": null | { "total_score", "implementation_score", "understanding_score", "feedback" }
}
```
- 내부 로직:
  1. 사용자 메시지 저장
  2. asked_count < total_questions → Gemini에 다음 질문 생성 → AI 메시지 저장
  3. asked_count == total_questions → 스레드 completed → 채점 시작 → evaluation 저장 → submission status: evaluated

---

### Dashboard (`/dashboard`)

#### `GET /dashboard/me`
내 역량 대시보드
```
Headers:  Authorization: Bearer <jwt>
Response: {
  "total_submissions": 12,
  "avg_score": 78.5,
  "competencies": [
    { "company": { "name": "토스" }, "job_role": { "name": "백엔드" }, "avg_score": 85, "attempt_count": 3 }
  ],
  "recent_evaluations": [
    { "submission_id", "task_title", "total_score", "created_at" }
  ]
}
```

#### `GET /dashboard/me/evaluations`
내 채점 결과 목록
```
Headers:  Authorization: Bearer <jwt>
Response: [{
  "id", "submission_id", "total_score", "implementation_score", "understanding_score",
  "feedback", "detail", "created_at",
  "task": { "title", "company_name", "job_role_name" }
}]
```

#### `GET /dashboard/me/evaluations/{evaluation_id}`
채점 결과 상세
```
Headers:  Authorization: Bearer <jwt>
Response: {
  "id", "implementation_score", "understanding_score", "total_score",
  "feedback", "detail",
  "submission": { "content" },
  "messages": [{ "role", "content" }],
  "task": { "title", "persona_name", "company": { "name" } }
}
```

---

### Dev - AI 테스트 (`/dev/ai`) - 개발 환경에서만 활성화

#### `POST /dev/ai/generate-tasks`
과제 생성 AI 직접 테스트 (DB 저장 없이 결과만 반환)
```
Request:  { "company_name": "토스", "job_role_name": "백엔드", "count": 3 }
Response: {
  "tasks": [{
    "title", "persona_name", "persona_role", "background",
    "tech_stack", "requirements", "deliverables", "difficulty",
    "key_points": [{ "point", "category" }]
  }]
}
```

#### `POST /dev/ai/generate-questions`
질문 생성 AI 직접 테스트
```
Request:  { "task_title": "간편송금 API 구현", "key_points": ["트랜잭션 처리", "에러 핸들링"], "submission_content": "제출 내용..." }
Response: {
  "questions": ["Controller에서 @Transactional을...", "에러 발생 시 롤백 전략은..."]
}
```

#### `POST /dev/ai/evaluate`
채점 AI 직접 테스트
```
Request:  { "task_title": "...", "submission_content": "...", "messages": [{"role": "ai", "content": "..."}, ...] }
Response: {
  "implementation_score": 85, "understanding_score": 78, "total_score": 82,
  "feedback": "...", "detail": { ... }
}
```

---

## 3. 구현 순서

### Phase 1: 기반 구축
1. `src/core/` (config, database, response)
2. `src/models/database/` (전체 ORM 모델, FK 제약조건 없음)
3. `src/models/schemas/` (전체 Pydantic 스키마)
4. Alembic 초기 설정 + 마이그레이션

### Phase 2: 인증
5. `src/routers/auth.py` + `src/services/auth_service.py`
6. JWT 미들웨어 (`src/core/auth.py`)

### Phase 3: 조회 API
7. `src/routers/companies.py` + `src/routers/job_roles.py`
8. 시드 데이터 스크립트

### Phase 4: 핵심 기능
9. `src/services/search_service.py` (Vertex AI Search)
10. `src/services/ai_service.py` (Gemini - 과제 생성/질문 생성/채점)
11. `src/routers/tasks.py` + `src/services/task_service.py`
12. `src/routers/submissions.py` + `src/services/submission_service.py`

### Phase 5: 대시보드
13. `src/routers/dashboard.py` + `src/services/dashboard_service.py`
