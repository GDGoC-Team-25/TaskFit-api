# TaskFit API

### " 진짜 실무 경험을 제공해 드립니다. "

기업 맞춤형 실무 과제 체험 플랫폼 TaskFit 백엔드 서버 입니다.

사용자가 도전하고 싶은 해당 기업의 직무 모집 공고에 활용된 자료를 이용해 AI가 실무 과제를 생성하고, 제출 후 AI 상사 페르소나와의 질의응답을 거쳐 모의 압박 면접 상황을 시뮬레이션 하고, 해결한 실무 과제와 모의 면접을 채점 및 역량 분석을 기반으로 피드백을 제공합니다.

## 제공하는 기능

* **맞춤형 과제 생성**: 사용자가 선택한 기업과 직무의 채용 공고 및 기술 블로그 자료를 기반으로 실무에 가까운 과제를 AI가 실시간으로 생성합니다. 난이도, 카테고리, 예상 소요시간까지 함께 제공하여 체계적인 준비를 지원합니다.

* **AI 상사 시뮬레이션**: 과제 제출 후, 해당 기업의 부서와 직급에 맞는 AI 페르소나가 생성됩니다. 3~5개의 심층 질문을 통해 제출물의 의도와 이해도를 검증하는 모의 압박 면접 상황을 시뮬레이션합니다.

* **데이터 기반 피드백**: 제출한 과제와 질의응답 내용을 종합적으로 분석하여 항목별 점수, 강점과 약점, 개선 방향을 포함한 상세 피드백을 제공합니다. 누적된 결과는 역량 대시보드에서 기업/직무별 성장 추이로 확인할 수 있습니다.

## 사용자 플로우

```
직무 목표 설정 → 기업/직무 선택 → AI 과제 생성
    → 과제 풀이 및 제출
    → AI 상사 페르소나와 질의응답 (3~5회)
    → 채점 및 역량 분석 리포트
    → 대시보드에서 성장 추이 확인
```

## 기술 스택

| 분류 | 기술 |
|------|------|
| Runtime | Python 3.12, FastAPI |
| Package Manager | uv |
| DB | Cloud SQL (PostgreSQL) + SQLAlchemy 2.0 (async) + asyncpg |
| Migration | Alembic |
| AI | Google Gemini API (google-genai SDK) |
| Auth | Google OAuth 2.0, JWT (PyJWT) |
| Infra | Google Cloud Run, Secret Manager |

## 프로젝트 구조

```
src/
├── main.py                  # FastAPI 앱, 라우터 등록
├── core/
│   ├── config.py            # Settings (Secret Manager 연동)
│   ├── database.py          # Cloud SQL Connector, AsyncSession
│   ├── auth.py              # JWT 생성/검증, get_current_user_id
│   └── response.py          # ApiResponse[T] 표준 응답 래퍼
├── routers/                 # API 엔드포인트
│   ├── auth.py              # Google OAuth 로그인
│   ├── companies.py         # 기업 검색
│   ├── job_roles.py         # 직무 카테고리/검색
│   ├── tasks.py             # 과제 생성/조회
│   ├── submissions.py       # 과제 제출
│   ├── threads.py           # AI 질의응답
│   ├── evaluations.py       # 채점 결과 조회
│   ├── dashboard.py         # 대시보드 요약
│   ├── profile.py           # 프로필 조회/수정
│   └── dev.py               # 개발용 (production 제외)
├── models/
│   ├── database/            # SQLAlchemy ORM 모델 (9개)
│   └── schemas/             # Pydantic 요청/응답 스키마
├── services/                # 비즈니스 로직
│   ├── ai_service.py        # Gemini API 연동
│   ├── user_service.py
│   ├── task_service.py
│   ├── submission_service.py
│   ├── thread_service.py
│   ├── evaluation_service.py
│   └── ...
├── alembic/                 # DB 마이그레이션
└── scripts/
    └── seed_data.py         # 테스트 데이터 삽입
```

