from fastapi import APIRouter, Depends, Query, HTTPException
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
    items = await call_sp(
        "sp_movimiento_listar",
        (user["empresa_id"], tipo, almacen_id, fecha_desde, fecha_hasta, estado, page, per_page),
    )
    count_result = await call_sp(
        "sp_movimiento_contar",
        (user["empresa_id"], tipo, almacen_id, fecha_desde, fecha_hasta, estado),
        fetch_one=True,
    )
    total = count_result["total"] if count_result else 0
    import math
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if per_page > 0 else 0,
    }


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


@router.delete("/movimientos/{id}/items/{item_id}")
async def eliminar_item(id: int, item_id: int, user=Depends(get_current_user)):
    try:
        return await call_sp(
            "sp_movimiento_item_eliminar",
            (id, item_id, user["empresa_id"]),
            fetch_one=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/movimientos/{id}/completar")
async def completar(id: int, user=Depends(get_current_user)):
    return await call_sp(
        "sp_movimiento_completar",
        (id, user["empresa_id"], user["user_id"]),
        fetch_one=True,
    )


# --- Stock Avanzado ---
@router.get("/stock/resumen")
async def stock_resumen(user=Depends(get_current_user)):
    result = await call_sp("sp_stock_resumen", (user["empresa_id"],), fetch_one=True)
    return result


@router.get("/stock/por-almacen")
async def stock_por_almacen(user=Depends(get_current_user)):
    return await call_sp("sp_stock_por_almacen", (user["empresa_id"],))


# --- Alertas de Stock ---
@router.get("/alertas")
async def alertas_stock(
    almacen_id: int | None = None,
    nivel: str | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 50,
    user=Depends(get_current_user),
):
    return await call_sp(
        "sp_alertas_stock",
        (user["empresa_id"], almacen_id, nivel, search, page, per_page),
    )


@router.get("/alertas/resumen")
async def alertas_resumen(
    almacen_id: int | None = None,
    user=Depends(get_current_user),
):
    result = await call_sp(
        "sp_alertas_stock_resumen",
        (user["empresa_id"], almacen_id),
        fetch_one=True,
    )
    return result


# --- Inventario Valorizado ---
@router.get("/valorizado")
async def inventario_valorizado(
    almacen_id: int | None = None,
    categoria_id: int | None = None,
    moneda: str = "PEN",
    tipo_cambio: float | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 50,
    user=Depends(get_current_user),
):
    import math
    items = await call_sp(
        "sp_inventario_valorizado",
        (user["empresa_id"], almacen_id, categoria_id, moneda, tipo_cambio, search, page, per_page),
    )
    count_result = await call_sp(
        "sp_inventario_valorizado_contar",
        (user["empresa_id"], almacen_id, categoria_id, search),
        fetch_one=True,
    )
    total = count_result["total"] if count_result else 0
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if per_page > 0 else 0,
    }


@router.get("/valorizado/por-familia")
async def valorizado_por_familia(
    almacen_id: int | None = None,
    moneda: str = "PEN",
    tipo_cambio: float | None = None,
    user=Depends(get_current_user),
):
    return await call_sp(
        "sp_inventario_valorizado_por_familia",
        (user["empresa_id"], almacen_id, moneda, tipo_cambio),
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
