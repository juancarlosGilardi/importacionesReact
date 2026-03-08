from fastapi import APIRouter, Depends, Query
from ..database import call_sp
from ..auth import get_current_user

router = APIRouter()


# --- Stock ---
@router.get("/stock")
async def stock(
    almacen_id: int | None = None,
    search: str | None = None,
    solo_con_stock: int = 1,
    user=Depends(get_current_user),
):
    return await call_sp(
        "sp_inventario_stock",
        (user["empresa_id"], almacen_id, search, solo_con_stock),
    )


@router.get("/stock-consolidado")
async def stock_consolidado(producto_id: int | None = None, user=Depends(get_current_user)):
    return await call_sp("sp_inventario_stock_consolidado", (user["empresa_id"], producto_id))


# --- Movimientos ---
@router.get("/movimientos")
async def listar_movimientos(
    tipo: str | None = None,
    almacen_id: int | None = None,
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    estado: str | None = None,
    page: int = 1,
    per_page: int = 20,
    user=Depends(get_current_user),
):
    return await call_sp(
        "sp_movimiento_listar",
        (user["empresa_id"], tipo, almacen_id, fecha_desde, fecha_hasta, estado, page, per_page),
    )


@router.get("/movimientos/{id}")
async def obtener_movimiento(id: int, user=Depends(get_current_user)):
    results = await call_sp("sp_movimiento_obtener", (id, user["empresa_id"]), multi=True)
    return {
        "cabecera": results[0][0] if results and results[0] else None,
        "detalle": results[1] if len(results) > 1 else [],
    }


@router.post("/movimientos/ingreso")
async def crear_ingreso(data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_movimiento_ingreso_crear",
        (user["empresa_id"], data["almacen_id"], data.get("oc_id"), data.get("documento_referencia"), data.get("fecha"), data.get("notas"), user["user_id"]),
        fetch_one=True,
    )


@router.post("/movimientos/transferencia")
async def crear_transferencia(data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_movimiento_transferencia_crear",
        (user["empresa_id"], data["almacen_origen_id"], data["almacen_destino_id"], data.get("documento_referencia"), data.get("fecha"), data.get("notas"), user["user_id"]),
        fetch_one=True,
    )


@router.post("/movimientos/salida")
async def crear_salida(data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_movimiento_salida_crear",
        (user["empresa_id"], data["almacen_id"], data.get("documento_referencia"), data.get("fecha"), data.get("notas"), user["user_id"]),
        fetch_one=True,
    )


@router.post("/movimientos/{id}/items")
async def agregar_item(id: int, data: dict, _=Depends(get_current_user)):
    return await call_sp(
        "sp_movimiento_item_agregar",
        (id, data["producto_id"], data.get("oc_item_id"), data["cantidad"], data["costo_unitario"], data.get("lote"), data.get("fecha_vencimiento"), data.get("ubicacion")),
        fetch_one=True,
    )


@router.post("/movimientos/{id}/completar")
async def completar(id: int, user=Depends(get_current_user)):
    return await call_sp(
        "sp_movimiento_completar",
        (id, user["empresa_id"], user["user_id"]),
        fetch_one=True,
    )


# --- Kardex ---
@router.get("/kardex")
async def kardex(
    producto_id: int = Query(...),
    almacen_id: int | None = None,
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    user=Depends(get_current_user),
):
    return await call_sp(
        "sp_kardex_producto",
        (user["empresa_id"], producto_id, almacen_id, fecha_desde, fecha_hasta),
    )
