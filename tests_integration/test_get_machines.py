import os
import asyncio
import pytest
import aiomysql

from types import SimpleNamespace

from database import DatabaseManager


async def _setup_schema_and_data(conn):
    async with conn.cursor() as cur:
        # Create groups table
        await cur.execute(
            """
            CREATE TABLE IF NOT EXISTS stroj_group (
              id INT PRIMARY KEY AUTO_INCREMENT,
              name VARCHAR(255) NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )
        # Create machines table
        await cur.execute(
            """
            CREATE TABLE IF NOT EXISTS stroje (
              id INT PRIMARY KEY AUTO_INCREMENT,
              name VARCHAR(255) NOT NULL,
              group_id INT,
              CONSTRAINT fk_group FOREIGN KEY (group_id) REFERENCES stroj_group(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )
        # Seed minimal data
        await cur.execute("DELETE FROM stroje")
        await cur.execute("DELETE FROM stroj_group")
        await cur.execute("INSERT INTO stroj_group (name) VALUES ('Soustruhy'), ('Frézky')")
        # Get IDs
        await cur.execute("SELECT id FROM stroj_group WHERE name='Soustruhy'")
        (soustruhy_id,) = await cur.fetchone()
        await cur.execute(
            "INSERT INTO stroje (name, group_id) VALUES (%s, %s), (%s, %s)",
            ("Soustruh SU250", soustruhy_id, "Soustruh SV18", soustruhy_id),
        )


@pytest.mark.asyncio
async def test_get_machines_returns_joined_group_names():
    host = os.getenv("EMISTR_DB_HOST", "127.0.0.1")
    port = int(os.getenv("EMISTR_DB_PORT", "3306"))
    user = os.getenv("EMISTR_DB_USER", "emistr")
    password = os.getenv("EMISTR_DB_PASSWORD", "emistr")
    database = os.getenv("EMISTR_DB_NAME", "emistr")

    # Prepare DB
    conn = await aiomysql.connect(
        host=host, port=port, user=user, password=password, db=database, autocommit=True
    )
    try:
        await _setup_schema_and_data(conn)
    finally:
        conn.close()

    # Prepare DatabaseManager with a minimal config-like object
    cfg = SimpleNamespace(database={
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "database": database,
    })
    dbm = DatabaseManager(cfg)
    await dbm.connect()
    try:
        result = await dbm.get_machines(limit=10)
        assert "machines" in result
        assert result["count"] >= 2
        names = [m["name"] for m in result["machines"]]
        groups = {m["group_name"] for m in result["machines"]}
        assert any("Soustruh" in n for n in names)
        assert "Soustruhy" in groups
    finally:
        await dbm.close()
