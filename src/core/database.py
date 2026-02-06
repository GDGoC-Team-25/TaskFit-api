from collections.abc import AsyncGenerator

from google.cloud.sql.connector import Connector, create_async_connector
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import get_settings

# 지연 초기화: 이벤트 루프 내에서 생성해야 함
_connector: Connector | None = None
_engine = None
_async_session = None


async def _get_connector() -> Connector:
    global _connector
    if _connector is None:
        _connector = await create_async_connector()
    return _connector


async def _get_connection():
    """Cloud SQL Connector로 asyncpg 연결을 생성한다."""
    settings = get_settings()
    connector = await _get_connector()
    conn = await connector.connect_async(
        settings.db_instance_connection_name,
        "asyncpg",
        user=settings.db_user,
        password=settings.db_password,
        db=settings.db_name,
    )
    # taskfit 스키마를 기본 search_path로 설정
    await conn.execute(f"SET search_path TO {settings.db_schema}, public")
    return conn


def _get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            "postgresql+asyncpg://",
            async_creator=_get_connection,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
    return _engine


def _get_session_maker():
    global _async_session
    if _async_session is None:
        _async_session = async_sessionmaker(
            _get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _async_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Depends()용 DB 세션 제공자."""
    session_maker = _get_session_maker()
    async with session_maker() as session:
        yield session


async def close_db():
    """앱 종료 시 커넥터/엔진 정리."""
    global _connector, _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
    if _connector is not None:
        await _connector.close_async()
        _connector = None
