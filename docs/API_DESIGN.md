# TaskFit API 수정 기획 (UI 기반)

## 결정사항 요약

- 기업/직무: **사전 등록 + 검색** (companies, job_roles 테이블 유지)
- 인증: Google OAuth → JWT 발급
- **두 플로우 분리, 데이터 연결**: 홈(문제 풀이) + 직무대화(AI 채팅) → submission → thread → evaluation
- 과제: 기업+직무 조합 기반 AI 생성, `POST /tasks/generate`로 명시적 생성
- DB FK 미사용: Integer 컬럼만, 관계는 코드 레벨
- 북마크/오답노트/순위: **보류**

---

## 1. DB 스키마 (9개 테이블)

### users
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | |
| google_id | String UNIQUE | Google OAuth sub |
| email | String UNIQUE | |
| name | String | |
| bio | Text NULL | 자기소개 |
| profile_image | String NULL | |
| created_at | DateTime | |
| updated_at | DateTime | |

### companies (사전 등록)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | |
| name | String UNIQUE | 기업명 |
| description | Text NULL | 기업 소개 |
| logo_url | String NULL | |
| tech_blog_url | String NULL | 기술 블로그 URL |
| created_at | DateTime | |

### job_roles (사전 등록)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | |
| category | String | 직무 대분류 (개발, 마케팅, 디자인) |
| name | String | 실무 상세 (소프트웨어 엔지니어, 전략기획) |
| description | Text NULL | |
| created_at | DateTime | |

UNIQUE: `(category, name)`

### tasks
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | |
| company_id | Integer | companies.id 참조 |
| job_role_id | Integer | job_roles.id 참조 |
| title | String | 문제 제목 |
| description | Text | 상세 문제 설명 |
| category | String | 카테고리 태그 (자료구조, 시스템 설계, 기술면접) |
| difficulty | String | 난이도 (상/중/하) |
| estimated_minutes | Integer | 예상 소요시간 |
| answer_type | String DEFAULT 'text' | text/code |
| key_points | JSONB NULL | `[{"point": "...", "category": "..."}]` |
| tech_stack | JSONB NULL | `["Python", "FastAPI"]` |
| created_at | DateTime | |

### submissions
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | |
| user_id | Integer | users.id 참조 |
| task_id | Integer | tasks.id 참조 |
| content | Text | 사용자 답변 |
| is_draft | Boolean DEFAULT false | 임시저장 여부 |
| status | String | draft / submitted / reviewing / evaluated |
| time_spent_seconds | Integer NULL | 실제 소요시간 (초) |
| created_at | DateTime | |
| updated_at | DateTime | |

### threads (submission과 1:1)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | |
| submission_id | Integer UNIQUE | submissions.id 참조 (1:1) |
| user_id | Integer | users.id (비정규화) |
| persona_name | String | AI 상사 이름 |
| persona_department | String | 부서 |
| topic_tag | String | 주제 태그 |
| status | String | questioning / completed |
| total_questions | Integer | 총 질문 수 (3~5) |
| asked_count | Integer DEFAULT 0 | 질문 진행 수 |
| created_at | DateTime | |
| updated_at | DateTime | |

### messages
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | |
| thread_id | Integer | threads.id 참조 |
| role | String | ai / user / system |
| content | Text | 메시지 내용 |
| message_order | Integer | 순서 |
| created_at | DateTime | |

### evaluations (submission과 1:1)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | |
| submission_id | Integer UNIQUE | submissions.id 참조 |
| thread_id | Integer UNIQUE | threads.id 참조 (비정규화) |
| total_score | Integer | 종합 점수 (0-100) |
| score_label | String | 등급 (Outstanding, Good 등) |
| scores_detail | JSONB | `[{"name": "시장 분석력", "score": 88}]` |
| ai_summary | Text | AI 분석 요약 |
| analysis_points | JSONB | `{"strengths": [...], "weaknesses": [...]}` |
| feedback | Text NULL | 종합 피드백 |
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
| weak_tags | JSONB NULL | 약점 태그 목록 |
| updated_at | DateTime | |

UNIQUE: `(user_id, company_id, job_role_id)`

---

## 2. API 엔드포인트

모든 응답: `{"success": true/false, "data": ..., "error": null/{"code": "...", "message": "..."}}`

### Auth (`/auth`)
- `POST /auth/google` - Google OAuth → JWT 발급
- `GET /auth/me` [인증] - 현재 사용자 정보

### Companies (`/companies`)
- `GET /companies?q=&limit=` - 기업 검색

### Job Roles (`/job-roles`)
- `GET /job-roles/categories` - 직무 대분류 목록
- `GET /job-roles?category=&q=` - 직무 목록

### Tasks (`/tasks`) [인증]
- `POST /tasks/generate` - AI 문제 생성
- `GET /tasks?company_id=&job_role_id=` - 문제 목록
- `GET /tasks/{task_id}` - 문제 상세

### Submissions (`/submissions`) [인증]
- `POST /submissions` - 답변 제출 / 임시저장 (제출 시 thread + 첫 메시지 자동 생성)
- `PUT /submissions/{id}` - 임시저장 업데이트 / 제출 전환
- `GET /submissions/{id}` - 제출 상세

### Threads & Messages (`/threads`) [인증]
- `GET /threads` - 채팅 목록 (직무대화 탭)
- `GET /threads/{id}` - 채팅 상세 (메시지 포함)
- `POST /threads/{id}/messages` - 메시지 전송 (마지막 답변 시 자동 채점)

### Evaluations (`/evaluations`) [인증]
- `GET /evaluations/{id}` - AI 분석 결과 상세

### Dashboard (`/dashboard`) [인증]
- `GET /dashboard/summary` - 대시보드

### Profile (`/profile`) [인증]
- `GET /profile` - 프로필
- `PATCH /profile` - 프로필 수정

### Dev AI 테스트 (`/dev/ai`)
- `POST /dev/ai/generate-tasks`
- `POST /dev/ai/generate-persona`
- `POST /dev/ai/evaluate`

---

## 3. 데이터 플로우

```
[직무 목표 설정] GET /job-roles/categories → GET /job-roles?category= → GET /companies?q=
                 → POST /tasks/generate { company_id, job_role_id }

[홈 - 문제 풀이] GET /tasks → GET /tasks/{id}
                 → POST /submissions { content, is_draft: false }
                 → submission + thread + first_message 생성

[직무대화]       GET /threads → GET /threads/{id}
                 → POST /threads/{id}/messages
                 → 마지막 답변 시 evaluation 자동 생성

[AI 분석 결과]   GET /evaluations/{id}
[분석 대시보드]  GET /dashboard/summary
[프로필]         GET /profile, PATCH /profile
```