## 시작하기

### 사전 요구사항

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- GCP 프로젝트 접근 권한 (`gcloud auth application-default login`)

### 설치 및 실행

uv 를 기반으로 서버를 실행해야 합니다.
```bash
# 의존성 설치
uv sync

# DB 마이그레이션 적용
uv run alembic upgrade head

# 개발 서버 실행
uv run uvicorn src.main:app --reload

# 테스트 데이터 삽입
uv run python -m scripts.seed_data
```

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [26876] using WatchFiles
```
해당 로그가 뜬다면 실행에 성공한 겁니다!

서버 실행 후 Swagger 문서는 http://localhost:8000/docs 해당 URL에서 확인 가능합니다.

### 환경변수

시크릿은 Google Secret Manager에서 자동 로드됩니다. 로컬에서 `.env` 파일을 사용하려면:

```bash
USE_ENV_FILE=true uv run uvicorn src.main:app --reload
```
실행해주세요!

필요한 시크릿 목록:

| 키 | 설명 |
|----|------|
| `DB_USER` | Cloud SQL 사용자명 |
| `DB_PASSWORD` | Cloud SQL 비밀번호 |
| `DB_NAME` | 데이터베이스명 |
| `DB_INSTANCE_CONNECTION_NAME` | Cloud SQL 인스턴스 연결명 |
| `GEMINI_API_KEY` | Google Gemini API 키 |
| `GOOGLE_CLIENT_ID` | Google OAuth 클라이언트 ID (웹) |
| `GOOGLE_CLIENT_ID_MOBILE` | Google OAuth 클라이언트 ID (모바일) |
| `GOOGLE_CLIENT_SECRET` | Google OAuth 클라이언트 시크릿 |
| `JWT_SECRET_KEY` | JWT 서명 키 |

## API 엔드포인트

| Method | Path | 설명 | 인증 |
|--------|------|------|------|
| POST | `/auth/google` | Google OAuth 로그인 | - |
| GET | `/auth/me` | 내 정보 조회 | O |
| GET | `/companies` | 기업 검색 | - |
| GET | `/job-roles/categories` | 직무 카테고리 목록 | - |
| GET | `/job-roles` | 직무 검색 | - |
| POST | `/tasks/generate` | AI 과제 생성 | O |
| GET | `/tasks` | 과제 목록 조회 | O |
| GET | `/tasks/{id}` | 과제 상세 조회 | O |
| POST | `/submissions` | 과제 제출 | O |
| PUT | `/submissions/{id}` | 제출물 수정 (draft) | O |
| GET | `/submissions/{id}` | 제출물 조회 | O |
| GET | `/threads` | 질의응답 목록 | O |
| GET | `/threads/{id}` | 질의응답 상세 | O |
| POST | `/threads/{id}/messages` | 메시지 전송 | O |
| GET | `/evaluations/{id}` | 채점 결과 조회 | O |
| GET | `/dashboard/summary` | 대시보드 요약 | O |
| GET | `/profile` | 프로필 조회 | O |
| PATCH | `/profile` | 프로필 수정 | O |
| GET | `/health` | 헬스 체크 | - |

## 배포

### Cloud Run

```bash
gcloud run deploy taskfit-api \
  --source . \
  --region asia-northeast3 \
  --set-env-vars ENVIRONMENT=production,GCP_PROJECT_ID=gdgoc-taskfit \
  --allow-unauthenticated \
  --project=gdgoc-taskfit
```

### Docker (로컬)

```bash
docker build -t taskfit-api .
docker run -p 8080:8080 taskfit-api
```

## 개발 도구

```bash
# 린트
uv run ruff check src/

# 린트 자동 수정
uv run ruff check src/ --fix

# 테스트
uv run pytest

# 마이그레이션 생성
uv run alembic revision --autogenerate -m "설명"
```
