import aiomysql
from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import Any
from .config import get_settings

pool: aiomysql.Pool | None = None


async def create_pool():
    global pool
    s = get_settings()
    pool = await aiomysql.create_pool(
        host=s.DB_HOST,
        port=s.DB_PORT,
        user=s.DB_USER,
        password=s.DB_PASSWORD,
        db=s.DB_NAME,
        charset="utf8mb4",
        autocommit=True,
        minsize=2,
        maxsize=10,
        cursorclass=aiomysql.DictCursor,
    )


async def close_pool():
    global pool
    if pool:
        pool.close()
        await pool.wait_closed()


def _serialize(val: Any) -> Any:
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, timedelta):
        return val.total_seconds()
    if isinstance(val, bytes):
        return val.decode("utf-8", errors="replace")
    return val


def _serialize_row(row: dict | None) -> dict | None:
    if row is None:
        return None
    return {k: _serialize(v) for k, v in row.items()}


def _serialize_rows(rows: list[dict]) -> list[dict]:
    return [_serialize_row(r) for r in rows]


async def call_sp(
    name: str,
    params: tuple = (),
    *,
    fetch_one: bool = False,
    fetch_all: bool = True,
    multi: bool = False,
) -> Any:
    """Call a stored procedure and return results.

    - fetch_one: return first row only
    - fetch_all: return all rows (default)
    - multi: return list of result sets (for SPs returning multiple SELECTs)
    """
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                f"CALL {name}({','.join(['%s'] * len(params))})", params
            )

            if multi:
                result_sets = []
                rows = await cur.fetchall()
                result_sets.append(_serialize_rows(rows))
                while await cur.nextset():
                    rows = await cur.fetchall()
                    if rows:
                        result_sets.append(_serialize_rows(rows))
                return result_sets

            if fetch_one:
                row = await cur.fetchone()
                return _serialize_row(row)

            if fetch_all:
                rows = await cur.fetchall()
                return _serialize_rows(rows)

            return None
