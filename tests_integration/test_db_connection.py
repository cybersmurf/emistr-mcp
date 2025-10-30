import os
import asyncio
import pytest

try:
    import aiomysql
except Exception:  # pragma: no cover
    aiomysql = None


@pytest.mark.asyncio
async def test_mariadb_connect_select_one():
    if aiomysql is None:
        pytest.skip("aiomysql not available")

    host = os.getenv("EMISTR_DB_HOST", "127.0.0.1")
    port = int(os.getenv("EMISTR_DB_PORT", "3306"))
    user = os.getenv("EMISTR_DB_USER", "emistr")
    password = os.getenv("EMISTR_DB_PASSWORD", "emistr")
    database = os.getenv("EMISTR_DB_NAME", "emistr")

    conn = await aiomysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        db=database,
        autocommit=True,
    )
    try:
        async with conn.cursor() as cur:
            await cur.execute("SELECT 1")
            row = await cur.fetchone()
            assert row is not None
            assert row[0] == 1
    finally:
        conn.close()
