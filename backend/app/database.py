import aiomysql
from app.config import settings

_pool: aiomysql.Pool | None = None


async def get_pool() -> aiomysql.Pool:
    global _pool
    if _pool is None:
        _pool = await aiomysql.create_pool(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            db=settings.DB_NAME,
            charset="utf8mb4",
            autocommit=True,
            minsize=2,
            maxsize=10,
            cursorclass=aiomysql.DictCursor,
        )
    return _pool


async def close_pool():
    global _pool
    if _pool:
        _pool.close()
        await _pool.wait_closed()
        _pool = None


async def call_sp(sp_name: str, args: tuple = ()) -> list[dict]:
    """Call a stored procedure and return all result rows."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.callproc(sp_name, args)
            rows = await cur.fetchall()
            return rows if rows else []


async def call_sp_multi(sp_name: str, args: tuple = ()) -> list[list[dict]]:
    """Call a stored procedure that returns multiple result sets."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.callproc(sp_name, args)
            results = []
            rows = await cur.fetchall()
            results.append(rows if rows else [])
            while await cur.nextset():
                rows = await cur.fetchall()
                results.append(rows if rows else [])
            return results


async def execute_query(query: str, args: tuple = ()) -> list[dict]:
    """Execute a raw query and return results."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(query, args)
            rows = await cur.fetchall()
            return rows if rows else []
