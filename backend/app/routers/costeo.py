from fastapi import APIRouter, Depends, HTTPException
from app.database import call_sp, call_sp_multi
from app.auth.dependencies import get_current_user
from app.schemas.costeo import GastoCreate, GastoUpdate, ProrrateoCalcular, ProrrateoAplicar

router = APIRouter(prefix="/costeo", tags=["Costeo"])


# ==================== GASTOS ====================
@router.get("/gastos")
async def listar_gastos(
    importacion_id: int | None = None,
    oc_id: int | None = None,
    tipo_gasto: str | None = None,
    estado: str | None = None,
    user: dict = Depends(get_current_user),
):
    return await call_sp("sp_gasto_listar", (user["empresa_id"], importacion_id, oc_id, tipo_gasto, estado))


@router.post("/gastos")
async def crear_gasto(data: GastoCreate, user: dict = Depends(get_current_user)):
    eid = user["empresa_id"]
    uid = user["sub"]
    rows = await call_sp("sp_gasto_crear", (
        eid, data.importacion_id, data.oc_id, data.tipo_gasto_codigo,
        data.descripcion, data.proveedor_ruc, data.proveedor_nombre,
        data.moneda_id, data.monto, data.tipo_cambio,
        data.numero_comprobante, data.fecha_gasto,
        data.comprobante_path, data.notas, uid
    ))
    return rows[0] if rows else {"id": None}


@router.put("/gastos/{id}")
async def actualizar_gasto(id: int, data: GastoUpdate, user: dict = Depends(get_current_user)):
    eid = user["empresa_id"]
    uid = user["sub"]
    rows = await call_sp("sp_gasto_actualizar", (
        id, eid, data.tipo_gasto_codigo, data.descripcion,
        data.proveedor_ruc, data.proveedor_nombre,
        data.moneda_id, data.monto, data.tipo_cambio,
        data.numero_comprobante, data.fecha_gasto,
        data.estado, data.notas, uid
    ))
    return rows[0] if rows else {"affected": 0}


@router.delete("/gastos/{id}")
async def eliminar_gasto(id: int, user: dict = Depends(get_current_user)):
    rows = await call_sp("sp_gasto_eliminar", (id, user["empresa_id"]))
    return rows[0] if rows else {"result": "error"}


@router.get("/gastos/resumen/{importacion_id}")
async def resumen_gastos(importacion_id: int, user: dict = Depends(get_current_user)):
    return await call_sp("sp_gasto_resumen_por_tipo", (user["empresa_id"], importacion_id))


# ==================== PRORRATEO ====================
@router.post("/prorrateo/calcular")
async def calcular_prorrateo(data: ProrrateoCalcular, user: dict = Depends(get_current_user)):
    eid = user["empresa_id"]
    uid = user["sub"]
    rows = await call_sp("sp_prorrateo_calcular", (
        eid, data.importacion_id, data.oc_id, data.metodo, uid
    ))
    return rows[0] if rows else {}


@router.post("/prorrateo/aplicar")
async def aplicar_prorrateo(data: ProrrateoAplicar, user: dict = Depends(get_current_user)):
    eid = user["empresa_id"]
    uid = user["sub"]
    rows = await call_sp("sp_prorrateo_aplicar", (data.prorrateo_id, eid, uid))
    return rows[0] if rows else {"result": "error"}


@router.get("/prorrateo/{id}")
async def obtener_prorrateo(id: int, user: dict = Depends(get_current_user)):
    results = await call_sp_multi("sp_prorrateo_obtener", (id, user["empresa_id"]))
    if not results or not results[0]:
        raise HTTPException(404, "Prorrateo no encontrado")
    return {"cabecera": results[0][0], "detalle": results[1] if len(results) > 1 else []}
