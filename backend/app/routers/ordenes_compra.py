from fastapi import APIRouter, Depends, HTTPException
from app.database import call_sp, call_sp_multi
from app.auth.dependencies import get_current_user
from app.schemas.operaciones import OCCreate, OCUpdate, OCCambiarEstado, OCItemCreate, OCItemUpdate

router = APIRouter(prefix="/ordenes-compra", tags=["Ordenes de Compra"])


@router.get("/")
async def listar(
    search: str | None = None,
    estado: str | None = None,
    proveedor_id: int | None = None,
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    page: int = 1,
    per_page: int = 20,
    user: dict = Depends(get_current_user),
):
    eid = user["empresa_id"]
    data = await call_sp("sp_oc_listar", (eid, search, estado, proveedor_id, fecha_desde, fecha_hasta, page, per_page))
    count = await call_sp("sp_oc_contar", (eid, search, estado, proveedor_id, fecha_desde, fecha_hasta))
    total = count[0]["total"] if count else 0
    return {"data": data, "total": total, "page": page, "per_page": per_page}


@router.get("/{id}")
async def obtener(id: int, user: dict = Depends(get_current_user)):
    results = await call_sp_multi("sp_oc_obtener", (id, user["empresa_id"]))
    if not results or not results[0]:
        raise HTTPException(404, "Orden de compra no encontrada")
    return {"cabecera": results[0][0], "items": results[1] if len(results) > 1 else []}


@router.post("/")
async def crear(data: OCCreate, user: dict = Depends(get_current_user)):
    eid = user["empresa_id"]
    uid = user["sub"]
    rows = await call_sp("sp_oc_crear", (
        eid, data.numero_oc, data.proveedor_id, data.fecha_orden,
        data.fecha_llegada_est, data.incoterm, data.moneda_id, data.tipo_cambio,
        data.puerto_embarque, data.puerto_destino, data.agente_aduanero,
        data.agente_carga, data.notas, uid
    ))
    return rows[0] if rows else {"id": None}


@router.put("/{id}")
async def actualizar(id: int, data: OCUpdate, user: dict = Depends(get_current_user)):
    eid = user["empresa_id"]
    uid = user["sub"]
    rows = await call_sp("sp_oc_actualizar", (
        id, eid, data.numero_oc, data.proveedor_id, data.fecha_orden,
        data.fecha_llegada_est, data.incoterm, data.moneda_id, data.tipo_cambio,
        data.puerto_embarque, data.puerto_destino, data.agente_aduanero,
        data.agente_carga, data.notas, uid
    ))
    return rows[0] if rows else {"affected": 0}


@router.patch("/{id}/estado")
async def cambiar_estado(id: int, data: OCCambiarEstado, user: dict = Depends(get_current_user)):
    rows = await call_sp("sp_oc_cambiar_estado", (id, user["empresa_id"], data.estado, user["sub"]))
    return rows[0] if rows else {"affected": 0}


@router.delete("/{id}")
async def eliminar(id: int, user: dict = Depends(get_current_user)):
    rows = await call_sp("sp_oc_eliminar", (id, user["empresa_id"]))
    return rows[0] if rows else {"result": "error"}


# --- ITEMS ---
@router.post("/{oc_id}/items")
async def agregar_item(oc_id: int, data: OCItemCreate, user: dict = Depends(get_current_user)):
    rows = await call_sp("sp_oc_item_agregar", (
        oc_id, data.producto_id, data.cantidad, data.precio_unitario,
        data.unidad_medida, data.peso_kg, data.volumen_m3, user["sub"]
    ))
    return rows[0] if rows else {"id": None}


@router.put("/{oc_id}/items/{item_id}")
async def actualizar_item(oc_id: int, item_id: int, data: OCItemUpdate, user: dict = Depends(get_current_user)):
    rows = await call_sp("sp_oc_item_actualizar", (
        item_id, data.cantidad, data.precio_unitario,
        data.peso_kg, data.volumen_m3, user["sub"]
    ))
    return rows[0] if rows else {"affected": 0}


@router.delete("/{oc_id}/items/{item_id}")
async def eliminar_item(oc_id: int, item_id: int, user: dict = Depends(get_current_user)):
    rows = await call_sp("sp_oc_item_eliminar", (item_id,))
    return rows[0] if rows else {"affected": 0}


# --- FICHA DE COSTEO ---
@router.get("/{id}/ficha-costeo")
async def ficha_costeo(id: int, user: dict = Depends(get_current_user)):
    results = await call_sp_multi("sp_ficha_costeo_oc", (id, user["empresa_id"]))
    if not results or not results[0]:
        raise HTTPException(404, "OC no encontrada")
    return {
        "cabecera": results[0][0],
        "items": results[1] if len(results) > 1 else [],
        "gastos": results[2] if len(results) > 2 else [],
    }
