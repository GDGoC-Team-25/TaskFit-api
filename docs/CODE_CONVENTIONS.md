# 팀 코드 컨벤션

> TaskFit API (GDGoC Team 25) 팀 코드 컨벤션 문서

---

## 1. 언어 규칙

| 항목 | 언어 |
|------|------|
| 코드 (변수, 함수, 클래스) | 영어 |
| 주석 | 한국어 |
| 커밋 메시지 | 한국어 |
| 문서 (README, PLAN 등) | 한국어 |
| API 에러 메시지 | 한국어 |

---

## 2. 네이밍 컨벤션

### Python

| 대상 | 규칙 | 예시 |
|------|------|------|
| 변수, 함수 | `snake_case` | `get_task_by_id`, `user_name` |
| 클래스 | `PascalCase` | `TaskResponse`, `UserCompetency` |
| 상수 | `UPPER_SNAKE_CASE` | `MAX_QUESTIONS`, `DEFAULT_PAGE_SIZE` |
| 파일명 | `snake_case` | `ai_service.py`, `task_key_point.py` |
| 패키지(디렉토리) | `snake_case` | `models/`, `services/` |

### DB

| 대상 | 규칙 | 예시 |
|------|------|------|
| 테이블명 | 복수형 `snake_case` | `users`, `task_key_points` |
| 컬럼명 | `snake_case` | `created_at`, `company_id` |
| FK 컬럼 | `{참조테이블_단수}_id` | `user_id`, `task_id` |
| 인덱스 | `ix_{테이블}_{컬럼}` | `ix_tasks_company_id` |

### API

| 대상 | 규칙 | 예시 |
|------|------|------|
| URL 경로 | `kebab-case` 또는 복수형 명사 | `/companies`, `/task-key-points` |
| Query Parameter | `snake_case` | `?company_id=1&page_size=10` |
| JSON 필드 | `snake_case` | `{ "user_name": "..." }` |

---

## 3. 커밋 컨벤션

### 커밋 메시지 형식

```
<type>: <한국어 설명>

(선택) 상세 내용
- 변경사항 1
- 변경사항 2
```

### Type 분류

| Type | 조건 |
|------|------|
| `feat` | 새 파일 추가, 새 기능/엔드포인트/컴포넌트 구현 |
| `fix` | 기존 로직 수정, 버그 해결, 에러 처리 추가 |
| `refactor` | 동작 변경 없이 코드 구조 개선, 이름 변경, 추출 |
| `style` | CSS/UI만 변경, 포맷팅, 공백 |
| `test` | 테스트 파일 추가/수정 |
| `chore` | pyproject.toml, config 파일 변경, 의존성 업데이트 |
| `docs` | README, CLAUDE.md, 주석만 변경 |
| `perf` | 성능 개선 (쿼리 최적화, 메모이제이션 등) |

### 예시

```bash
# 단순 커밋
feat: 대시보드 차트 컴포넌트 추가

# 상세 내용이 있는 커밋
feat: 과제 생성 API 구현

- POST /tasks 엔드포인트 추가
- Gemini API 연동하여 과제 자동 생성
- task_key_points 테이블에 핵심 포인트 저장

# 버그 수정
fix: 과제 목록 조회 시 N+1 쿼리 문제 해결

# 리팩토링
refactor: ai_service에서 프롬프트 생성 로직 분리
```

### 커밋 규칙

1. 하나의 커밋은 하나의 논리적 변경만 포함
2. 커밋 제목은 50자 이내
3. 본문은 72자에서 줄바꿈
4. **커밋 시 `/commit` 스킬 사용 권장**

---

## 4. 코드 스타일

### 함수/메서드

```python
# 모든 엔드포인트 및 서비스 함수는 async
async def get_tasks_by_company(db: AsyncSession, company_id: int) -> list[Task]:
    """기업별 과제 목록 조회"""
    result = await db.execute(select(Task).where(Task.company_id == company_id))
    return result.scalars().all()
```

### Import 순서

```python
# 1. 표준 라이브러리
from datetime import datetime

# 2. 서드파티
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

# 3. 프로젝트 내부
from src.core.database import get_db
from src.models.schemas.task import TaskResponse
```

### Pydantic 모델

```python
# 생성 요청 - 필수 필드만
class TaskCreate(BaseModel):
    company_id: int
    job_role_id: int

# 수정 요청 - 모두 Optional
class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None

# 응답 - from_attributes 필수
class TaskResponse(BaseModel):
    id: int
    title: str
    created_at: datetime

    model_config = {"from_attributes": True}
```

### SQLAlchemy ORM

```python
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 관계 정의
    company = relationship("Company", back_populates="tasks", lazy="selectin")
```

---

## 5. API 응답 형식

### 성공 응답

```json
{
  "success": true,
  "data": { "id": 1, "title": "..." },
  "error": null
}
```

### 에러 응답

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "NOT_FOUND",
    "message": "해당 과제를 찾을 수 없습니다"
  }
}
```

### 에러 코드 목록

| HTTP 상태 | 에러 코드 | 설명 |
|-----------|-----------|------|
| 400 | `BAD_REQUEST` | 잘못된 요청 |
| 401 | `UNAUTHORIZED` | 인증 필요 |
| 403 | `FORBIDDEN` | 권한 없음 |
| 404 | `NOT_FOUND` | 리소스 없음 |
| 409 | `CONFLICT` | 리소스 충돌 |
| 500 | `INTERNAL_ERROR` | 서버 내부 오류 |

---

## 6. 디렉토리 구조 규칙

```
src/
├── main.py                  # 앱 진입점 - 라우터 include만
├── core/                    # 공통 설정/유틸
├── routers/                 # HTTP 요청 처리 (얇게 유지)
├── models/
│   ├── database/            # SQLAlchemy ORM (DB 스키마)
│   └── schemas/             # Pydantic (API 계약)
└── services/                # 비즈니스 로직 (핵심)
```

### 계층 규칙

| 계층 | 역할 | 금지 사항 |
|------|------|-----------|
| Router | HTTP 요청/응답 처리, 입력 검증 | 직접 DB 쿼리, 비즈니스 로직 |
| Service | 비즈니스 로직, 트랜잭션 관리 | HTTP 관련 코드 (HTTPException 등) |
| Model | 데이터 구조 정의 | 로직 포함 |

---

## 7. 보안 규칙

1. **시크릿**: `.env`로만 관리, 절대 코드에 하드코딩 금지
2. **SQL**: SQLAlchemy ORM/Core만 사용, raw SQL 금지
3. **인증**: 보호가 필요한 엔드포인트에 인증 미들웨어 적용
4. **CORS**: 허용 origin 명시적으로 설정
5. **입력 검증**: Pydantic 모델로 모든 요청 데이터 검증
