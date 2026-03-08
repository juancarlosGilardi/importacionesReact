from fastapi import APIRouter, Depends, Query
from ..database import call_sp
from ..auth import get_current_user

router = APIRouter()


@router.get("/paises")
async def listar_paises(_=Depends(get_current_user)):
    return await call_sp("sp_pais_listar")


@router.get("/monedas")
async def listar_monedas(_=Depends(get_current_user)):
    return await call_sp("sp_moneda_listar")


@router.get("/tipo-cambio")
async def obtener_tipo_cambio(
    moneda: str = Query("USD"),
    fecha: str | None = None,
    _=Depends(get_current_user),
):
    return await call_sp("sp_tipo_cambio_obtener", (moneda, fecha), fetch_one=True)


@router.post("/tipo-cambio")
async def registrar_tipo_cambio(
    data: dict,
    user=Depends(get_current_user),
):
    return await call_sp(
        "sp_tipo_cambio_registrar",
        (data["moneda"], data["fecha"], data["tc_compra"], data["tc_venta"], data.get("fuente", "manual")),
        fetch_one=True,
    )


@router.get("/partidas")
async def buscar_partidas(codigo: str = Query(""), _=Depends(get_current_user)):
    return await call_sp("sp_partida_arancelaria_buscar", (codigo,))


@router.get("/estados")
async def listar_estados(_=Depends(get_current_user)):
    from ..database import pool
    import aiomysql

    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM estados_importacion ORDER BY orden")
            return await cur.fetchall()


@router.get("/tipos-gasto")
async def listar_tipos_gasto(_=Depends(get_current_user)):
    from ..database import pool
    import aiomysql

    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM tipos_gasto ORDER BY orden")
            return await cur.fetchall()


@router.get("/tlc")
async def listar_tlc(_=Depends(get_current_user)):
    from ..database import pool
    import aiomysql

    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT t.*, p.nombre AS pais, p.codigo AS pais_codigo "
                "FROM tlc_acuerdos t JOIN paises p ON t.pais_id = p.id "
                "WHERE t.status = 'vigente' ORDER BY p.nombre"
            )
            return await cur.fetchall()
