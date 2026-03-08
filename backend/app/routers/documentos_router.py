from fastapi import APIRouter, Depends, Query
from ..database import call_sp
from ..auth import get_current_user

router = APIRouter()


# --- DUA ---
@router.get("/dua")
async def listar_dua(
    importacion_id: int | None = None,
    estado: str | None = None,
    page: int = 1,
    per_page: int = 20,
    user=Depends(get_current_user),
):
    return await call_sp(
        "sp_dua_listar",
        (user["empresa_id"], importacion_id, estado, page, per_page),
    )


@router.get("/dua/{id}")
async def obtener_dua(id: int, user=Depends(get_current_user)):
    results = await call_sp("sp_dua_obtener", (id, user["empresa_id"]), multi=True)
    return {
        "cabecera": results[0][0] if results and results[0] else None,
        "items": results[1] if len(results) > 1 else [],
    }


@router.post("/dua")
async def crear_dua(data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_dua_crear",
        (
            user["empresa_id"], data["importacion_id"], data["numero_dua"],
            data.get("fecha_registro"), data.get("fecha_levante"),
            data.get("agencia_aduanas"), data.get("ruc_agente"), data.get("numero_operacion"),
            data.get("valor_fob_usd"), data.get("flete_usd"), data.get("seguro_usd"),
            data.get("tasa_ad_valorem"), data.get("tasa_igv", 18),
            data.get("tasa_ipm", 0), data.get("monto_isc", 0),
            data.get("monto_antidumping", 0), data.get("tasa_percepcion", 3.5),
            data.get("gastos_despacho", 0), data.get("honorarios_agente", 0),
            data.get("almacenaje", 0), data.get("otros_gastos", 0),
            data.get("tipo_cambio"), data.get("archivo_pdf"),
            data.get("notas"), user["user_id"],
        ),
        fetch_one=True,
    )


@router.put("/dua/{id}")
async def actualizar_dua(id: int, data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_dua_actualizar",
        (
            id, user["empresa_id"], data.get("fecha_levante"),
            data.get("valor_fob_usd"), data.get("flete_usd"), data.get("seguro_usd"),
            data.get("tasa_ad_valorem"), data.get("tasa_igv"),
            data.get("tasa_ipm"), data.get("monto_isc"),
            data.get("monto_antidumping"), data.get("tasa_percepcion"),
            data.get("gastos_despacho"), data.get("honorarios_agente"),
            data.get("almacenaje"), data.get("otros_gastos"),
            data.get("estado"), data.get("notas"), user["user_id"],
        ),
        fetch_one=True,
    )


@router.post("/dua/{dua_id}/items")
async def agregar_dua_item(dua_id: int, data: dict, _=Depends(get_current_user)):
    return await call_sp(
        "sp_dua_item_agregar",
        (
            dua_id, data.get("numero_serie"), data.get("producto_id"),
            data.get("codigo_hs"), data.get("descripcion"),
            data.get("cantidad"), data.get("unidad_medida"),
            data.get("valor_fob_usd"), data.get("peso_kg"),
            data.get("tasa_ad_valorem"),
        ),
        fetch_one=True,
    )


# --- Transporte ---
@router.get("/transporte")
async def listar_transporte(importacion_id: int | None = None, user=Depends(get_current_user)):
    return await call_sp("sp_doc_transporte_listar", (user["empresa_id"], importacion_id))


@router.post("/transporte")
async def crear_transporte(data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_doc_transporte_crear",
        (
            user["empresa_id"], data["importacion_id"], data.get("tipo_documento"),
            data.get("numero_documento"), data.get("transportista"),
            data.get("nombre_nave"), data.get("numero_viaje"),
            data.get("fecha_etd"), data.get("fecha_eta"),
            data.get("total_bultos"), data.get("peso_bruto_kg"), data.get("volumen_m3"),
            data.get("archivo_path"), data.get("tracking_url"),
            data.get("notas"), user["user_id"],
        ),
        fetch_one=True,
    )


@router.put("/transporte/{id}")
async def actualizar_transporte(id: int, data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_doc_transporte_actualizar",
        (
            id, user["empresa_id"], data.get("numero_documento"), data.get("transportista"),
            data.get("nombre_nave"), data.get("numero_viaje"),
            data.get("fecha_etd"), data.get("fecha_eta"), data.get("fecha_arribo_real"),
            data.get("total_bultos"), data.get("peso_bruto_kg"), data.get("volumen_m3"),
            data.get("tracking_url"), data.get("notas"), user["user_id"],
        ),
        fetch_one=True,
    )


# --- Facturas ---
@router.get("/facturas")
async def listar_facturas(
    oc_id: int | None = None,
    proveedor_id: int | None = None,
    estado: str | None = None,
    page: int = 1,
    per_page: int = 20,
    user=Depends(get_current_user),
):
    return await call_sp(
        "sp_factura_listar",
        (user["empresa_id"], oc_id, proveedor_id, estado, page, per_page),
    )


@router.get("/facturas/{id}")
async def obtener_factura(id: int, user=Depends(get_current_user)):
    results = await call_sp("sp_factura_obtener", (id, user["empresa_id"]), multi=True)
    return {
        "cabecera": results[0][0] if results and results[0] else None,
        "items": results[1] if len(results) > 1 else [],
    }


@router.post("/facturas")
async def crear_factura(data: dict, user=Depends(get_current_user)):
    return await call_sp(
        "sp_factura_crear",
        (
            user["empresa_id"], data["numero_factura"], data.get("oc_id"),
            data["proveedor_id"], data.get("fecha_factura"),
            data.get("moneda_id"), data.get("tipo_cambio"),
            data.get("subtotal"), data.get("impuesto"), data.get("total"),
            data.get("xml_file_path"), data.get("xml_hash"),
            data.get("archivo_pdf"), data.get("notas"), user["user_id"],
        ),
        fetch_one=True,
    )


@router.post("/facturas/{factura_id}/items")
async def agregar_factura_item(factura_id: int, data: dict, _=Depends(get_current_user)):
    return await call_sp(
        "sp_factura_item_agregar",
        (factura_id, data["producto_id"], data["cantidad"], data["precio_unitario"], data.get("precio_total")),
        fetch_one=True,
    )
