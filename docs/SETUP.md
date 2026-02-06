# 개발 환경 세팅 가이드

> TaskFit API 프로젝트 개발 환경 구성 가이드

## 사전 요구사항

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) 패키지 매니저
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) (gcloud CLI)
- GCP 프로젝트 `gdgoc-taskfit` 접근 권한

---

## 1. GCP 인증 (최초 1회)

```bash
# Google Cloud SDK 로그인
gcloud auth login

# Application Default Credentials 설정 (Secret Manager, Cloud SQL 접근에 필요)
gcloud auth application-default login

# 프로젝트 설정
gcloud config set project gdgoc-taskfit
```

---

## 2. 프로젝트 설치

```bash
git clone <repo-url>
cd GDGOC

# 의존성 설치
uv sync
```

---

## 3. Secret Manager 시크릿 등록

모든 시크릿은 Google Secret Manager에서 관리합니다. `.env` 파일은 사용하지 않습니다.

### 필요한 시크릿 목록

| Secret ID | 설명 |
|---|---|
| `DB_USER` | Cloud SQL 사용자명 |
| `DB_PASSWORD` | Cloud SQL 비밀번호 |
| `DB_NAME` | 데이터베이스 이름 (기본: `taskfit`) |
| `DB_INSTANCE_CONNECTION_NAME` | Cloud SQL 인스턴스 연결명 |
| `GEMINI_API_KEY` | Google Gemini API 키 |
| `GOOGLE_CLIENT_ID` | Google OAuth 클라이언트 ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth 클라이언트 시크릿 |
| `JWT_SECRET_KEY` | JWT 서명 키 |
| `VERTEX_AI_SEARCH_DATASTORE_ID` | Vertex AI Search 데이터스토어 ID |

### 시크릿 등록 방법

```bash
# 개별 등록
echo -n "시크릿값" | gcloud secrets create SECRET_ID --data-file=-

# 기존 시크릿 업데이트
echo -n "새로운값" | gcloud secrets versions add SECRET_ID --data-file=-

# 시크릿 확인
gcloud secrets versions access latest --secret=SECRET_ID
```

### 일괄 등록 스크립트

```bash
# DB 설정
echo -n "taskfit_user" | gcloud secrets create DB_USER --data-file=- --project=gdgoc-taskfit
echo -n "your-db-password" | gcloud secrets create DB_PASSWORD --data-file=- --project=gdgoc-taskfit
echo -n "taskfit" | gcloud secrets create DB_NAME --data-file=- --project=gdgoc-taskfit
echo -n "gdgoc-taskfit:asia-northeast3:taskfit-db-dev" | gcloud secrets create DB_INSTANCE_CONNECTION_NAME --data-file=- --project=gdgoc-taskfit

# JWT (랜덤 키 생성)
python -c "import secrets; print(secrets.token_urlsafe(32), end='')" | gcloud secrets create JWT_SECRET_KEY --data-file=- --project=gdgoc-taskfit

# Gemini API 키
echo -n "your-gemini-api-key" | gcloud secrets create GEMINI_API_KEY --data-file=- --project=gdgoc-taskfit

# Google OAuth
echo -n "your-client-id" | gcloud secrets create GOOGLE_CLIENT_ID --data-file=- --project=gdgoc-taskfit
echo -n "your-client-secret" | gcloud secrets create GOOGLE_CLIENT_SECRET --data-file=- --project=gdgoc-taskfit
```

### 팀원 권한 부여

```bash
# Secret Manager 접근 권한 부여
gcloud projects add-iam-policy-binding gdgoc-taskfit \
  --member="user:팀원이메일@gmail.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

## 4. Cloud SQL 설정

### 인스턴스 정보

| 항목 | 값 |
|---|---|
| 프로젝트 | `gdgoc-taskfit` |
| 인스턴스 | `taskfit-db-dev` |
| 리전 | `asia-northeast3` (서울) |
| 연결명 | `gdgoc-taskfit:asia-northeast3:taskfit-db-dev` |

### DB 사용자 생성

```bash
# Cloud SQL에 사용자 생성
gcloud sql users create taskfit_user \
  --instance=taskfit-db-dev \
  --password="your-secure-password"

# 데이터베이스 생성
gcloud sql databases create taskfit \
  --instance=taskfit-db-dev
```

### 로컬 연결 테스트

```bash
# Cloud SQL Auth Proxy 없이 Cloud SQL Connector로 자동 연결 (코드 내장)
uv run python -c "
import asyncio
from src.core.config import get_settings
s = get_settings()
print(f'Project: {s.gcp_project_id}')
print(f'DB: {s.db_name}')
print(f'Instance: {s.db_instance_connection_name}')
print('Settings loaded successfully!')
"
```

---

## 5. Vertex AI Search 설정

### 5-1. API 활성화

```bash
gcloud services enable discoveryengine.googleapis.com --project=gdgoc-taskfit
gcloud services enable aiplatform.googleapis.com --project=gdgoc-taskfit
```

### 5-2. 데이터스토어 생성

1. [Google Cloud Console](https://console.cloud.google.com/gen-app-builder/engines) 접속
2. **Agent Builder** → **Data Stores** → **Create Data Store**
3. 데이터 소스: **Website URL** 선택
4. 기업 기술 블로그 URL 등록:
   - `https://toss.tech/*`
   - `https://techblog.woowahan.com/*`
   - `https://tech.kakao.com/*`
   - `https://engineering.linecorp.com/ko/*`
   - `https://netflixtechblog.com/*`
5. 데이터스토어 이름: `taskfit-tech-blogs`
6. 생성 후 **데이터스토어 ID**를 Secret Manager에 등록:

```bash
echo -n "데이터스토어ID" | gcloud secrets create VERTEX_AI_SEARCH_DATASTORE_ID --data-file=- --project=gdgoc-taskfit
```

### 5-3. Search App 생성

1. **Agent Builder** → **Apps** → **Create App**
2. 타입: **Search**
3. 데이터스토어: 위에서 생성한 `taskfit-tech-blogs` 연결
4. 앱 이름: `taskfit-search`

---

## 6. 개발 서버 실행

```bash
# 서버 실행
uv run uvicorn src.main:app --reload

# API 문서 확인
# http://localhost:8000/docs
```

---

## 7. CI/테스트 환경

CI 환경에서는 `.env` 파일을 사용할 수 있습니다:

```bash
cp .env.example .env
# .env 파일에 값 채우기

# .env 파일 모드로 실행
USE_ENV_FILE=true uv run pytest
```

---

## 문제 해결

### "Permission denied" 에러
```bash
# ADC 재설정
gcloud auth application-default login

# Secret Manager 권한 확인
gcloud projects get-iam-policy gdgoc-taskfit \
  --flatten="bindings[].members" \
  --filter="bindings.role=roles/secretmanager.secretAccessor"
```

### Cloud SQL 연결 실패
```bash
# Cloud SQL Admin API 활성화
gcloud services enable sqladmin.googleapis.com --project=gdgoc-taskfit

# 인스턴스 상태 확인
gcloud sql instances describe taskfit-db-dev --project=gdgoc-taskfit
```
