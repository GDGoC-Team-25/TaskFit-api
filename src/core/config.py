import os
from functools import lru_cache

from google.cloud import secretmanager
from pydantic_settings import BaseSettings


def _get_secret(project_id: str, secret_id: str) -> str:
    """Google Secret Manager에서 시크릿 값을 가져온다."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("utf-8")


def _load_secrets_from_gcp(project_id: str, secret_keys: list[str]) -> dict[str, str]:
    """여러 시크릿을 한번에 로드하여 dict로 반환한다."""
    secrets = {}
    for key in secret_keys:
        try:
            secrets[key] = _get_secret(project_id, key)
        except Exception:
            pass
    return secrets


class Settings(BaseSettings):
    # GCP
    gcp_project_id: str = "gdgoc-taskfit"
    environment: str = "development"

    # Cloud SQL
    db_user: str = "postgres"
    db_password: str = ""
    db_name: str = "postgres"
    db_schema: str = "taskfit"
    db_instance_connection_name: str = "gdgoc-taskfit:asia-northeast3:taskfit-db-dev"

    # Gemini API
    gemini_api_key: str = ""

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""

    # JWT
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7일

    # Vertex AI Search
    vertex_ai_search_datastore_id: str = ""

    model_config = {"env_prefix": "", "case_sensitive": False}


@lru_cache
def get_settings() -> Settings:
    """Secret Manager에서 시크릿을 로드하고 Settings를 생성한다.

    환경변수 USE_ENV_FILE=true로 설정하면 .env 파일을 사용한다 (CI/테스트용).
    """
    if os.getenv("USE_ENV_FILE", "").lower() == "true":
        return Settings(_env_file=".env")

    project_id = os.getenv("GCP_PROJECT_ID", "gdgoc-taskfit")

    secret_keys = [
        "DB_USER",
        "DB_PASSWORD",
        "DB_NAME",
        "DB_INSTANCE_CONNECTION_NAME",
        "GEMINI_API_KEY",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "JWT_SECRET_KEY",
        "VERTEX_AI_SEARCH_DATASTORE_ID",
    ]

    secrets = _load_secrets_from_gcp(project_id, secret_keys)

    # Secret Manager 값을 환경변수에 설정 (BaseSettings가 읽을 수 있도록)
    for key, value in secrets.items():
        if key not in os.environ:
            os.environ[key] = value

    return Settings(gcp_project_id=project_id)
