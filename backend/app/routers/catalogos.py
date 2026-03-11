from fastapi import APIRouter, Depends, Query
from app.database import call_sp
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/catalogos", tags=["Catalogos"])


@router.get("/paises")
async def listar_paises(user: dict = Depends(get_current_user)):
    return await call_sp("sp_pais_listar")


@router.get("/monedas")
async def listar_monedas(user: dict = Depends(get_current_user)):
    return await call_sp("sp_moneda_listar")


@router.get("/tipo-cambio")
async def obtener_tipo_cambio(
    moneda: str = Query(...),
    fecha: str | None = None,
    user: dict = Depends(get_current_user),
):
    rows = await call_sp("sp_tipo_cambio_obtener", (moneda, fecha))
    return rows[0] if rows else {"tc_compra": None, "tc_venta": None}


@router.post("/tipo-cambio")
async def registrar_tipo_cambio(
    moneda_codigo: str,
    fecha: str,
    tc_compra: float,
    tc_venta: float,
    fuente: str | None = "manual",
    user: dict = Depends(get_current_user),
):
    return await call_sp("sp_tipo_cambio_registrar", (moneda_codigo, fecha, tc_compra, tc_venta, fuente))


@router.get("/partidas-arancelarias")
async def buscar_partida(
    codigo: str = Query(..., min_length=2),
    user: dict = Depends(get_current_user),
):
    return await call_sp("sp_partida_arancelaria_buscar", (codigo,))


@router.get("/categorias")
async def listar_categorias(user: dict = Depends(get_current_user)):
    empresa_id = user["empresa_id"]
    return await call_sp("sp_categoria_listar", (empresa_id,))


@router.post("/categorias")
async def crear_categoria(
    nombre: str,
    descripcion: str | None = None,
    color_ui: str | None = "#3B82F6",
    icono_ui: str | None = "category",
    user: dict = Depends(get_current_user),
):
    empresa_id = user["empresa_id"]
    rows = await call_sp("sp_categoria_crear", (empresa_id, nombre, descripcion, color_ui, icono_ui))
    return rows[0] if rows else {"id": None}


@router.get("/tipos-gasto")
async def listar_tipos_gasto(user: dict = Depends(get_current_user)):
    from app.database import execute_query
    return await execute_query("SELECT * FROM tipos_gasto ORDER BY orden")


@router.get("/estados-importacion")
async def listar_estados(user: dict = Depends(get_current_user)):
    from app.database import execute_query
    return await execute_query("SELECT * FROM estados_importacion ORDER BY orden")
