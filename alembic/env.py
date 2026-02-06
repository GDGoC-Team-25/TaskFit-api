import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from src.core.database import _get_connection
from src.models.database import Base

# Alembic Config 객체
config = context.config

# 로깅 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# autogenerate용 메타데이터
target_metadata = Base.metadata


def do_run_migrations(connection):
    """동기 컨텍스트에서 마이그레이션 실행."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table_schema="taskfit",
        include_schemas=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Cloud SQL Connector를 사용한 async 마이그레이션."""
    engine = create_async_engine(
        "postgresql+asyncpg://",
        async_creator=_get_connection,
    )
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()

    # Connector 정리
    from src.core.database import close_db
    await close_db()


def run_migrations_online() -> None:
    """온라인 모드 마이그레이션 실행."""
    asyncio.run(run_async_migrations())


run_migrations_online()
