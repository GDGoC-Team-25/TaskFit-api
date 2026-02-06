import asyncio
from google.cloud.sql.connector import create_async_connector

async def test():
    from src.core.config import get_settings

    settings = get_settings()
    print(f"Project: {settings.gcp_project_id}")
    print(f"DB: {settings.db_name} / Schema: {settings.db_schema}")
    print(f"User: {settings.db_user}")
    print(f"Instance: {settings.db_instance_connection_name}")
    print("--- Settings loaded from Secret Manager ---")

    connector = await create_async_connector()
    try:
        conn = await connector.connect_async(
            settings.db_instance_connection_name,
            "asyncpg",
            user=settings.db_user,
            password=settings.db_password,
            db=settings.db_name,
        )

        result = await conn.fetch("SELECT current_database(), version()")
        row = result[0]
        print(f"Connected DB: {row[0]}")
        print(f"PG Version: {row[1][:60]}...")

        await conn.execute(f"SET search_path TO {settings.db_schema}, public")
        schema_check = await conn.fetch("SELECT current_schema()")
        print(f"Current Schema: {schema_check[0][0]}")

        schemas = await conn.fetch(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'taskfit'"
        )
        print(f"taskfit schema exists: {len(schemas) > 0}")

        await conn.close()
        print("--- DB Connection OK ---")
    finally:
        await connector.close_async()

asyncio.run(test())
