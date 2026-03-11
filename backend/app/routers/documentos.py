from fastapi import APIRouter, Depends, HTTPException
from app.database import call_sp, call_sp_multi
from app.auth.dependencies import get_current_user
from app.schemas.documentos import (
    DUACreate, DUAUpdate, DUAItemCreate,
    DocTransporteCreate, DocTransporteUpdate,
    FacturaCreate, FacturaItemCreate,
)

router = APIRouter(prefix="/documentos", tags=["Documentos"])


# ==================== DUA ====================
@router.get("/dua")
async def listar_dua(
    importacion_id: int | None = None,
    estado: str | None = None,
    page: int = 1,
    per_page: int = 20,
    user: dict = Depends(get_current_user),
):
    return await call_sp("sp_dua_listar", (user["empresa_id"], importacion_id, estado, page, per_page))


@router.get("/dua/{id}")
async def obtener_dua(id: int, user: dict = Depends(get_current_user)):
    results = await call_sp_multi("sp_dua_obtener", (id, user["empresa_id"]))
    if not results or not results[0]:
        raise HTTPException(404, "DUA no encontrada")
    return {"cabecera": results[0][0], "items": results[1] if len(results) > 1 else []}


@router.post("/dua")
async def crear_dua(data: DUACreate, user: dict = Depends(get_current_user)):
    eid = user["empresa_id"]
    uid = user["sub"]
    rows = await call_sp("sp_dua_crear", (
        eid, data.importacion_id, data.numero_dua, data.fecha_registro, data.fecha_levante,
        data.agencia_aduanas, data.ruc_agente, data.numero_operacion,
        data.valor_fob_usd, data.flete_usd, data.seguro_usd,
        data.tasa_ad_valorem, data.tasa_igv, data.tasa_ipm,
        data.monto_isc, data.monto_antidumping, data.tasa_percepcion,
        data.gastos_despacho, data.honorarios_agente, data.almacenaje, data.otros_gastos,
        data.tipo_cambio, data.archivo_pdf, data.notas, uid
    ))
    return rows[0] if rows else {"id": None}


@router.put("/dua/{id}")
async def actualizar_dua(id: int, data: DUAUpdate, user: dict = Depends(get_current_user)):
    eid = user["empresa_id"]
    uid = user["sub"]
    rows = await call_sp("sp_dua_actualizar", (
        id, eid, data.fecha_levante,
        data.valor_fob_usd, data.flete_usd, data.seguro_usd,
        data.tasa_ad_valorem, data.tasa_igv, data.tasa_ipm,
        data.monto_isc, data.monto_antidumping, data.tasa_percepcion,
        data.gastos_despacho, data.honorarios_agente, data.almacenaje, data.otros_gastos,
        data.estado, data.notas, uid
    ))
    return rows[0] if rows else {"affected": 0}


@router.post("/dua/{dua_id}/items")
async def agregar_dua_item(dua_id: int, data: DUAItemCreate, user: dict = Depends(get_current_user)):
    rows = await call_sp("sp_dua_item_agregar", (
        dua_id, data.numero_serie, data.producto_id, data.codigo_hs,
        data.descripcion, data.cantidad, data.unidad_medida,
        data.valor_fob_usd, data.peso_kg, data.tasa_ad_valorem
    ))
    return rows[0] if rows else {"id": None}


# ==================== DOCUMENTOS DE TRANSPORTE ====================
@router.get("/transporte")
async def listar_doc_transporte(
    importacion_id: int | None = None,
    user: dict = Depends(get_current_user),
):
    return await call_sp("sp_doc_transporte_listar", (user["empresa_id"], importacion_id))


@router.post("/transporte")
async def crear_doc_transporte(data: DocTransporteCreate, user: dict = Depends(get_current_user)):
    eid = user["empresa_id"]
    uid = user["sub"]
    rows = await call_sp("sp_doc_transporte_crear", (
        eid, data.importacion_id, data.tipo_documento, data.numero_documento,
        data.transportista, data.nombre_nave, data.numero_viaje,
        data.fecha_etd, data.fecha_eta, data.total_bultos,
        data.peso_bruto_kg, data.volumen_m3, data.archivo_path,
        data.tracking_url, data.notas, uid
    ))
    return rows[0] if rows else {"id": None}


@router.put("/transporte/{id}")
async def actualizar_doc_transporte(id: int, data: DocTransporteUpdate, user: dict = Depends(get_current_user)):
    eid = user["empresa_id"]
    uid = user["sub"]
    rows = await call_sp("sp_doc_transporte_actualizar", (
        id, eid, data.numero_documento, data.transportista,
        data.nombre_nave, data.numero_viaje,
        data.fecha_etd, data.fecha_eta, data.fecha_arribo_real,
        data.total_bultos, data.peso_bruto_kg, data.volumen_m3,
        data.tracking_url, data.notas, uid
    ))
    return rows[0] if rows else {"affected": 0}


# ==================== FACTURAS DE PROVEEDOR ====================
@router.get("/facturas")
async def listar_facturas(
    oc_id: int | None = None,
    proveedor_id: int | None = None,
    estado: str | None = None,
    page: int = 1,
    per_page: int = 20,
    user: dict = Depends(get_current_user),
):
    return await call_sp("sp_factura_listar", (user["empresa_id"], oc_id, proveedor_id, estado, page, per_page))


@router.get("/facturas/{id}")
async def obtener_factura(id: int, user: dict = Depends(get_current_user)):
    results = await call_sp_multi("sp_factura_obtener", (id, user["empresa_id"]))
    if not results or not results[0]:
        raise HTTPException(404, "Factura no encontrada")
    return {"cabecera": results[0][0], "items": results[1] if len(results) > 1 else []}


@router.post("/facturas")
async def crear_factura(data: FacturaCreate, user: dict = Depends(get_current_user)):
    eid = user["empresa_id"]
    uid = user["sub"]
    rows = await call_sp("sp_factura_crear", (
        eid, data.numero_factura, data.oc_id, data.proveedor_id,
        data.fecha_factura, data.moneda_id, data.tipo_cambio,
        data.subtotal, data.impuesto, data.total,
        data.xml_file_path, data.xml_hash, data.archivo_pdf, data.notas, uid
    ))
    return rows[0] if rows else {"id": None}


@router.post("/facturas/{factura_id}/items")
async def agregar_factura_item(factura_id: int, data: FacturaItemCreate, user: dict = Depends(get_current_user)):
    rows = await call_sp("sp_factura_item_agregar", (
        factura_id, data.producto_id, data.cantidad,
        data.precio_unitario, data.precio_total
    ))
    return rows[0] if rows else {"id": None}
