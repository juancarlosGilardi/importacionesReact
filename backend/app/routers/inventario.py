from fastapi import APIRouter, Depends, HTTPException
from app.database import call_sp, call_sp_multi
from app.auth.dependencies import get_current_user
from app.schemas.inventario import (
    MovimientoIngresoCreate, MovimientoTransferenciaCreate,
    MovimientoSalidaCreate, MovimientoItemCreate,
)

router = APIRouter(prefix="/inventario", tags=["Inventario"])


# ==================== STOCK ====================
@router.get("/stock")
async def stock(
    almacen_id: int | None = None,
    search: str | None = None,
    solo_con_stock: int = 1,
    user: dict = Depends(get_current_user),
):
    return await call_sp("sp_inventario_stock", (user["empresa_id"], almacen_id, search, solo_con_stock))


@router.get("/stock-consolidado")
async def stock_consolidado(
    producto_id: int | None = None,
    user: dict = Depends(get_current_user),
):
    return await call_sp("sp_inventario_stock_consolidado", (user["empresa_id"], producto_id))


@router.get("/kardex")
async def kardex(
    producto_id: int,
    almacen_id: int | None = None,
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    user: dict = Depends(get_current_user),
):
    return await call_sp("sp_kardex_producto", (
        user["empresa_id"], producto_id, almacen_id, fecha_desde, fecha_hasta
    ))


# ==================== MOVIMIENTOS ====================
@router.get("/movimientos")
async def listar_movimientos(
    tipo: str | None = None,
    almacen_id: int | None = None,
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    estado: str | None = None,
    page: int = 1,
    per_page: int = 20,
    user: dict = Depends(get_current_user),
):
    return await call_sp("sp_movimiento_listar", (
        user["empresa_id"], tipo, almacen_id, fecha_desde, fecha_hasta, estado, page, per_page
    ))


@router.get("/movimientos/{id}")
async def obtener_movimiento(id: int, user: dict = Depends(get_current_user)):
    results = await call_sp_multi("sp_movimiento_obtener", (id, user["empresa_id"]))
    if not results or not results[0]:
        raise HTTPException(404, "Movimiento no encontrado")
    return {"cabecera": results[0][0], "items": results[1] if len(results) > 1 else []}


@router.post("/movimientos/ingreso")
async def crear_ingreso(data: MovimientoIngresoCreate, user: dict = Depends(get_current_user)):
    eid = user["empresa_id"]
    uid = user["sub"]
    rows = await call_sp("sp_movimiento_ingreso_crear", (
        eid, data.almacen_id, data.oc_id,
        data.documento_referencia, data.fecha, data.notas, uid
    ))
    return rows[0] if rows else {"id": None}


@router.post("/movimientos/transferencia")
async def crear_transferencia(data: MovimientoTransferenciaCreate, user: dict = Depends(get_current_user)):
    eid = user["empresa_id"]
    uid = user["sub"]
    rows = await call_sp("sp_movimiento_transferencia_crear", (
        eid, data.almacen_origen_id, data.almacen_destino_id,
        data.documento_referencia, data.fecha, data.notas, uid
    ))
    return rows[0] if rows else {"id": None}


@router.post("/movimientos/salida")
async def crear_salida(data: MovimientoSalidaCreate, user: dict = Depends(get_current_user)):
    eid = user["empresa_id"]
    uid = user["sub"]
    rows = await call_sp("sp_movimiento_salida_crear", (
        eid, data.almacen_id,
        data.documento_referencia, data.fecha, data.notas, uid
    ))
    return rows[0] if rows else {"id": None}


@router.post("/movimientos/{id}/items")
async def agregar_item(id: int, data: MovimientoItemCreate, user: dict = Depends(get_current_user)):
    rows = await call_sp("sp_movimiento_item_agregar", (
        id, data.producto_id, data.oc_item_id, data.cantidad,
        data.costo_unitario, data.lote, data.fecha_vencimiento, data.ubicacion
    ))
    return rows[0] if rows else {"id": None}


@router.post("/movimientos/{id}/completar")
async def completar_movimiento(id: int, user: dict = Depends(get_current_user)):
    rows = await call_sp("sp_movimiento_completar", (id, user["empresa_id"], user["sub"]))
    return rows[0] if rows else {"result": "error"}
